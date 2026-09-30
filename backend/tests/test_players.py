import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.auth.dependencies import _attempts
from app.auth.service import COOKIE_NAME, issue_session
from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import Player, SquadMembership, User

ORIGIN = {"Origin": "http://localhost:4173"}
BODY = {
    "display_name": "New Player",
    "photo_url": "https://example.com/photo.jpg",
    "shirt_number": 9,
    "position": "Forwards",
    "season": "2026/2027",
}


@pytest.fixture
def player_client(monkeypatch):
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    monkeypatch.setenv("JWT_SECRET", "test-signing-key-not-for-production-1234567890")
    get_settings.cache_clear()
    _attempts.clear()
    with engine.connect() as connection:
        tx = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        user = User(normalized_email=f"{uuid4()}@example.com", password_hash="unused", role="admin")
        db.add(user)
        db.flush()
        token = issue_session(db, user)
        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app) as client:
                client.cookies.set(COOKIE_NAME, token)
                yield client, db, user
        finally:
            app.dependency_overrides.pop(get_db, None)
            db.close()
            tx.rollback()
            engine.dispose()
            get_settings.cache_clear()
            _attempts.clear()


def test_player_lifecycle_and_public_visibility(player_client):
    client, db, user = player_client
    response = client.post("/api/players", json=BODY, headers=ORIGIN)
    assert response.status_code == 201, response.text
    player_id = response.json()["id"]
    path = f"/api/players/{player_id}"
    edit = client.patch(
        path + "?season=2026/2027",
        json={"display_name": "Updated Player", "photo_url": None, "shirt_number": None},
        headers=ORIGIN,
    )
    assert edit.status_code == 200, edit.text
    assert edit.json()["photo_url"] is None and edit.json()["shirt_number"] is None
    assert client.delete(path, headers=ORIGIN).status_code == 204
    assert client.get("/api/players?season=2026/2027").json() == []
    assert client.get("/api/admin/players?season=2026/2027").json()[0]["active"] is False
    assert db.scalar(select(Player).where(Player.display_name == "Updated Player")) is not None
    assert (
        db.scalar(select(SquadMembership).where(SquadMembership.season_label == "2026/2027"))
        is not None
    )
    restored = client.patch(path + "?season=2026/2027", json={"active": True}, headers=ORIGIN)
    assert restored.status_code == 200
    client.cookies.clear()
    assert client.get("/api/players?season=2026/2027").json()[0]["display_name"] == "Updated Player"
    assert client.get("/api/players?season=2025/2026").json() == []


@pytest.mark.parametrize("role, status", [(None, 401), ("user", 403), ("player", 403)])
def test_admin_required(player_client, role, status):
    client, db, user = player_client
    if role is None:
        client.cookies.clear()
    else:
        user.role = role
        db.commit()
    assert client.get("/api/admin/players").status_code == status
    assert client.post("/api/players", json=BODY, headers=ORIGIN).status_code == status
    assert (
        client.patch(
            f"/api/players/{uuid4()}?season=2026/2027", json={"active": False}, headers=ORIGIN
        ).status_code
        == status
    )
    assert client.delete(f"/api/players/{uuid4()}", headers=ORIGIN).status_code == status


@pytest.mark.parametrize(
    "change",
    [
        {"display_name": " "},
        {"photo_url": "javascript:alert(1)"},
        {"photo_url": "http://example.com/a.jpg"},
        {"photo_url": "https://user:pass@example.com/a.jpg"},
        {"shirt_number": 0},
        {"shirt_number": True},
        {"shirt_number": 1.5},
        {"position": "invalid"},
        {"active": "false"},
    ],
)
def test_invalid_create_and_edit(player_client, change):
    client, _, _ = player_client
    assert client.post("/api/players", json=BODY | change, headers=ORIGIN).status_code == 422
    created = client.post("/api/players", json=BODY, headers=ORIGIN).json()
    assert (
        client.patch(
            f"/api/players/{created['id']}?season=2026/2027", json=change, headers=ORIGIN
        ).status_code
        == 422
    )


def test_duplicate_shirt_and_invalid_targets(player_client):
    client, _, _ = player_client
    assert client.post("/api/players", json=BODY).status_code == 403
    one = client.post("/api/players", json=BODY, headers=ORIGIN).json()
    assert client.post("/api/players", json=BODY, headers=ORIGIN).status_code == 409
    two = client.post("/api/players", json=BODY | {"shirt_number": 10}, headers=ORIGIN).json()
    assert (
        client.patch(
            f"/api/players/{two['id']}?season=2026/2027", json={"shirt_number": 9}, headers=ORIGIN
        ).status_code
        == 409
    )
    assert (
        client.patch(
            f"/api/players/{one['id']}?season=2025/2026",
            json={"display_name": "Wrong season"},
            headers=ORIGIN,
        ).status_code
        == 404
    )
    assert client.delete(f"/api/players/{uuid4()}", headers=ORIGIN).status_code == 404
    assert (
        client.post("/api/players", json=BODY | {"season": "2026/2029"}, headers=ORIGIN).status_code
        == 422
    )
    assert len(client.get("/api/players").json()) == 2
