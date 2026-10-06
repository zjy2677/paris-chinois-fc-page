import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app import blog, guestbook, media
from app.auth.dependencies import _attempts, current_user
from app.config import get_settings
from app.database import get_db
from app.models import BlogPost, GuestbookMessage, User
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ORIGIN = {"Origin": "http://localhost:4173"}
CONTENT = {"title": "A club story", "body": "Our team played a great match together."}


@pytest.fixture
def community(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    _attempts.clear()
    guestbook._post_attempts.clear()
    app = FastAPI()
    app.include_router(blog.router)
    app.include_router(guestbook.router)
    app.include_router(media.router)
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        user = User(normalized_email=f"{uuid4()}@example.com", password_hash="unused", role="admin")
        db.add(user)
        db.flush()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[current_user] = lambda: user
        with TestClient(app) as client:
            yield client, db, user
        db.close()
        transaction.rollback()
    engine.dispose()
    guestbook._post_attempts.clear()
    _attempts.clear()
    get_settings.cache_clear()


@pytest.mark.parametrize("action", ["publish", "reject"])
@pytest.mark.parametrize("status", ["draft", "pending", "published", "rejected"])
def test_moderation_only_accepts_pending(community, action, status):
    client, db, user = community
    timestamp = datetime.now(timezone.utc) if status == "published" else None
    post = BlogPost(author_id=user.id, status=status, published_at=timestamp, **CONTENT)
    db.add(post)
    db.commit()
    response = client.post(f"/api/blog/posts/{post.id}/{action}", headers=ORIGIN)
    assert response.status_code == (200 if status == "pending" else 409)
    db.refresh(post)
    if status != "pending":
        assert post.status == status and post.published_at == timestamp
    else:
        assert post.status == ("published" if action == "publish" else "rejected")


@pytest.mark.parametrize("status", ["draft", "pending", "published", "rejected"])
def test_edit_preserves_review_queue(community, status):
    client, db, user = community
    user.role = "user"
    post = BlogPost(author_id=user.id, status=status, **CONTENT)
    db.add(post)
    db.commit()
    response = client.patch(
        f"/api/blog/posts/{post.id}", json=CONTENT | {"title": "Changed title"}, headers=ORIGIN
    )
    db.refresh(post)
    if status in ("pending", "published"):
        assert response.status_code == 409
        assert post.status == status and post.title == CONTENT["title"]
    else:
        assert response.status_code == 200
        assert post.status == "draft" and post.title == "Changed title"


def test_missing_posts_and_non_admin_moderation(community):
    client, db, user = community
    assert client.post(f"/api/blog/posts/{uuid4()}/publish", headers=ORIGIN).status_code == 404
    user.role = "user"
    db.commit()
    assert client.post(f"/api/blog/posts/{uuid4()}/reject", headers=ORIGIN).status_code == 403


def test_published_pagination(community):
    client, db, user = community
    now = datetime.now(timezone.utc)
    for i in range(13):
        db.add(
            BlogPost(
                author_id=user.id,
                status="published",
                published_at=now,
                title=f"Story {i}",
                body=CONTENT["body"],
            )
        )
    db.commit()
    first = client.get("/api/blog/posts?offset=0&limit=12").json()
    second = client.get("/api/blog/posts?offset=12&limit=12").json()
    assert first["total"] == second["total"] == 13
    assert len(first["items"]) == 12 and len(second["items"]) == 1
    assert not ({p["id"] for p in first["items"]} & {p["id"] for p in second["items"]})


def test_cookie_removal_cannot_bypass_posting_cooldown(community, monkeypatch):
    client, db, _ = community
    clock = [100.0]
    monkeypatch.setattr(guestbook, "monotonic", lambda: clock[0])
    body = {"nickname": "Supporter", "body": "Great game!"}
    assert client.post("/api/guestbook/messages", json=body, headers=ORIGIN).status_code == 201
    client.cookies.clear()
    result = client.post("/api/guestbook/messages", json=body, headers=ORIGIN)
    assert result.status_code == 429 and result.headers["retry-after"] == "30"
    clock[0] += 30
    assert client.post("/api/guestbook/messages", json=body, headers=ORIGIN).status_code == 201
    assert len(db.scalars(select(GuestbookMessage)).all()) == 2


def test_guestbook_photo_stays_pending_until_admin_approval(community):
    client, _, _ = community
    created = client.post(
        "/api/guestbook/messages",
        json={"nickname": "Supporter", "body": "A photo from the match", "has_photo": True},
        headers=ORIGIN,
    )
    assert created.status_code == 201
    assert created.json()["status"] == "pending"
    assert "Path=/api" in created.headers["set-cookie"]
    message_id = created.json()["id"]
    assert client.get("/api/guestbook/messages").json() == []

    uploaded = client.post(
        f"/api/media/guestbook/{message_id}/photo?alt=Match%20photo",
        content=b"\x89PNG\r\n\x1a\nimage-data",
        headers=ORIGIN | {"Content-Type": "image/png"},
    )
    assert uploaded.status_code == 201
    photo_id = uploaded.json()["id"]
    assert client.get(f"/api/media/photos/{photo_id}/content").status_code == 404

    moderation = client.get("/api/guestbook/moderation")
    assert moderation.status_code == 200
    pending = next(item for item in moderation.json() if item["id"] == message_id)
    assert pending["status"] == "pending"
    assert pending["photo"]["url"] == f"/api/media/photos/{photo_id}/preview"
    preview = client.get(pending["photo"]["url"])
    assert preview.status_code == 200
    assert preview.headers["cache-control"] == "no-store"

    approved = client.post(f"/api/guestbook/messages/{message_id}/restore", headers=ORIGIN)
    assert approved.status_code == 200
    assert approved.json()["status"] == "visible"
    public = client.get("/api/guestbook/messages").json()
    assert public[0]["photo"]["url"] == f"/api/media/photos/{photo_id}/content"
    assert client.get(public[0]["photo"]["url"]).status_code == 200


def test_visible_guestbook_message_rejects_late_photo_upload(community):
    client, _, _ = community
    created = client.post(
        "/api/guestbook/messages",
        json={"nickname": "Supporter", "body": "Text only"},
        headers=ORIGIN,
    )
    response = client.post(
        f"/api/media/guestbook/{created.json()['id']}/photo",
        content=b"\x89PNG\r\n\x1a\nimage-data",
        headers=ORIGIN | {"Content-Type": "image/png"},
    )
    assert response.status_code == 409
