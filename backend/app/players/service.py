from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import and_, func, select, union_all
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import (
    CompetitionSeason,
    Match,
    MatchEvent,
    MatchGoal,
    Player,
    PlayerPhoto,
    SquadMembership,
)
from ..schemas import PlayerResponse
from .schemas import (
    LeaderboardEntry,
    PlayerCreate,
    PlayerInput,
    PlayerLeaderboardsResponse,
    PlayerProfileResponse,
    PlayerUpdate,
    SquadSeasonResponse,
)


def goal_records():
    """Combine match-editor events with legacy goals without counting a match twice."""
    match_has_events = (
        select(MatchEvent.id)
        .where(MatchEvent.match_id == MatchGoal.match_id, MatchEvent.event_type == "goal")
        .exists()
    )
    return union_all(
        select(
            MatchEvent.match_id.label("match_id"),
            MatchEvent.player_id.label("scorer_id"),
            MatchEvent.assist_player_id.label("assist_player_id"),
        ).where(MatchEvent.event_type == "goal"),
        select(
            MatchGoal.match_id.label("match_id"),
            MatchGoal.scorer_id.label("scorer_id"),
            MatchGoal.assist_player_id.label("assist_player_id"),
        ).where(MatchGoal.goal_type != "own_goal", ~match_has_events),
    ).subquery()


def leaderboard_entries(db: Session, season: str, records, player_field) -> list[LeaderboardEntry]:
    """Aggregate one ranked list from the club events entered in the match editor."""
    total = func.count().label("total")
    rows = db.execute(
        select(Player, SquadMembership.shirt_number, total)
        .join(records, player_field == Player.id)
        .join(Match, Match.id == records.c.match_id)
        .join(CompetitionSeason, CompetitionSeason.id == Match.competition_season_id)
        .outerjoin(
            SquadMembership,
            and_(
                SquadMembership.player_id == Player.id,
                SquadMembership.season_label == season,
            ),
        )
        .where(CompetitionSeason.season_label == season)
        .group_by(Player.id, SquadMembership.shirt_number)
        .order_by(total.desc(), Player.display_name, Player.id)
    ).all()
    rank = 0
    previous_total = None
    entries = []
    for position, (player, shirt_number, count) in enumerate(rows, start=1):
        if count != previous_total:
            rank = position
            previous_total = count
        entries.append(
            LeaderboardEntry(
                rank=rank,
                player_id=player.id,
                display_name=player.display_name,
                chinese_name=player.chinese_name,
                photo_url=player.photo_url,
                has_uploaded_photo=db.get(PlayerPhoto, player.id) is not None,
                shirt_number=shirt_number,
                total=count,
            )
        )
    return entries


def leaderboards(db: Session, season: str) -> PlayerLeaderboardsResponse:
    records = goal_records()
    return PlayerLeaderboardsResponse(
        season=season,
        scorers=leaderboard_entries(db, season, records, records.c.scorer_id),
        assists=leaderboard_entries(db, season, records, records.c.assist_player_id),
    )


def response(
    player: Player, squad: SquadMembership, has_uploaded_photo: bool = False
) -> PlayerResponse:
    """Combine permanent player details and season membership into an API response."""
    return PlayerResponse(
        description=player.description,
        id=player.id,
        display_name=player.display_name,
        chinese_name=player.chinese_name,
        photo_url=player.photo_url,
        has_uploaded_photo=has_uploaded_photo,
        active=player.active,
        season=squad.season_label,
        shirt_number=squad.shirt_number,
        position=squad.position,
        alternate_positions=squad.alternate_positions or [],
    )


def commit(db: Session):
    """Commit pending changes, rolling back integrity failures as HTTP 409 shirt conflicts."""
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Shirt number is already assigned in this season, including inactive players"
        ) from None


def create(db: Session, body: PlayerCreate):
    """Persist a player and their season membership, then return the combined response."""
    player = Player(
        description=body.description,
        display_name=body.display_name,
        chinese_name=body.chinese_name,
        photo_url=str(body.photo_url) if body.photo_url else None,
        active=body.active,
    )
    db.add(player)
    db.flush()
    squad = SquadMembership(
        player_id=player.id,
        season_label=body.season,
        shirt_number=body.shirt_number,
        position=body.position,
        alternate_positions=body.alternate_positions,
    )
    db.add(squad)
    commit(db)
    return response(player, squad)


def update(db: Session, player_id: UUID, season: str, body: PlayerUpdate):
    """Lock player and season records, validate merged fields, and commit their updates."""
    player = db.get(Player, player_id, with_for_update=True)
    if player is None:
        raise HTTPException(404, "Player not found")
    squad = db.scalar(
        select(SquadMembership)
        .where(SquadMembership.player_id == player_id, SquadMembership.season_label == season)
        .with_for_update()
    )
    if squad is None:
        raise HTTPException(404, "Player is not in this season's squad")
    changes = body.model_dump(exclude_unset=True)
    values = {
        "description": player.description,
        "display_name": player.display_name,
        "chinese_name": player.chinese_name,
        "photo_url": player.photo_url,
        "active": player.active,
        "shirt_number": squad.shirt_number,
        "position": squad.position,
        "alternate_positions": squad.alternate_positions or [],
    }

    try:
        validated = PlayerInput.model_validate(values | changes)
    except ValidationError:
        raise HTTPException(422, "Invalid player details or photo URL") from None
    player.display_name, player.active = validated.display_name, validated.active
    player.chinese_name = validated.chinese_name
    player.photo_url = str(validated.photo_url) if validated.photo_url else None
    if "photo_url" in changes:
        uploaded = db.get(PlayerPhoto, player_id)
        if uploaded is not None:
            db.delete(uploaded)
    player.description = validated.description
    squad.shirt_number, squad.position = validated.shirt_number, validated.position
    squad.alternate_positions = validated.alternate_positions
    commit(db)
    return response(player, squad, db.get(PlayerPhoto, player_id) is not None)


def deactivate(db: Session, player_id: UUID):
    """Mark an existing player inactive while preserving memberships and goal history."""
    player = db.get(Player, player_id, with_for_update=True)
    if player is None:
        raise HTTPException(404, "Player not found")
    player.active = False
    db.commit()


def profile(db: Session, player_id: UUID) -> PlayerProfileResponse:
    player = db.get(Player, player_id)
    if player is None:
        raise HTTPException(404, "Player not found")
    squads = db.scalars(
        select(SquadMembership)
        .where(SquadMembership.player_id == player_id)
        .order_by(SquadMembership.season_label.desc())
    )
    # Match events take precedence, with legacy goal rows retained for unconverted matches.
    records = goal_records()
    goals = db.scalar(
        select(func.count()).select_from(records).where(records.c.scorer_id == player_id)
    )
    assists = db.scalar(
        select(func.count()).select_from(records).where(records.c.assist_player_id == player_id)
    )
    return PlayerProfileResponse(
        id=player.id,
        display_name=player.display_name,
        chinese_name=player.chinese_name,
        photo_url=player.photo_url,
        has_uploaded_photo=db.get(PlayerPhoto, player_id) is not None,
        description=player.description,
        active=player.active,
        squads=[
            SquadSeasonResponse(
                season=s.season_label,
                position=s.position,
                alternate_positions=s.alternate_positions or [],
                shirt_number=s.shirt_number,
            )
            for s in squads
        ],
        goals=goals or 0,
        assists=assists or 0,
    )
