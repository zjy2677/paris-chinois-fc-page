import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from threading import Barrier
from uuid import uuid4

import pytest
from app import media
from app.media import image_type
from app.models import AlbumPhoto, GuestbookMessage, MediaAsset, PhotoAlbum, User
from fastapi import HTTPException
from PIL import Image
from sqlalchemy import create_engine, delete, func, select
from sqlalchemy.orm import Session
from starlette.requests import Request


@pytest.mark.parametrize(
    "format,content_type", [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")]
)
def test_decodes_supported_images(format, content_type):
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format=format)
    assert image_type(content_type, buffer.getvalue()) == content_type


@pytest.mark.parametrize(
    "content_type,data",
    [
        ("image/png", b"\x89PNG\r\n\x1a\ngarbage"),
        ("image/jpeg", b"\xff\xd8\xffgarbage"),
        ("image/webp", b"RIFF0000WEBPgarbage"),
        ("image/svg+xml", b"<svg/>"),
    ],
)
def test_rejects_malformed_images(content_type, data):
    with pytest.raises(HTTPException) as error:
        image_type(content_type, data)
    assert error.value.status_code == 415


def test_rejects_declared_type_mismatch_and_truncated_pixels():
    buffer = BytesIO()
    Image.new("RGB", (32, 32), "red").save(buffer, format="JPEG")
    for content_type, data in [
        ("image/png", buffer.getvalue()),
        ("image/jpeg", buffer.getvalue()[:-20]),
    ]:
        with pytest.raises(HTTPException) as error:
            image_type(content_type, data)
        assert error.value.status_code == 415


def test_rejects_decompression_bomb_warning(monkeypatch):
    buffer = BytesIO()
    Image.new("RGB", (4, 4)).save(buffer, format="PNG")
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 10)
    with pytest.raises(HTTPException) as error:
        image_type("image/png", buffer.getvalue())
    assert error.value.status_code == 415


@pytest.mark.parametrize("kind", ["album", "guestbook"])
def test_concurrent_uploads_enforce_parent_limit(monkeypatch, kind):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    parent_id, user_id = uuid4(), uuid4()
    token = "test-visitor"
    with Session(engine) as db:
        db.add(
            User(
                id=user_id,
                normalized_email=f"{user_id}@example.com",
                password_hash="unused",
                role="admin",
            )
        )
        db.flush()
        if kind == "album":
            db.add(PhotoAlbum(id=parent_id, title="Concurrency test", created_by=user_id))
        else:
            db.add(
                GuestbookMessage(
                    id=parent_id,
                    nickname="Test",
                    body="Match photo",
                    visitor_hash=media.token_hash(token),
                    status="pending",
                )
            )
        db.commit()
    # With one slot remaining, exactly one of the concurrent requests may insert.
    monkeypatch.setattr(media, "MAX_PHOTOS_PER_CONTENT", 1)
    new_asset = media.new_asset

    def delayed_asset(*args, **kwargs):
        # Widen the count/insert race so the parent lock is exercised reliably.
        time.sleep(0.1)
        return new_asset(*args, **kwargs)

    monkeypatch.setattr(media, "new_asset", delayed_asset)
    barrier = Barrier(2)
    buffer = BytesIO()
    Image.new("RGB", (2, 2)).save(buffer, format="PNG")

    def upload():
        async def receive():
            return {"type": "http.request", "body": buffer.getvalue(), "more_body": False}

        request = Request(
            {
                "type": "http",
                "headers": [
                    (b"content-type", b"image/png"),
                    (b"cookie", f"{media.COOKIE_NAME}={token}".encode()),
                ],
            },
            receive,
        )
        with Session(engine) as db:
            user = db.get(User, user_id)
            barrier.wait(timeout=5)
            try:
                if kind == "album":
                    asyncio.run(
                        media.upload_album_photo(
                            parent_id, request, db, user, caption=None, alt=None
                        )
                    )
                else:
                    asyncio.run(
                        media.upload_guestbook_photo(parent_id, request, db, caption=None, alt=None)
                    )
                return 201
            except HTTPException as error:
                return error.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(upload) for _ in range(2)]
            assert sorted(future.result(timeout=10) for future in futures) == [201, 409]
        with Session(engine) as db:
            if kind == "album":
                count = db.scalar(
                    select(func.count())
                    .select_from(AlbumPhoto)
                    .where(AlbumPhoto.album_id == parent_id)
                )
            else:
                count = db.scalar(
                    select(func.count())
                    .select_from(MediaAsset)
                    .where(MediaAsset.guestbook_message_id == parent_id)
                )
            assert count == 1
    finally:
        with Session(engine) as db:
            if kind == "album":
                asset_ids = list(
                    db.scalars(select(AlbumPhoto.media_id).where(AlbumPhoto.album_id == parent_id))
                )
                db.execute(delete(PhotoAlbum).where(PhotoAlbum.id == parent_id))
                db.execute(delete(MediaAsset).where(MediaAsset.id.in_(asset_ids)))
            else:
                db.execute(delete(GuestbookMessage).where(GuestbookMessage.id == parent_id))
            db.execute(delete(User).where(User.id == user_id))
            db.commit()
        engine.dispose()
