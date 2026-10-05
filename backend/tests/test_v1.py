import os
from dataclasses import replace
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from etl.config import SourceConfig
from etl.load import load
from etl.parse_fixtures import parse_fixtures
from etl.parse_standings import parse_standings
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.models import Match, StandingsSnapshot, SyncRun, Team

FIXTURES = Path(__file__).parents[2] / "etl/tests/fixtures"


@pytest.fixture
def parsed():
    config = SourceConfig()
    rows = parse_standings((FIXTURES / "standings.html").read_text(), config)
    fixtures, skipped = parse_fixtures((FIXTURES / "fixtures.html").read_text(), rows, config)
    return config, rows, fixtures, skipped


def test_source_parse_and_dedup(parsed):
    _, rows, fixtures, skipped = parsed
    assert len(rows) == 14
    assert len(fixtures) == 29
    assert skipped == 0
    assert all(f.kickoff.utcoffset() is not None for f in fixtures)
    assert sum(f.competition_kind == "cup" for f in fixtures) == 3
    assert next(f for f in fixtures if f.status == "final").home_score == 3


def test_wrong_season_rejected():
    html = (FIXTURES / "standings.html").read_text()
    with pytest.raises(ValueError):
        parse_standings(html, replace(SourceConfig(), season_id=999))


def test_partial_table_rejected():
    from bs4 import BeautifulSoup

    soup = BeautifulSoup((FIXTURES / "standings.html").read_text(), "html.parser")
    soup.select("tbody tr")[-1].decompose()
    with pytest.raises(ValueError):
        parse_standings(str(soup), SourceConfig())


def test_unknown_opponent_rejected(parsed):
    config, rows, _, _ = parsed
    html = (FIXTURES / "fixtures.html").read_text().replace("Reçoit ASTERIA", "Reçoit UNKNOWN")
    with pytest.raises(ValueError, match="Unmapped"):
        parse_fixtures(html, rows, config)


@pytest.fixture
def engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a migrated disposable PostgreSQL database")
    engine = create_engine(url)
    if not engine.url.database.endswith("_test"):
        raise ValueError("Tests require a database name ending in _test")
    yield engine
    engine.dispose()


def test_import_atomicity_and_api(engine, parsed, monkeypatch):
    from app.config import get_settings
    from app.database import get_db

    config, rows, fixtures, _ = parsed
    load(engine, config, rows, fixtures)
    with Session(engine) as db:
        before_ids = set(db.scalars(select(Match.id)))
        snapshots_before = db.scalar(select(func.count()).select_from(StandingsSnapshot))
    load(engine, config, rows, fixtures)
    corrected = replace(
        fixtures[0],
        kickoff=fixtures[0].kickoff + timedelta(days=1),
        status="final",
        home_score=2,
        away_score=1,
    )
    load(engine, config, rows, [corrected, *fixtures[1:]])
    with Session(engine) as db:
        assert set(db.scalars(select(Match.id))) == before_ids
        assert db.scalar(select(func.count()).select_from(StandingsSnapshot)) == snapshots_before
        match = db.scalar(select(Match).where(Match.source_key == corrected.source_key))
        assert match.home_score == 2
        match_id = str(match.id)
        original_name = db.scalar(select(Team.name).where(Team.fla_team_id == rows[0].team_id))
    with pytest.raises(KeyError):
        load(
            engine,
            config,
            [replace(rows[0], name="SHOULD ROLLBACK"), *rows[1:]],
            [replace(fixtures[0], home_id=999999)],
        )
    with Session(engine) as db:
        assert (
            db.scalar(select(Team.name).where(Team.fla_team_id == rows[0].team_id)) == original_name
        )
        assert (
            db.scalar(select(SyncRun.status).order_by(SyncRun.started_at.desc()).limit(1))
            == "failed"
        )
    monkeypatch.setenv("DATABASE_URL", str(engine.url.render_as_string(hide_password=False)))
    get_settings.cache_clear()
    from app.main import app

    def test_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as client:
            assert client.get("/api/health").status_code == 200
            assert client.get("/api/ready").status_code == 200
            page = client.get("/api/matches?limit=2").json()
            assert page["total"] == 29 and len(page["items"]) == 2
            assert client.get("/api/matches?limit=101").status_code == 422
            assert client.get(f"/api/matches/{uuid4()}").status_code == 404
            detail = client.get(f"/api/matches/{match_id}").json()
            assert detail["home_score"] == 2 and detail["videos"] == []
            assert "source_key" not in detail
            assert len(client.get("/api/standings").json()["rows"]) == 14
            assert (
                client.get(f"/api/standings?competition_season_id={uuid4()}").json()["rows"] == []
            )
            assert client.get("/api/players").json() == []
            assert (
                client.post(
                    "/api/contact-messages",
                    json={
                        "name": "Test",
                        "email": "test@example.com",
                        "subject": "Test",
                        "message": "Hello",
                    },
                ).status_code
                == 503
            )
    finally:
        app.dependency_overrides.clear()
        get_settings.cache_clear()


def test_away_result_orientation(parsed):
    from bs4 import BeautifulSoup

    config, rows, _, _ = parsed
    soup = BeautifulSoup((FIXTURES / "fixtures.html").read_text(), "html.parser")
    card = next(
        c
        for c in soup.select('[data-testid="rencontre"]')
        if "Championnat" in c.get_text() and "Se déplace chez" in c.get_text()
    )
    for span in card.select("span"):
        if span.get_text(strip=True) == "À jouer":
            span.replace_with(
                BeautifulSoup(
                    '<span data-testid="rencontre-score">3 – 1</span><span>V</span>', "html.parser"
                )
            )
            break
    fixtures, _ = parse_fixtures(str(card), rows, config)
    assert fixtures[0].home_score == 1
    assert fixtures[0].away_score == 3


def test_missing_result_marker_rejected(parsed):
    from bs4 import BeautifulSoup

    config, rows, _, _ = parsed
    soup = BeautifulSoup((FIXTURES / "fixtures.html").read_text(), "html.parser")
    card = next(
        c for c in soup.select('[data-testid="rencontre"]') if "Championnat" in c.get_text()
    )
    card.append(BeautifulSoup('<span data-testid="rencontre-score">2 – 1</span>', "html.parser"))
    with pytest.raises(ValueError, match="marker"):
        parse_fixtures(str(card), rows, config)


def test_matchdays_follow_source_dates(parsed):
    _, _, fixtures, _ = parsed
    league = {f.matchday: f for f in fixtures if f.competition_kind == "league"}
    assert set(league) == set(range(1, 27))
    assert league[2].kickoff < league[7].kickoff < league[3].kickoff < league[6].kickoff


def test_address_cleanup():
    from etl.parse_fixtures import clean_address

    assert (
        clean_address(
            "Stade Jules Noel 3 avenue Maurice d'Ocagne 75014 Paris, 75014, Paris",
            "Stade Jules Noel",
        )
        == "3 avenue Maurice d'Ocagne 75014 Paris"
    )
    assert (
        clean_address("Stade Parking, 94000 Créteil, 94000, Créteil", "Stade")
        == "Parking, 94000 Créteil"
    )
    assert clean_address("10 rue de Paris, 75019, Paris", "") == "10 rue de Paris, 75019, Paris"


@pytest.mark.parametrize(
    "url",
    [
        "https://youtu.be/FQheFBefpgI?si=tracking",
        "https://www.youtube.com/watch?v=FQheFBefpgI",
        "https://www.youtube.com/shorts/FQheFBefpgI",
        "https://m.youtube.com/live/FQheFBefpgI?feature=share",
    ],
)
def test_youtube_url_normalization(url):
    from app.highlights import canonical_url, embed_url

    assert canonical_url(url) == "https://www.youtube.com/watch?v=FQheFBefpgI"
    assert (
        embed_url(url) == "https://www.youtube-nocookie.com/embed/FQheFBefpgI?playsinline=1&rel=0"
    )


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "https://youtube.com.evil.test/watch?v=FQheFBefpgI",
        "https://youtu.be/invalid",
    ],
)
def test_unsafe_highlight_url_rejected(url):
    from app.highlights import canonical_url, embed_url

    with pytest.raises(ValueError):
        canonical_url(url)
    assert embed_url(url) is None


def test_highlight_survives_etl(engine, parsed):
    from app.models import MatchVideo
    from app.services import match_detail

    config, rows, fixtures, _ = parsed
    load(engine, config, rows, fixtures)
    with Session(engine) as db:
        match_id = db.scalar(select(Match.id).where(Match.status == "final"))
        video = MatchVideo(
            match_id=match_id,
            video_url="https://www.youtube.com/watch?v=FQheFBefpgI",
            status="ready",
        )
        db.add(video)
        db.commit()
        video_id = video.id
    try:
        load(engine, config, rows, fixtures)
        with Session(engine) as db:
            detail = match_detail(db, match_id)
            assert any(
                v["id"] == video_id and "FQheFBefpgI" in v["embed_url"] for v in detail["videos"]
            )
            assert db.get(MatchVideo, video_id).match_id == match_id
    finally:
        with Session(engine) as db:
            db.delete(db.get(MatchVideo, video_id))
            db.commit()
