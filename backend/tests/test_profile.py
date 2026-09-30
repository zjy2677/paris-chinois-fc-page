import asyncio
import os
from unittest.mock import Mock

import pytest
from app.auth.dependencies import _attempts
from app.database import get_db
from app.main import app
from app.profile import MAX_AVATAR_BYTES, upload_avatar
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

ORIGIN = {"Origin": "http://localhost:4173"}
SIGNUP = {
    "email": "avatar@example.com",
    "password": "A long test password 2026",
    "confirm_password": "A long test password 2026",
    "first_name": "Test",
    "last_name": "Member",
    "age": 28,
}
PNG = b"\x89PNG\r\n\x1a\n" + b"minimal-test-image"


@pytest.fixture
def profile_client(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    monkeypatch.setenv("JWT_SECRET", "test-signing-key-not-for-production-1234567890")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    from app.config import get_settings

    get_settings.cache_clear()
    _attempts.clear()
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.pop(get_db, None)
        db.close()
        transaction.rollback()
    engine.dispose()
    get_settings.cache_clear()
    _attempts.clear()


def test_avatar_upload_and_read(profile_client):
    client = profile_client
    assert client.post("/api/auth/register", json=SIGNUP, headers=ORIGIN).status_code == 201
    response = client.put(
        "/api/profile/avatar", content=PNG, headers={**ORIGIN, "Content-Type": "image/png"}
    )
    assert response.status_code == 204
    assert client.get("/api/profile/avatar").content == PNG
    assert client.get("/api/auth/me").json()["avatar_updated_at"] is not None


def test_avatar_rejects_bad_type_and_size(profile_client):
    client = profile_client
    assert client.post("/api/auth/register", json=SIGNUP, headers=ORIGIN).status_code == 201
    assert (
        client.put(
            "/api/profile/avatar",
            content=b"not-an-image",
            headers={**ORIGIN, "Content-Type": "image/png"},
        ).status_code
        == 415
    )
    huge = b"\x89PNG\r\n\x1a\n" + b"x" * (2 * 1024 * 1024)
    assert (
        client.put(
            "/api/profile/avatar", content=huge, headers={**ORIGIN, "Content-Type": "image/png"}
        ).status_code
        == 413
    )


def test_avatar_requires_session(profile_client):
    response = profile_client.get("/api/profile/avatar")
    assert response.status_code == 401


def test_chunked_avatar_stops_reading_at_size_limit():
    chunks = iter([b"x" * MAX_AVATAR_BYTES, b"x"])
    reads = 0

    async def receive():
        nonlocal reads
        reads += 1
        assert reads <= 2, "Upload must stop reading once the limit is exceeded"
        return {"type": "http.request", "body": next(chunks), "more_body": True}

    request = Request({"type": "http", "headers": []}, receive)
    db = Mock()
    with pytest.raises(HTTPException) as error:
        asyncio.run(upload_avatar(request, db, Mock()))
    assert error.value.status_code == 413
    assert reads == 2
    db.scalar.assert_not_called()
    db.commit.assert_not_called()
