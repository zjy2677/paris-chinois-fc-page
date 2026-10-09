"""Exercise database/R2 failure boundaries without contacting an actual bucket."""

import asyncio
import os
import threading
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from app import media, photo_storage, profile
from app.models import (
    Base,
    MediaAsset,
    PhotoAlbum,
    Player,
    PlayerPhoto,
    StorageDeletion,
    User,
    UserAvatar,
)
from app.players import router as players
from app.players import service
from app.players.schemas import PlayerCreate, PlayerUpdate
from app.storage import StorageUnavailable
from fastapi import HTTPException
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from starlette.requests import Request


class FakeStorage:
    enabled = True
    configured = True
    fail_delete = False
    fail_put = False

    def __init__(self):
        self.objects = {}
        self.deleted = []

    def put(self, key, data, content_type):
        self.objects[key] = data
        if self.fail_put:
            raise StorageUnavailable("PUT timed out after persisting bytes")

    def delete(self, key):
        if self.fail_delete:
            raise StorageUnavailable("R2 temporarily unavailable")
        self.deleted.append(key)
        self.objects.pop(key, None)


@pytest.fixture
def storage(monkeypatch):
    store = FakeStorage()
    monkeypatch.setattr(photo_storage, "get_storage", lambda: store)
    return store


@pytest.fixture
def db(tmp_path):
    url = os.environ.get("TEST_DATABASE_URL")
    engine = create_engine(url or f"sqlite:///{tmp_path}/photos.db")
    if url:
        assert engine.url.database.endswith("_test")
    else:
        Base.metadata.create_all(engine)
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(connection, join_transaction_mode="create_savepoint") as session:
            yield session
        transaction.rollback()
    engine.dispose()


def fail_next_commit(db):
    def fail(session):
        raise RuntimeError("simulated commit failure")

    event.listen(db, "before_commit", fail, once=True)


@pytest.mark.parametrize("status_code", [403, 404, 409, 503])
def test_photo_transaction_http_failure_diagnostics(status_code, monkeypatch, caplog):
    db = Mock(spec=Session)
    queue_deletion = Mock()
    retry_deletions = Mock()
    monkeypatch.setattr(photo_storage, "queue_deletion", queue_deletion)
    monkeypatch.setattr(photo_storage, "retry_deletions", retry_deletions)
    error = HTTPException(status_code, "private response detail")
    cause = StorageUnavailable("private storage detail")

    with pytest.raises(HTTPException) as raised:
        with photo_storage.photo_transaction(db) as write:
            write.uploaded.append("new/photo")
            raise error from cause

    assert raised.value is error
    assert raised.value.__cause__ is cause
    db.rollback.assert_called_once_with()
    queue_deletion.assert_called_once_with(db, "new/photo")
    db.commit.assert_called_once_with()
    retry_deletions.assert_called_once_with(db, ["new/photo"])
    diagnostics = [
        record.getMessage()
        for record in caplog.records
        if record.name == "app.photo_storage"
        and record.getMessage().startswith("Photo transaction failed")
    ]
    assert diagnostics == (
        ["Photo transaction failed exception_type=HTTPException cause_type=StorageUnavailable"]
        if status_code >= 500
        else []
    )
    assert "private" not in caplog.text


def test_photo_transaction_database_failure_diagnostics(caplog):
    db = Mock(spec=Session)
    error = RuntimeError("private database detail")
    db.commit.side_effect = error

    with pytest.raises(RuntimeError) as raised:
        with photo_storage.photo_transaction(db):
            pass

    assert raised.value is error
    db.commit.assert_called_once_with()
    db.rollback.assert_called_once_with()
    assert "Photo transaction failed exception_type=RuntimeError cause_type=none" in caplog.text
    assert "private database detail" not in caplog.text


@pytest.fixture(params=["avatar", "player"])
def existing_photo(request, db, storage):
    owner_id = uuid4()
    old_key = f"old/{owner_id}"
    storage.objects[old_key] = b"original"
    if request.param == "avatar":
        db.add(
            User(id=owner_id, normalized_email=f"{owner_id}@example.com", password_hash="unused")
        )
        db.flush()
        row = UserAvatar(user_id=owner_id, content_type="image/png", storage_key=old_key)
        saver = profile.save_avatar
    else:
        db.add(Player(id=owner_id, display_name="Player", chinese_name="球员"))
        db.flush()
        row = PlayerPhoto(player_id=owner_id, content_type="image/png", storage_key=old_key)
        saver = players.save_player_photo
    db.add(row)
    db.commit()
    return row, lambda: saver(db, owner_id, "image/jpeg", b"replacement"), old_key


def test_replacement_commit_failure_preserves_original(existing_photo, db, storage):
    row, save, old_key = existing_photo
    fail_next_commit(db)
    with pytest.raises(RuntimeError, match="commit failure"):
        save()
    db.refresh(row)
    assert row.storage_key == old_key
    assert row.content_type == "image/png"
    assert storage.objects == {old_key: b"original"}
    assert old_key not in storage.deleted


def test_successful_replacement_uses_new_key_then_retires_old(existing_photo, db, storage):
    row, save, old_key = existing_photo
    save()
    db.refresh(row)
    assert row.storage_key != old_key
    assert storage.objects == {row.storage_key: b"replacement"}
    assert storage.deleted == [old_key]


def test_storage_disabled_keeps_old_key_for_retry(existing_photo, db, storage):
    row, save, old_key = existing_photo
    storage.enabled = storage.configured = False
    save()
    db.refresh(row)
    assert row.storage_key is None
    assert row.data == b"replacement"
    assert db.get(StorageDeletion, old_key) is not None
    assert storage.objects[old_key] == b"original"
    storage.enabled = storage.configured = True
    photo_storage.retry_deletions(db)
    assert db.get(StorageDeletion, old_key) is None
    assert not storage.objects


def test_failed_compensation_is_queued_and_can_be_retried(existing_photo, db, storage):
    row, save, old_key = existing_photo
    storage.fail_delete = True
    fail_next_commit(db)
    with pytest.raises(RuntimeError):
        save()
    keys = list(db.scalars(select(StorageDeletion.storage_key)))
    assert len(keys) == 1
    assert keys[0] != old_key
    assert (
        db.get(type(row), row.id if isinstance(row, UserAvatar) else row.player_id).storage_key
        == old_key
    )
    storage.fail_delete = False
    photo_storage.retry_deletions(db)
    assert storage.objects == {old_key: b"original"}
    assert not list(db.scalars(select(StorageDeletion)))


def test_timed_out_put_is_compensated(existing_photo, db, storage):
    row, save, old_key = existing_photo
    storage.fail_put = True
    with pytest.raises(HTTPException) as error:
        save()
    assert error.value.status_code == 503
    db.refresh(row)
    assert row.storage_key == old_key
    assert storage.objects == {old_key: b"original"}


def test_media_commit_failure_removes_new_object(db, storage):
    user = User(normalized_email=f"{uuid4()}@example.com", password_hash="unused", role="admin")
    db.add(user)
    db.flush()
    album = PhotoAlbum(title="Club photos", created_by=user.id)
    db.add(album)
    db.commit()
    fail_next_commit(db)
    with pytest.raises(RuntimeError):
        media.save_album_photo(("image/png", b"new"), album.id, db, user.id, None, None)
    assert not storage.objects
    assert not list(db.scalars(select(MediaAsset)))


@pytest.mark.parametrize("kind", ["media", "avatar"])
def test_delete_commit_failure_preserves_live_bytes(kind, db, storage):
    user = User(normalized_email=f"{uuid4()}@example.com", password_hash="unused", role="admin")
    db.add(user)
    db.flush()
    key = f"delete/{uuid4()}"
    storage.objects[key] = b"original"
    row = (
        MediaAsset(uploaded_by=user.id, content_type="image/png", size_bytes=8, storage_key=key)
        if kind == "media"
        else UserAvatar(user_id=user.id, content_type="image/png", storage_key=key)
    )
    db.add(row)
    db.commit()
    row_id = row.id
    fail_next_commit(db)
    with pytest.raises(RuntimeError):
        if kind == "media":
            media.delete_photo(row_id, db, user)
        else:
            profile.delete_avatar(db, user)
    assert storage.objects[key] == b"original"
    assert db.get(type(row), row_id) is not None
    # A storage failure after a successful delete must not undo the DB deletion.
    storage.fail_delete = True
    if kind == "media":
        media.delete_photo(row_id, db, user)
    else:
        profile.delete_avatar(db, user)
    assert db.get(type(row), row_id) is None
    assert db.get(StorageDeletion, key) is not None


def test_switch_to_external_photo_url_retires_uploaded_object(db, storage):
    player = service.create(
        db,
        PlayerCreate(
            display_name="Player",
            chinese_name="球员",
            season="2026/2027",
            position="Forwards",
            shirt_number=9,
        ),
    )
    players.save_player_photo(db, player.id, "image/png", b"photo")
    old_key = db.get(PlayerPhoto, player.id).storage_key
    storage.fail_delete = True
    service.update(
        db, player.id, "2026/2027", PlayerUpdate(photo_url="https://example.com/photo.jpg")
    )
    assert db.get(PlayerPhoto, player.id) is None
    assert db.get(StorageDeletion, old_key) is not None
    storage.fail_delete = False
    photo_storage.retry_deletions(db)
    assert not storage.objects


@pytest.mark.parametrize("kind", ["album", "blog", "match", "guestbook", "avatar", "player"])
def test_async_uploads_run_sync_work_off_event_loop(kind, monkeypatch):
    async def exercise():
        event_loop_thread = threading.get_ident()
        threads = []

        def save(*args):
            threads.append(threading.get_ident())

        async def receive():
            return {"type": "http.request", "body": b"\x89PNG\r\n\x1a\nphoto", "more_body": False}

        async def read_image(request):
            return "image/png", b"photo"

        request = Request({"type": "http", "headers": [(b"content-type", b"image/png")]}, receive)
        db, user, identifier = Mock(), SimpleNamespace(id=uuid4()), uuid4()
        if kind == "avatar":
            monkeypatch.setattr(profile, "save_avatar", save)
            await profile.upload_avatar(request, db, user)
        elif kind == "player":
            monkeypatch.setattr(players, "save_player_photo", save)
            await players.upload_player_photo(identifier, request, db)
        else:
            monkeypatch.setattr(media, "read_image", read_image)
            monkeypatch.setattr(media, f"save_{kind}_photo", save)
            args = [identifier, request, db]
            if kind != "guestbook":
                args.append(user)
            await getattr(media, f"upload_{kind}_photo")(*args, caption=None, alt=None)
        assert len(threads) == 1
        assert threads[0] != event_loop_thread

    asyncio.run(exercise())
