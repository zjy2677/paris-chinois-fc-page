"""Match ratings stay tied to the saved squad and the reviewing account."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app.auth import dependencies
from app.auth.service import COOKIE_NAME
from app.database import get_db
from app.main import app
from app.models import (
    Base,
    CompetitionSeason,
    FormationPlacement,
    Match,
    Player,
    SquadMembership,
    Team,
    User,
)
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ORIGIN = {"Origin": "http://localhost:4173"}


@pytest.fixture
def rating_client(tmp_path, monkeypatch):
    engine = create_engine(
        f"sqlite:///{tmp_path}/ratings.db", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        season = CompetitionSeason(
            fla_season_id=2, competition_name="FLA", division="1", season_label="2026/2027"
        )
        home, away = Team(name="Home"), Team(name="Away")
        player, outsider = Player(display_name="Starter"), Player(display_name="Outsider")
        users = [
            User(normalized_email=f"{role}@example.com", password_hash="unused", role=role)
            for role in ("user", "player", "admin")
        ]
        db.add_all([season, home, away, player, outsider, *users])
        db.flush()
        db.add_all(
            [
                SquadMembership(
                    player_id=player.id, season_label=season.season_label, position="Defenders"
                ),
                SquadMembership(
                    player_id=outsider.id, season_label=season.season_label, position="Forwards"
                ),
            ]
        )
        match = Match(
            competition_season_id=season.id,
            source_key=str(uuid4()),
            home_team_id=home.id,
            away_team_id=away.id,
            leg="",
            status="final",
            home_score=1,
            away_score=0,
            source_url="",
            last_synced_at=datetime.now(timezone.utc),
        )
        db.add(match)
        db.flush()
        db.add(FormationPlacement(match_id=match.id, player_id=player.id, placement="bench"))
        db.commit()
        active = {"user": users[1]}

        def session_user(session, token):
            if token != "test-session":
                raise HTTPException(401, "Not authenticated")
            return active["user"], None

        monkeypatch.setattr(dependencies, "resolve_session", session_user)
        dependencies._attempts.clear()
        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app) as client:
                client.cookies.set(COOKIE_NAME, "test-session")
                yield client, db, match, player, outsider, users, active
        finally:
            app.dependency_overrides.pop(get_db, None)
            dependencies._attempts.clear()
    engine.dispose()


def test_ratings_permissions_and_updates(rating_client):
    client, db, match, player, outsider, users, active = rating_client
    root = f"/api/matches/{match.id}"
    url = f"{root}/players/{player.id}/rating"
    initial = client.get(f"{root}/ratings").json()
    assert len(initial) == 2
    assert {entry["participation"] for entry in initial} == {"sub", "absent"}
    assert [entry["display_name"] for entry in initial] == ["Outsider", "Starter"]
    assert client.put(url, json={"stars": 5, "comment": "Great match"}).status_code == 403
    active["user"] = users[0]
    assert client.put(url, json={"stars": 5}, headers=ORIGIN).status_code == 403
    active["user"] = users[1]
    assert client.put(url, json={"stars": 0}, headers=ORIGIN).status_code == 422
    assert client.put(url, json={"stars": 6}, headers=ORIGIN).status_code == 422
    assert (
        client.put(url, json={"stars": 5, "comment": " Great match "}, headers=ORIGIN).status_code
        == 204
    )
    assert client.get(f"{url}/mine").json() == {"stars": 5, "comment": "Great match"}
    assert client.put(url, json={"stars": 4, "comment": ""}, headers=ORIGIN).status_code == 204
    active["user"] = users[2]
    assert client.put(url, json={"stars": 2}, headers=ORIGIN).status_code == 204
    detail = client.get(f"{root}/players/{player.id}/ratings").json()
    assert detail["summary"]["rating_count"] == 2
    assert detail["summary"]["average_stars"] == 3.0
    assert "password_hash" not in str(detail)
    absent = client.get(f"{root}/players/{outsider.id}/ratings").json()
    assert absent["summary"]["participation"] == "absent"
    assert (
        client.put(
            f"{root}/players/{outsider.id}/rating", json={"stars": 5}, headers=ORIGIN
        ).status_code
        == 204
    )
    assert client.get(f"{root}/ratings").json()[0]["player_id"] == str(outsider.id)
    assert client.get(f"{root}/players/{uuid4()}/ratings").status_code == 404
    assert client.delete(url, headers=ORIGIN).status_code == 204
    assert client.get(f"{root}/ratings").json()[0]["rating_count"] == 1
    client.cookies.clear()
    assert client.get(f"{root}/ratings").status_code == 200
    assert client.get(f"{url}/mine").status_code == 401
    assert client.put(url, json={"stars": 5}, headers=ORIGIN).status_code == 401
    assert len(db.scalars(select(Team)).all()) == 2


def test_ratings_open_only_after_final(rating_client):
    client, db, match, player, _, _, _ = rating_client
    match.status = "scheduled"
    match.home_score = None
    match.away_score = None
    db.commit()
    root = f"/api/matches/{match.id}"
    assert client.get(f"{root}/ratings").status_code == 409
    assert (
        client.put(
            f"{root}/players/{player.id}/rating", json={"stars": 5}, headers=ORIGIN
        ).status_code
        == 409
    )


def test_inactive_players_only_remain_rateable_if_placed_in_match(rating_client):
    client, db, match, placed, unplaced, _, _ = rating_client
    root = f"/api/matches/{match.id}"
    placed.active = False
    unplaced.active = False
    db.commit()

    roster = client.get(f"{root}/ratings").json()
    assert [entry["player_id"] for entry in roster] == [str(placed.id)]
    assert roster[0]["participation"] == "sub"
    assert client.get(f"{root}/players/{placed.id}/ratings").status_code == 200
    assert client.get(f"{root}/players/{unplaced.id}/ratings").status_code == 404
    assert (
        client.put(
            f"{root}/players/{unplaced.id}/rating", json={"stars": 5}, headers=ORIGIN
        ).status_code
        == 404
    )
