import hashlib
import json
from datetime import datetime, timezone

from app.models import (
    CompetitionSeason,
    Match,
    StandingsRow,
    StandingsSnapshot,
    SyncRun,
    Team,
    Venue,
)
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .parse_standings import canonical_rows


def load(engine, config, rows, fixtures):
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        run = SyncRun(
            dataset="league", source_url=config.standings_url, status="running"
        )
        db.add(run)
        db.commit()
        run_id = run.id
    try:
        with Session(engine) as db, db.begin():
            locked = db.scalar(text("SELECT pg_try_advisory_xact_lock(3221402)"))
            if not locked:
                raise ValueError("Another FLA import is running")
            run = db.get(SyncRun, run_id)
            comp = db.scalar(
                select(CompetitionSeason).where(
                    CompetitionSeason.fla_championship_id == config.championship_id,
                    CompetitionSeason.fla_season_id == config.season_id,
                )
            )
            if comp is None:
                comp = CompetitionSeason(
                    fla_championship_id=config.championship_id,
                    fla_season_id=config.season_id,
                    competition_name=config.championship_name,
                    division="1ère division Elite",
                    season_label=config.season_label,
                )
                db.add(comp)
                db.flush()
            cup = db.scalar(
                select(CompetitionSeason).where(
                    CompetitionSeason.fla_cup_id == config.cup_id,
                    CompetitionSeason.fla_season_id == config.season_id,
                )
            )
            if cup is None and any(f.competition_kind == "cup" for f in fixtures):
                cup = CompetitionSeason(
                    fla_cup_id=config.cup_id,
                    fla_season_id=config.season_id,
                    competition_name=config.cup_name,
                    division="Cup",
                    season_label=config.season_label,
                )
                db.add(cup)
                db.flush()
            teams = {}
            for row in rows:
                team = db.scalar(select(Team).where(Team.fla_team_id == row.team_id))
                if team is None:
                    team = Team(fla_team_id=row.team_id, name=row.name)
                    db.add(team)
                    db.flush()
                else:
                    team.name = row.name
                teams[row.team_id] = team
            for source_id, name in config.cup_teams.items():
                team = db.scalar(select(Team).where(Team.fla_team_id == source_id))
                if team is None:
                    team = Team(fla_team_id=source_id, name=name)
                    db.add(team)
                    db.flush()
                teams[source_id] = team
            for fixture in fixtures:
                fixture_comp = cup if fixture.competition_kind == "cup" else comp
                venue_id = None
                if fixture.stadium:
                    venue = db.scalar(
                        select(Venue).where(
                            Venue.name == fixture.stadium,
                            Venue.address == fixture.address,
                        )
                    )
                    if venue is None:
                        venue = Venue(name=fixture.stadium, address=fixture.address)
                        db.add(venue)
                        db.flush()
                    venue_id = venue.id
                match = db.scalar(
                    select(Match).where(
                        Match.competition_season_id == fixture_comp.id,
                        Match.source_key == fixture.source_key,
                    )
                )
                if match is None:
                    match = Match(
                        competition_season_id=fixture_comp.id,
                        source_key=fixture.source_key,
                    )
                    db.add(match)
                    run.inserted_count += 1
                else:
                    run.updated_count += 1
                match.home_team_id, match.away_team_id = (
                    teams[fixture.home_id].id,
                    teams[fixture.away_id].id,
                )
                match.venue_id = venue_id
                match.matchday, match.leg = fixture.matchday, fixture.leg
                match.kickoff_at, match.status = fixture.kickoff, fixture.status
                match.home_score, match.away_score = (
                    fixture.home_score,
                    fixture.away_score,
                )
                match.source_url, match.last_synced_at = config.fixtures_url, now
            digest = hashlib.sha256(
                json.dumps(canonical_rows(rows), sort_keys=True).encode()
            ).hexdigest()
            latest = db.scalar(
                select(StandingsSnapshot)
                .where(StandingsSnapshot.competition_season_id == comp.id)
                .order_by(StandingsSnapshot.fetched_at.desc())
                .limit(1)
            )
            if latest is None or latest.content_hash != digest:
                snapshot = StandingsSnapshot(
                    competition_season_id=comp.id,
                    sync_run_id=run_id,
                    source_url=config.standings_url,
                    fetched_at=now,
                    content_hash=digest,
                )
                db.add(snapshot)
                db.flush()
                for row in rows:
                    values = {
                        key: value
                        for key, value in canonical_rows([row])[0].items()
                        if key not in ("team_id", "name")
                    }
                    db.add(
                        StandingsRow(
                            snapshot_id=snapshot.id,
                            team_id=teams[row.team_id].id,
                            **values,
                        )
                    )
            run.status, run.finished_at = "success", now
            db.flush()
            result = {
                "run_id": str(run_id),
                "matches": len(fixtures),
                "standings": len(rows),
                "inserted": run.inserted_count,
                "updated": run.updated_count,
            }
        return result
    except Exception as exc:
        with Session(engine) as db, db.begin():
            run = db.get(SyncRun, run_id)
            run.status, run.finished_at = "failed", datetime.now(timezone.utc)
            # Never persist SQL parameters or credentials from driver exceptions.
            run.error_summary = type(exc).__name__
        raise
