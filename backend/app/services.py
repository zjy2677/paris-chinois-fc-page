from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, aliased

from .goals.service import list_goals
from .highlights import embed_url
from .models import (
    CompetitionSeason,
    Match,
    MatchEvent,
    MatchReport,
    MatchVideo,
    Player,
    SquadMembership,
    StandingsRow,
    StandingsSnapshot,
    SyncRun,
    Team,
    Venue,
)
from .schemas import (
    MatchResponse,
    PlayerResponse,
    StandingResponse,
    StandingsResponse,
    TeamResponse,
    VenueResponse,
)


def match_query():
    home, away = aliased(Team), aliased(Team)
    return (
        select(Match, home, away, Venue, CompetitionSeason)
        .join(CompetitionSeason, Match.competition_season_id == CompetitionSeason.id)
        .join(home, Match.home_team_id == home.id)
        .join(away, Match.away_team_id == away.id)
        .outerjoin(Venue, Match.venue_id == Venue.id)
    )


def serialize_match(row):
    match, home, away, venue, competition = row
    return MatchResponse(
        **{
            key: getattr(match, key)
            for key in MatchResponse.model_fields
            if key
            not in {"home_team", "away_team", "venue", "competition_name", "competition_kind"}
        },
        competition_name=competition.competition_name,
        competition_kind=(
            "cup"
            if competition.fla_cup_id is not None
            else "custom"
            if match.source_type == "manual"
            else "league"
        ),
        home_team=TeamResponse.model_validate(home),
        away_team=TeamResponse.model_validate(away),
        venue=VenueResponse.model_validate(venue) if venue else None,
    )


def list_matches(
    db: Session,
    team_id: UUID | None,
    competition_season_id: UUID | None,
    status: str | None,
    offset: int,
    limit: int,
):
    conditions = []
    if team_id:
        conditions.append(or_(Match.home_team_id == team_id, Match.away_team_id == team_id))
    if competition_season_id:
        conditions.append(Match.competition_season_id == competition_season_id)
    if status:
        conditions.append(Match.status == status)
    total = db.scalar(select(func.count()).select_from(Match).where(*conditions))
    rows = db.execute(
        match_query()
        .where(*conditions)
        .order_by(Match.kickoff_at.asc().nulls_last(), Match.id)
        .offset(offset)
        .limit(limit)
    )
    return {
        "items": [serialize_match(row) for row in rows],
        "total": total,
        "offset": offset,
        "limit": limit,
    }


def match_detail(db: Session, match_id: UUID):
    """Return match details with recorded goals and ready videos, or None if absent."""
    row = db.execute(match_query().where(Match.id == match_id)).first()
    if row is None:
        return None
    videos = db.scalars(
        select(MatchVideo)
        .where(MatchVideo.match_id == match_id, MatchVideo.status == "ready")
        .order_by(MatchVideo.created_at, MatchVideo.id)
    ).all()
    report = db.scalar(select(MatchReport).where(MatchReport.match_id == match_id))
    scorer, assistant = aliased(Player), aliased(Player)
    events = db.execute(
        select(MatchEvent, scorer, assistant)
        .outerjoin(scorer, MatchEvent.player_id == scorer.id)
        .outerjoin(assistant, MatchEvent.assist_player_id == assistant.id)
        .where(MatchEvent.match_id == match_id)
        .order_by(MatchEvent.sequence, MatchEvent.id)
    ).all()
    return {
        **serialize_match(row).model_dump(),
        "goals": list_goals(db, match_id),
        "videos": [
            {
                "id": video.id,
                "title": video.title,
                "published_at": video.published_at,
                "embed_url": embed_url(video.video_url),
            }
            for video in videos
        ],
        "description": report.description if report else None,
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "player_id": event.player_id,
                "player_name": player.display_name if player else None,
                "assist_player_id": event.assist_player_id,
                "assist_player_name": assist.display_name if assist else None,
                "minute": event.minute,
                "sequence": event.sequence,
            }
            for event, player, assist in events
        ],
    }


def standings(db: Session, competition_season_id: UUID | None):
    query = select(StandingsSnapshot)
    if competition_season_id:
        query = query.where(StandingsSnapshot.competition_season_id == competition_season_id)
    snapshot = db.scalar(
        query.order_by(StandingsSnapshot.fetched_at.desc(), StandingsSnapshot.id).limit(1)
    )
    if snapshot is None:
        return StandingsResponse(
            competition_season_id=competition_season_id,
            source_url=None,
            fetched_at=None,
            last_successful_sync=None,
            rows=[],
        )
    last_sync = db.scalar(
        select(func.max(SyncRun.finished_at)).where(
            SyncRun.status == "success", SyncRun.source_url == snapshot.source_url
        )
    )
    rows = db.execute(
        select(StandingsRow, Team)
        .join(Team)
        .where(StandingsRow.snapshot_id == snapshot.id)
        .order_by(StandingsRow.position)
    )
    return StandingsResponse(
        competition_season_id=snapshot.competition_season_id,
        source_url=snapshot.source_url,
        fetched_at=snapshot.fetched_at,
        last_successful_sync=last_sync,
        rows=[
            StandingResponse(
                team=TeamResponse.model_validate(team),
                **{
                    key: getattr(row, key) for key in StandingResponse.model_fields if key != "team"
                },
            )
            for row, team in rows
        ],
    )


def players(db: Session, season: str, include_inactive: bool = False):
    """Return the season squad ordered by position and shirt number, active only by default."""
    rows = db.execute(
        select(Player, SquadMembership)
        .join(SquadMembership)
        .where(SquadMembership.season_label == season)
        .where(True if include_inactive else Player.active.is_(True))
        .order_by(SquadMembership.position, SquadMembership.shirt_number, Player.id)
    )
    return [
        PlayerResponse(
            description=p.description,
            id=p.id,
            display_name=p.display_name,
            active=p.active,
            photo_url=p.photo_url,
            season=s.season_label,
            shirt_number=s.shirt_number,
            position=s.position,
        )
        for p, s in rows
    ]
