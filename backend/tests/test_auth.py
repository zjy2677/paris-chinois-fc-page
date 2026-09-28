import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from app.auth.dependencies import _attempts, require_role
from app.auth.router import router
from app.auth.service import COOKIE_NAME, hasher
from app.config import get_settings
from app.database import get_db
from app.models import User
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ORIGIN = {"Origin": "http://localhost:4173"}
CREDENTIALS = {"email": "member@example.com", "password": "A long test password 2026"}


@pytest.fixture
def auth(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    monkeypatch.setenv("JWT_SECRET", "test-signing-key-not-for-production-1234567890")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    _attempts.clear()
    app = FastAPI()
    app.include_router(router)

    @app.get("/admin-check")
    def admin_check(user=Depends(require_role("admin"))):
        return {"role": user.role}

    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            yield client, db
        db.close()
        transaction.rollback()
    engine.dispose()
    get_settings.cache_clear()
    _attempts.clear()


def test_register_user_hash_and_http_only_cookie(auth):
    client, db = auth
    response = client.post("/api/auth/register", json=CREDENTIALS, headers=ORIGIN)
    assert response.status_code == 201
    assert response.json()["role"] == "user"
    assert set(response.json()) == {"id", "email", "role"}
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert "Path=/api" in response.headers["set-cookie"]
    assert response.headers["cache-control"] == "no-store"
    user = db.scalar(select(User).where(User.normalized_email == CREDENTIALS["email"]))
    assert user.password_hash.startswith("$argon2id$")
    assert hasher.verify(user.password_hash, CREDENTIALS["password"])
    assert client.get("/api/auth/me").json()["email"] == CREDENTIALS["email"]


@pytest.mark.parametrize("role", ["player", "admin", "user"])
def test_registration_cannot_supply_role(auth, role):
    client, db = auth
    response = client.post("/api/auth/register", json={**CREDENTIALS, "role": role}, headers=ORIGIN)
    assert response.status_code == 422
    assert db.scalar(select(User).where(User.normalized_email == CREDENTIALS["email"])) is None


def test_origin_password_and_duplicate_validation(auth):
    client, _ = auth
    assert client.post("/api/auth/register", json=CREDENTIALS).status_code == 403
    assert (
        client.post(
            "/api/auth/register", json=CREDENTIALS, headers={"Origin": "https://attacker.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/register", json={**CREDENTIALS, "password": "short"}, headers=ORIGIN
        ).status_code
        == 422
    )
    assert client.post("/api/auth/register", json=CREDENTIALS, headers=ORIGIN).status_code == 201
    assert (
        client.post(
            "/api/auth/register",
            json={**CREDENTIALS, "email": "MEMBER@example.com"},
            headers=ORIGIN,
        ).status_code
        == 409
    )


def test_login_logout_and_replay(auth):
    client, _ = auth
    client.post("/api/auth/register", json=CREDENTIALS, headers=ORIGIN)
    token = client.cookies.get(COOKIE_NAME)
    assert client.post("/api/auth/logout", headers=ORIGIN).status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE_NAME}={token}"}).status_code == 401
    )
    assert (
        client.post(
            "/api/auth/login", json={**CREDENTIALS, "password": "incorrect"}, headers=ORIGIN
        ).status_code
        == 401
    )
    assert client.post("/api/auth/login", json=CREDENTIALS, headers=ORIGIN).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_database_role_and_deactivation_checked_each_request(auth):
    client, db = auth
    client.post("/api/auth/register", json=CREDENTIALS, headers=ORIGIN)
    token = client.cookies.get(COOKIE_NAME)
    # Cookie path is /api, so explicitly pass it to this test-only protected route.
    headers = {"Cookie": f"{COOKIE_NAME}={token}"}
    assert client.get("/admin-check", headers=headers).status_code == 403
    user = db.scalar(select(User).where(User.normalized_email == CREDENTIALS["email"]))
    user.role = "admin"
    db.commit()
    assert client.get("/admin-check", headers=headers).status_code == 200
    user.role = "player"
    db.commit()
    assert client.get("/admin-check", headers=headers).status_code == 403
    assert client.get("/api/auth/me").json()["role"] == "player"
    user.active = False
    db.commit()
    assert client.get("/api/auth/me").status_code == 401


def test_tampered_and_expired_jwt_rejected(auth):
    client, _ = auth
    client.post("/api/auth/register", json=CREDENTIALS, headers=ORIGIN)
    token = client.cookies.get(COOKIE_NAME)
    claims = jwt.decode(token, options={"verify_signature": False})
    forged = jwt.encode(claims, "wrong-signing-key-12345678901234567890", algorithm="HS256")
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE_NAME}={forged}"}).status_code == 401
    )
    claims["exp"] = datetime.now(timezone.utc) - timedelta(seconds=1)
    expired = jwt.encode(claims, get_settings().jwt_secret, algorithm="HS256")
    assert (
        client.get("/api/auth/me", headers={"Cookie": f"{COOKIE_NAME}={expired}"}).status_code
        == 401
    )


def test_auth_throttling(auth):
    client, _ = auth
    for _ in range(10):
        assert client.post("/api/auth/login", json={}, headers=ORIGIN).status_code == 422
    response = client.post("/api/auth/login", json={}, headers=ORIGIN)
    assert response.status_code == 429
    assert response.headers["retry-after"] == "60"
