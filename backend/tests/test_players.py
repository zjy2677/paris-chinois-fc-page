import os
from uuid import uuid4

import pytest
from app.auth.dependencies import _attempts
from app.auth.service import COOKIE_NAME, issue_session
from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import Player, SquadMembership, User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ORIGIN = {"Origin": "http://localhost:4173"}
BODY = {
    "display_name": "New Player",
    "chinese_name": "新球员",
    "photo_url": "https://example.com/photo.jpg",
    "shirt_number": 9,
    "position": "Forwards",
    "season": "2026/2027",
}


@pytest.fixture
def player_client(monkeypatch):
    """Yield an admin client and database session, rolling back test changes on teardown."""
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
    """Verify editing, deactivation, restoration, and season visibility preserve player records."""
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
    """Verify signed-out and non-admin callers cannot manage players or list inactive players."""
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
        {"display_name": None},
        {"chinese_name": " "},
        {"chinese_name": None},
        {"chinese_name": "名" * 151},
        {"photo_url": "javascript:alert(1)"},
        {"photo_url": "http://example.com/a.jpg"},
        {"photo_url": "https://user:pass@example.com/a.jpg"},
        {"shirt_number": 0},
        {"shirt_number": True},
        {"shirt_number": 1.5},
        {"position": "invalid"},
        {"active": "false"},
        {"description": "x" * 2001},
    ],
)
def test_invalid_create_and_edit(player_client, change):
    """Verify invalid player fields are rejected during both creation and partial updates."""
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
    """Verify origin checks, shirt conflicts, missing targets, and invalid season rejection."""
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


def test_description_lifecycle_and_public_profile(player_client):
    client, _, _ = player_client
    created = client.post(
        "/api/players", json=BODY | {"description": "  Creative midfielder.  "}, headers=ORIGIN
    )
    assert created.status_code == 201
    path = f"/api/players/{created.json()['id']}"
    assert client.get(path).json()["description"] == "Creative midfielder."
    edited = client.patch(
        path + "?season=2026/2027", json={"description": "Captain."}, headers=ORIGIN
    )
    assert edited.status_code == 200
    assert client.get(path).json()["description"] == "Captain."
    assert (
        client.patch(
            path + "?season=2026/2027", json={"description": None}, headers=ORIGIN
        ).status_code
        == 200
    )
    assert client.delete(path, headers=ORIGIN).status_code == 204
    client.cookies.clear()
    profile = client.get(path)
    assert profile.status_code == 200
    assert profile.json()["active"] is False
    assert profile.json()["description"] is None
    assert profile.json()["goals"] == profile.json()["assists"] == 0
    assert profile.json()["squads"] == [
        {
            "season": "2026/2027",
            "position": "Forwards",
            "alternate_positions": [],
            "shirt_number": 9,
        }
    ]
    assert "normalized_email" not in profile.json()
    assert client.get(f"/api/players/{uuid4()}").status_code == 404
    assert client.get("/api/players/not-a-uuid").status_code == 422


def test_alternate_positions_and_uploaded_photo(player_client):
    client, _, _ = player_client
    created = client.post(
        "/api/players",
        json=BODY | {"alternate_positions": ["Midfielders", "Defenders"]},
        headers=ORIGIN,
    )
    assert created.status_code == 201, created.text
    player = created.json()
    assert player["position"] == "Forwards"
    assert player["alternate_positions"] == ["Midfielders", "Defenders"]
    photo_path = f"/api/players/{player['id']}/photo"
    png = b"\x89PNG\r\n\x1a\n" + b"test-image"
    uploaded = client.put(photo_path, content=png, headers=ORIGIN | {"Content-Type": "image/png"})
    assert uploaded.status_code == 204, uploaded.text
    public = client.get("/api/players?season=2026/2027").json()[0]
    assert public["has_uploaded_photo"] is True
    image = client.get(photo_path)
    assert image.status_code == 200 and image.content == png
    assert image.headers["content-type"] == "image/png"


def test_position_validation():
    from app.players.schemas import PlayerCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PlayerCreate.model_validate(BODY | {"alternate_positions": ["Forwards"]})
    with pytest.raises(ValidationError):
        PlayerCreate.model_validate(BODY | {"alternate_positions": ["Defenders", "Defenders"]})


@pytest.mark.parametrize("name", ["display_name", "chinese_name"])
def test_both_names_required_on_create(player_client, name):
    client, _, _ = player_client
    payload = {key: value for key, value in BODY.items() if key != name}
    assert client.post("/api/players", json=payload, headers=ORIGIN).status_code == 422
    assert client.get("/api/players").json() == []


def test_bilingual_names_create_update_and_public_responses(player_client):
    client, db, _ = player_client
    names = {"display_name": "  Zhang Wei  ", "chinese_name": "  张伟  "}
    created = client.post("/api/players", json=BODY | names, headers=ORIGIN)
    assert created.status_code == 201, created.text
    player_id = created.json()["id"]
    path = f"/api/players/{player_id}"
    expected = {"display_name": "Zhang Wei", "chinese_name": "张伟"}
    for key, value in expected.items():
        assert created.json()[key] == value
        assert client.get("/api/admin/players").json()[0][key] == value
    edited = client.patch(
        path + "?season=2026/2027", json={"chinese_name": "  张玮  "}, headers=ORIGIN
    )
    assert edited.status_code == 200, edited.text
    assert edited.json()["display_name"] == "Zhang Wei"
    assert edited.json()["chinese_name"] == "张玮"
    assert (
        db.scalar(select(Player).where(Player.display_name == "Zhang Wei")).chinese_name == "张玮"
    )
    client.cookies.clear()
    for data in [client.get(path).json(), client.get("/api/players").json()[0]]:
        assert data["display_name"] == "Zhang Wei"
        assert data["chinese_name"] == "张玮"


def test_legacy_player_can_be_read_and_given_a_chinese_name(player_client):
    client, db, _ = player_client
    legacy = Player(display_name="Existing Player")
    db.add(legacy)
    db.flush()
    db.add(SquadMembership(player_id=legacy.id, season_label="2026/2027", position="Defenders"))
    db.commit()
    path = f"/api/players/{legacy.id}"
    assert client.get(path).json()["chinese_name"] is None
    assert client.get("/api/players").json()[0]["display_name"] == "Existing Player"
    # Partial status changes remain possible before a legacy player's name is filled in.
    edit = client.patch(path + "?season=2026/2027", json={"active": False}, headers=ORIGIN)
    assert edit.status_code == 200 and edit.json()["chinese_name"] is None
    edit = client.patch(path + "?season=2026/2027", json={"chinese_name": "老队员"}, headers=ORIGIN)
    assert edit.status_code == 200
    assert edit.json()["display_name"] == "Existing Player"
    assert client.get(path).json()["chinese_name"] == "老队员"
