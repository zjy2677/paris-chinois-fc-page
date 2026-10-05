import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app.auth.dependencies import _attempts
from app.auth.service import COOKIE_NAME, issue_session
from app.config import get_settings
from app.database import get_db
from app.main import app
from app.models import CompetitionSeason, Match, Player, SquadMembership, Team, User
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

ORIGIN = {"Origin": "http://localhost:4173"}


@pytest.fixture
def goals_client(monkeypatch):
    """Yield an admin client with seeded matches and players; roll back changes on teardown."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Requires disposable TEST_DATABASE_URL")
    engine = create_engine(url)
    assert engine.url.database.endswith("_test")
    monkeypatch.setenv("JWT_SECRET", "test-signing-key-not-for-production-1234567890")
    get_settings.cache_clear()
    _attempts.clear()
    with engine.connect() as connection:
        transaction = connection.begin()
        db = Session(bind=connection, join_transaction_mode="create_savepoint")
        teams = [
            Team(name=name, fla_team_id=-(uuid4().int % 1000000000))
            for name in ("Home", "Away", "Other")
        ]
        players = [Player(display_name=name) for name in ("Scorer", "Assistant")]
        season = CompetitionSeason(
            fla_championship_id=14,
            fla_season_id=uuid4().int % 1000000000,
            competition_name="FLA",
            division="1",
            season_label="2026/2027",
        )
        user = User(normalized_email=f"{uuid4()}@example.com", password_hash="unused", role="admin")
        db.add_all([*teams, *players, season, user])
        db.flush()
        matches = [
            Match(
                competition_season_id=season.id,
                source_key=str(uuid4()),
                home_team_id=teams[0].id,
                away_team_id=teams[1].id,
                matchday=n,
                leg="",
                status="final",
                home_score=3,
                away_score=1,
                source_url="https://example.com/match",
                last_synced_at=datetime.now(timezone.utc),
            )
            for n in (1, 2)
        ]
        db.add_all(matches)
        db.flush()
        token = issue_session(db, user)
        app.dependency_overrides[get_db] = lambda: db
        try:
            with TestClient(app) as client:
                client.cookies.set(COOKIE_NAME, token)
                yield client, db, matches, teams, players, user
        finally:
            app.dependency_overrides.pop(get_db, None)
            db.close()
            transaction.rollback()
            engine.dispose()
            get_settings.cache_clear()
            _attempts.clear()


def goal_body(teams, players):
    """Build a valid stoppage-time goal payload using the supplied team and players."""
    return {
        "team_id": str(teams[0].id),
        "scorer_id": str(players[0].id),
        "assist_player_id": str(players[1].id),
        "minute": 45,
        "stoppage_minute": 2,
    }


def test_goal_lifecycle_and_public_match_detail(goals_client):
    """Verify goal CRUD and public player details without altering the official match score."""
    client, db, matches, teams, players, user = goals_client
    base = f"/api/matches/{matches[0].id}"
    response = client.post(f"{base}/goals", json=goal_body(teams, players), headers=ORIGIN)
    assert response.status_code == 201, response.text
    goal = response.json()
    assert goal["scorer"]["display_name"] == "Scorer"
    assert goal["assist_player"]["display_name"] == "Assistant"
    path = f"{base}/goals/{goal['id']}"
    response = client.patch(
        path, json={"scorer_id": str(players[1].id), "assist_player_id": None}, headers=ORIGIN
    )
    assert response.status_code == 200, response.text
    assert response.json()["scorer"]["display_name"] == "Assistant"
    assert response.json()["assist_player"] is None
    client.cookies.clear()
    assert len(client.get(f"{base}/goals").json()) == 1
    detail = client.get(base)
    assert detail.status_code == 200, detail.text
    assert detail.json()["goals"][0]["id"] == goal["id"]
    assert (detail.json()["home_score"], detail.json()["away_score"]) == (3, 1)
    client.cookies.set(COOKIE_NAME, issue_session(db, user))
    assert client.delete(path, headers=ORIGIN).status_code == 204
    assert client.get(f"{base}/goals").json() == []
    assert client.delete(path, headers=ORIGIN).status_code == 404


@pytest.mark.parametrize("role, expected", [(None, 401), ("user", 403), ("player", 403)])
def test_goal_mutations_require_admin(goals_client, role, expected):
    """Verify signed-out and non-admin callers cannot create, edit, or delete goals."""
    client, db, matches, teams, players, user = goals_client
    if role is None:
        client.cookies.clear()
    else:
        user.role = role
        db.commit()
    base = f"/api/matches/{matches[0].id}/goals"
    body = goal_body(teams, players)
    assert client.post(base, json=body, headers=ORIGIN).status_code == expected
    assert (
        client.patch(f"{base}/{uuid4()}", json={"minute": 1}, headers=ORIGIN).status_code
        == expected
    )
    assert client.delete(f"{base}/{uuid4()}", headers=ORIGIN).status_code == expected


def test_goals_are_scoped_to_match_and_origin(goals_client):
    """Verify writes require a trusted origin and goals cannot be edited through another match."""
    client, _, matches, teams, players, _ = goals_client
    base = f"/api/matches/{matches[0].id}/goals"
    body = goal_body(teams, players)
    assert client.post(base, json=body).status_code == 403
    goal = client.post(base, json=body, headers=ORIGIN).json()
    wrong = f"/api/matches/{matches[1].id}/goals/{goal['id']}"
    assert client.patch(wrong, json={"minute": 1}, headers=ORIGIN).status_code == 404
    assert client.delete(wrong, headers=ORIGIN).status_code == 404
    assert len(client.get(base).json()) == 1
    assert client.get(f"/api/matches/{uuid4()}/goals").status_code == 404
    assert (
        client.post(f"/api/matches/{uuid4()}/goals", json=body, headers=ORIGIN).status_code == 404
    )


@pytest.mark.parametrize(
    "change",
    [
        {"minute": -1},
        {"minute": True},
        {"minute": 1.5},
        {"stoppage_minute": 0},
        {"minute": None, "stoppage_minute": 2},
        {"goal_type": "shootout"},
        {"goal_type": "own_goal"},
        {"scorer_id": str(uuid4())},
        {"assist_player_id": str(uuid4())},
        {"team_id": None},
        {"goal_type": None},
        {"unexpected": "value"},
    ],
)
def test_invalid_goal_input(goals_client, change):
    """Verify invalid create and patch payloads are rejected without changing the stored minute."""
    client, _, matches, teams, players, _ = goals_client
    base = f"/api/matches/{matches[0].id}/goals"
    body = goal_body(teams, players)
    created = client.post(base, json=body, headers=ORIGIN).json()
    assert client.post(base, json=body | change, headers=ORIGIN).status_code == 422
    assert client.patch(f"{base}/{created['id']}", json=change, headers=ORIGIN).status_code == 422
    assert client.get(base).json()[0]["minute"] == 45


def test_goal_rules_allow_unknown_and_own_goals(goals_client):
    """Verify cross-field rules, valid own goals, and unknown goals sorting after timed goals."""
    client, _, matches, teams, players, _ = goals_client
    base = f"/api/matches/{matches[0].id}/goals"
    body = goal_body(teams, players)
    assert (
        client.post(base, json=body | {"team_id": str(teams[2].id)}, headers=ORIGIN).status_code
        == 422
    )
    assert (
        client.post(
            base, json=body | {"assist_player_id": body["scorer_id"]}, headers=ORIGIN
        ).status_code
        == 422
    )
    goal = client.post(base, json=body, headers=ORIGIN).json()
    path = f"{base}/{goal['id']}"
    assert (
        client.patch(path, json={"scorer_id": body["assist_player_id"]}, headers=ORIGIN).status_code
        == 422
    )
    assert client.patch(path, json={}, headers=ORIGIN).status_code == 422
    assert (
        client.patch(
            path, json={"goal_type": "own_goal", "assist_player_id": None}, headers=ORIGIN
        ).status_code
        == 200
    )
    unknown = client.post(base, json={"team_id": str(teams[0].id)}, headers=ORIGIN)
    assert unknown.status_code == 201
    assert unknown.json()["scorer"] is None
    assert client.get(base).json()[-1]["id"] == unknown.json()["id"]


def test_profile_totals_follow_goal_changes_without_membership_duplicates(goals_client):
    client, db, matches, teams, players, _ = goals_client
    db.add_all(
        [
            SquadMembership(
                player_id=players[0].id, season_label=season, position="Forwards", shirt_number=11
            )
            for season in ("2025/2026", "2026/2027")
        ]
    )
    db.commit()
    base = f"/api/matches/{matches[0].id}/goals"
    body = goal_body(teams, players)
    regular = client.post(base, json=body, headers=ORIGIN).json()
    penalty = client.post(
        f"/api/matches/{matches[1].id}/goals", json=body | {"goal_type": "penalty"}, headers=ORIGIN
    )
    assert penalty.status_code == 201
    own = client.post(
        base, json=body | {"goal_type": "own_goal", "assist_player_id": None}, headers=ORIGIN
    )
    assert own.status_code == 201
    assert client.post(base, json={"team_id": str(teams[0].id)}, headers=ORIGIN).status_code == 201
    scorer_path = f"/api/players/{players[0].id}"
    assistant_path = f"/api/players/{players[1].id}"
    profile = client.get(scorer_path).json()
    assert profile["goals"] == 2
    assert profile["assists"] == 0
    assert [s["season"] for s in profile["squads"]] == ["2026/2027", "2025/2026"]
    assert client.get(assistant_path).json()["assists"] == 2
    assert client.get(assistant_path).json()["squads"] == []
    changed = client.patch(
        f"{base}/{regular['id']}",
        json={"scorer_id": str(players[1].id), "assist_player_id": None},
        headers=ORIGIN,
    )
    assert changed.status_code == 200
    assert client.get(scorer_path).json()["goals"] == 1
    assert client.get(assistant_path).json()["goals"] == 1
    assert client.get(assistant_path).json()["assists"] == 1
    assert client.delete(f"{base}/{regular['id']}", headers=ORIGIN).status_code == 204
    assert client.get(assistant_path).json()["goals"] == 0


def test_match_record_rejects_neutral_fixture(goals_client):
    client, db, matches, teams, _, _ = goals_client
    if db.scalar(select(Team).where(Team.fla_team_id == 322)) is None:
        teams[2].fla_team_id = 322
    db.commit()
    response = client.put(
        f"/api/admin/matches/{matches[0].id}/record",
        json={"description": "Should not save", "events": [{"event_type": "goal"}]},
        headers=ORIGIN,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Records can only be edited for club matches"
    assert client.get(f"/api/matches/{matches[0].id}").json()["description"] is None


@pytest.mark.parametrize("club_index", [0, 1])
def test_match_record_rejects_self_assist_and_accepts_valid_pair(goals_client, club_index):
    client, db, matches, teams, players, _ = goals_client
    club = db.scalar(select(Team).where(Team.fla_team_id == 322))
    match = matches[0]
    if club is None:
        teams[club_index].fla_team_id = 322
    elif club_index == 0:
        match.home_team_id = club.id
    else:
        match.away_team_id = club.id
    db.commit()
    count = match.home_score if club_index == 0 else match.away_score
    events = [{"event_type": "goal"} for _ in range(count)]
    events[0].update(player_id=str(players[0].id), assist_player_id=str(players[0].id))
    path = f"/api/admin/matches/{match.id}/record"
    response = client.put(path, json={"events": events}, headers=ORIGIN)
    assert response.status_code == 422
    assert response.json()["detail"] == "A scorer cannot assist their own goal"
    assert client.get(f"/api/matches/{match.id}").json()["events"] == []
    events[0]["assist_player_id"] = str(players[1].id)
    response = client.put(path, json={"description": "Saved", "events": events}, headers=ORIGIN)
    assert response.status_code == 200, response.text
    assert len(response.json()["events"]) == count
    assert response.json()["description"] == "Saved"
