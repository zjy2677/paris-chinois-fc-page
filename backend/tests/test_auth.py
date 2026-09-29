import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.auth.dependencies import _attempts, require_role
from app.auth.router import router
from app.auth.service import COOKIE_NAME, hasher
from app.config import get_settings
from app.database import get_db
from app.models import User

ORIGIN = {"Origin": "http://localhost:4173"}
CREDENTIALS = {"email": "member@example.com", "password": "A long test password 2026"}
SIGNUP = {
    **CREDENTIALS,
    "confirm_password": CREDENTIALS["password"],
    "first_name": "Jun",
    "last_name": "Zhao",
    "age": 28,
}


def signup(client):
    return client.post("/api/auth/register", json=SIGNUP, headers=ORIGIN)


def signup_and_login(client):
    assert signup(client).status_code == 201
    assert client.post("/api/auth/login", json=CREDENTIALS, headers=ORIGIN).status_code == 200


@pytest.fixture
def auth(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    monkeypatch.setenv("JWT_SECRET", "test-signing-key-not-for-production-1234567890")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    for key in ("RESEND_API_KEY", "EMAIL_FROM", "PUBLIC_SITE_URL"):
        monkeypatch.delenv(key, raising=False)
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


def test_register_signs_in_without_email_configuration(auth):
    client, db = auth
    response = signup(client)
    assert response.status_code == 201
    assert response.json()["first_name"] == "Jun"
    assert response.json()["role"] == "user"
    assert response.headers["cache-control"] == "no-store"
    user = db.scalar(select(User).where(User.normalized_email == CREDENTIALS["email"]))
    assert user.email_verified_at is None
    assert (user.first_name, user.last_name, user.age_at_registration) == ("Jun", "Zhao", 28)
    assert hasher.verify(user.password_hash, CREDENTIALS["password"])
    assert client.get("/api/auth/me").status_code == 200
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "SameSite=lax" in response.headers["set-cookie"]
    assert "Path=/api" in response.headers["set-cookie"]


@pytest.mark.parametrize("role", ["player", "admin", "user"])
def test_registration_cannot_supply_role(auth, role):
    client, db = auth
    response = client.post("/api/auth/register", json={**SIGNUP, "role": role}, headers=ORIGIN)
    assert response.status_code == 422
    assert db.scalar(select(User).where(User.normalized_email == CREDENTIALS["email"])) is None


def test_origin_password_and_duplicate_validation(auth):
    client, _ = auth
    assert client.post("/api/auth/register", json=SIGNUP).status_code == 403
    assert (
        client.post(
            "/api/auth/register", json=SIGNUP, headers={"Origin": "https://attacker.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/register", json={**SIGNUP, "password": "short"}, headers=ORIGIN
        ).status_code
        == 422
    )
    assert client.post("/api/auth/register", json=SIGNUP, headers=ORIGIN).status_code == 201
    assert (
        client.post(
            "/api/auth/register",
            json={**SIGNUP, "email": "MEMBER@example.com"},
            headers=ORIGIN,
        ).status_code
        == 409
    )


def test_login_logout_and_replay(auth):
    client, _ = auth
    signup_and_login(client)
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
    signup_and_login(client)
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
    signup_and_login(client)
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


@pytest.mark.parametrize(
    "change",
    [
        {"first_name": "   "},
        {"last_name": ""},
        {"age": 0},
        {"age": 121},
        {"age": 20.5},
        {"age": True},
        {"confirm_password": "different long password"},
    ],
)
def test_profile_validation(auth, change):
    client, _ = auth
    assert (
        client.post("/api/auth/register", json=SIGNUP | change, headers=ORIGIN).status_code == 422
    )


def test_existing_unverified_account_can_login(auth):
    client, db = auth
    user = User(
        normalized_email=CREDENTIALS["email"],
        password_hash=hasher.hash(CREDENTIALS["password"]),
        role="admin",
    )
    db.add(user)
    db.commit()
    response = client.post("/api/auth/login", json=CREDENTIALS, headers=ORIGIN)
    assert response.status_code == 200
    assert response.json()["role"] == "admin" and response.json()["first_name"] is None
    assert client.get("/api/auth/me").status_code == 200
    assert user.email_verified_at is None
