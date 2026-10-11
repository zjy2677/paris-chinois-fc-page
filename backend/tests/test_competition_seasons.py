from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database import get_db
from app.models import CompetitionSeason


def test_competition_seasons_exposes_persisted_league_and_cup_labels(monkeypatch):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    CompetitionSeason.__table__.create(engine)
    with Session(engine) as db:
        db.add_all(
            [
                CompetitionSeason(
                    fla_championship_id=14,
                    fla_cup_id=None,
                    fla_season_id=2,
                    competition_name="FLA",
                    division="Elite",
                    season_label="2026/2027",
                ),
                CompetitionSeason(
                    fla_championship_id=None,
                    fla_cup_id=1,
                    fla_season_id=2,
                    competition_name="Cup",
                    division="Cup",
                    season_label="2026/2027",
                ),
                CompetitionSeason(
                    fla_championship_id=14,
                    fla_cup_id=None,
                    fla_season_id=1,
                    competition_name="FLA",
                    division="Elite",
                    season_label="2025/2026",
                ),
            ]
        )
        db.commit()

    def test_db():
        with Session(engine) as db:
            yield db

    monkeypatch.setenv("DATABASE_URL", str(engine.url))
    get_settings.cache_clear()
    from app.main import app

    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as client:
            response = client.get("/api/competition-seasons")
        assert response.status_code == 200
        rows = response.json()
        assert [row["season_label"] for row in rows] == [
            "2026/2027",
            "2026/2027",
            "2025/2026",
        ]
        assert {row["competition_kind"] for row in rows[:2]} == {"league", "cup"}
        assert all(set(row) == {"id", "season_label", "competition_kind"} for row in rows)
    finally:
        app.dependency_overrides.pop(get_db, None)
        get_settings.cache_clear()
        engine.dispose()
