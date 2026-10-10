"""Formation permissions and persistence against an isolated database."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.auth import dependencies
from app.auth.service import COOKIE_NAME
from app.database import get_db
from app.main import app
from app.models import (
    Base,
    CompetitionSeason,
    Match,
    MatchEvent,
    MatchGoal,
    Player,
    SquadMembership,
    Team,
    User,
)

ORIGIN = {"Origin": "http://localhost:4173"}


@pytest.fixture
def board_client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path}/board.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        teams = [Team(name="Home"), Team(name="Away")]
        season = CompetitionSeason(
            fla_season_id=2, competition_name="FLA", division="1", season_label="2026/2027"
        )
        players = [Player(display_name=f"Player {n}", chinese_name=f"球员{n}") for n in range(3)]
        user = User(normalized_email="coach@example.com", password_hash="unused", role="player")
        db.add_all([*teams, *players, season, user])
        db.flush()
        db.add_all(
            [
                SquadMembership(
                    player_id=p.id,
                    season_label="2026/2027",
                    position="Defenders",
                    shirt_number=n + 1,
                )
                for n, p in enumerate(players[:2])
            ]
        )
        matches = [
            Match(
                competition_season_id=season.id,
                source_key=str(uuid4()),
                home_team_id=teams[0].id,
                away_team_id=teams[1].id,
                leg="",
                status="scheduled",
                source_url="",
                last_synced_at=datetime.now(timezone.utc),
            )
            for _ in range(2)
        ]
        db.add_all(matches)
        db.commit()

        # Authentication itself is covered by auth tests; exercise actual role/origin dependencies.
        def session_user(session, token):
            if token != "test-session":
                raise HTTPException(401, "Not authenticated")
            return user, None

        monkeypatch.setattr(dependencies, "resolve_session", session_user)
        dependencies._attempts.clear()
        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app) as client:
                client.cookies.set(COOKIE_NAME, "test-session")
                yield client, db, matches, players, user, teams
        finally:
            app.dependency_overrides.pop(get_db, None)
            dependencies._attempts.clear()
    engine.dispose()


def payload(player, placement="pitch"):
    return {
        "placements": [
            {
                "player_id": str(player.id),
                "placement": placement,
                "x": 25 if placement == "pitch" else None,
                "y": 75 if placement == "pitch" else None,
            }
        ]
    }


def test_permissions_persistence_and_final_transition(board_client):
    client, db, matches, players, user, _ = board_client
    url = f"/api/formations/{matches[0].id}"
    client.cookies.clear()
    assert client.get(url).status_code == 401
    assert client.put(url, json=payload(players[0]), headers=ORIGIN).status_code == 401
    client.cookies.set(COOKIE_NAME, "test-session")
    user.role = "user"
    db.commit()
    assert client.get(url).status_code == 403
    assert client.put(url, json=payload(players[0]), headers=ORIGIN).status_code == 403
    for role in ("player", "admin"):
        user.role = role
        db.commit()
        response = client.put(url, json=payload(players[0]), headers=ORIGIN)
        assert response.status_code == 200, response.text
        assert response.headers["cache-control"] == "no-store"
    db.expire_all()
    assert client.get(url).json()["placements"] == payload(players[0])["placements"]
    assert client.get(f"/api/formations/{matches[1].id}").json()["placements"] == []
    assert client.put(url, json=payload(players[0])).status_code == 403
    players[0].active = False
    matches[0].status = "final"
    matches[0].home_score = 1
    matches[0].away_score = 0
    db.commit()
    user.role = "player"
    db.commit()
    assert client.put(url, json={"placements": []}, headers=ORIGIN).status_code == 409
    assert not client.get(url).json()["editable"]
    user.role = "admin"
    db.commit()
    admin_board = client.get(url).json()
    assert admin_board["editable"]
    assert {p["id"] for p in admin_board["players"]} == {
        str(players[0].id),
        str(players[1].id),
    }
    assert client.put(url, json=payload(players[2]), headers=ORIGIN).status_code == 422
    saved = client.put(url, json=payload(players[1]), headers=ORIGIN)
    assert saved.status_code == 200, saved.text
    assert saved.json()["editable"]
    client.cookies.clear()
    response = client.get(url)
    assert response.status_code == 200
    assert not response.json()["editable"]
    assert response.json()["placements"] == payload(players[1])["placements"]
    assert [p["id"] for p in response.json()["players"]] == [str(players[1].id)]
    assert "password_hash" not in response.text


def test_invalid_placements_do_not_replace_saved_board(board_client):
    client, _, matches, players, _, _ = board_client
    url = f"/api/formations/{matches[0].id}"
    assert client.put(url, json=payload(players[0]), headers=ORIGIN).status_code == 200
    duplicate = payload(players[0])
    duplicate["placements"] *= 2
    assert client.put(url, json=duplicate, headers=ORIGIN).status_code == 422
    invalid = payload(players[0])
    invalid["placements"][0]["x"] = 101
    assert client.put(url, json=invalid, headers=ORIGIN).status_code == 422
    invalid = payload(players[0])
    invalid["placements"][0]["placement"] = "bench"
    assert client.put(url, json=invalid, headers=ORIGIN).status_code == 422
    assert client.put(url, json=payload(players[2]), headers=ORIGIN).status_code == 422
    assert client.get(url).json()["placements"] == payload(players[0])["placements"]
    assert client.put(url, json=payload(players[0], "bench"), headers=ORIGIN).status_code == 200
    assert client.put(url, json={"placements": []}, headers=ORIGIN).status_code == 200
    assert client.get(url).json()["placements"] == []


def test_goal_sources_and_cancelled_game(board_client):
    client, db, matches, players, user, teams = board_client
    match = matches[0]
    url = f"/api/formations/{match.id}"
    db.add(
        MatchGoal(
            match_id=match.id,
            team_id=teams[0].id,
            scorer_id=players[0].id,
            assist_player_id=players[1].id,
            goal_type="regular",
        )
    )
    db.add(
        MatchGoal(
            match_id=match.id, team_id=teams[0].id, scorer_id=players[0].id, goal_type="own_goal"
        )
    )
    db.commit()
    roster = {p["id"]: p for p in client.get(url).json()["players"]}
    assert roster[str(players[0].id)]["goals"] == 1
    assert roster[str(players[1].id)]["assists"] == 1
    db.add(
        MatchEvent(
            match_id=match.id,
            event_type="goal",
            player_id=players[1].id,
            assist_player_id=players[0].id,
            sequence=0,
        )
    )
    db.commit()
    roster = {p["id"]: p for p in client.get(url).json()["players"]}
    assert roster[str(players[0].id)]["goals"] == 0
    assert roster[str(players[1].id)]["goals"] == 1
    match.status = "cancelled"
    user.role = "admin"
    db.commit()
    assert client.put(url, json=payload(players[0]), headers=ORIGIN).status_code == 409
    assert not client.get(url).json()["editable"]
    client.cookies.clear()
    assert client.get(url).status_code == 401
