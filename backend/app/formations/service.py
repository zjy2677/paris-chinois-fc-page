from collections import Counter
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.orm import Session

from ..models import (
    CompetitionSeason,
    FormationPlacement,
    Match,
    Player,
    PlayerPhoto,
    SquadMembership,
)
from ..players.service import goal_records
from .schemas import BoardPlayer, FormationInput, FormationResponse, Placement


def get_match(db: Session, match_id: UUID, lock: bool = False) -> Match:
    query = select(Match).where(Match.id == match_id)
    if lock:
        query = query.with_for_update()
    match = db.scalar(query)
    if match is None:
        raise HTTPException(404, "Match not found")
    return match


def roster(db: Session, match: Match):
    season = db.get(CompetitionSeason, match.competition_season_id)
    saved = select(FormationPlacement.player_id).where(FormationPlacement.match_id == match.id)
    selected = Player.id.in_(saved)
    eligible = and_(Player.active.is_(True), SquadMembership.id.is_not(None))
    has_photo = select(PlayerPhoto.player_id).where(PlayerPhoto.player_id == Player.id).exists()
    return db.execute(
        select(Player, SquadMembership, has_photo)
        .outerjoin(
            SquadMembership,
            and_(
                SquadMembership.player_id == Player.id,
                SquadMembership.season_label == season.season_label,
            ),
        )
        .where(selected if match.status == "final" else or_(selected, eligible))
        .order_by(Player.display_name, Player.id)
    ).all()


def board(db: Session, match: Match) -> FormationResponse:
    records = goal_records()
    goals, assists = Counter(), Counter()
    for scorer, assistant in db.execute(
        select(records.c.scorer_id, records.c.assist_player_id).where(
            records.c.match_id == match.id
        )
    ):
        if scorer:
            goals[scorer] += 1
        if assistant:
            assists[assistant] += 1
    players = [
        BoardPlayer(
            id=player.id,
            display_name=player.display_name,
            chinese_name=player.chinese_name,
            photo_url=player.photo_url,
            has_uploaded_photo=has_photo,
            shirt_number=squad.shirt_number if squad else None,
            description=player.description,
            position=squad.position if squad else None,
            goals=goals[player.id],
            assists=assists[player.id],
        )
        for player, squad, has_photo in roster(db, match)
    ]
    return FormationResponse(
        match_id=match.id,
        status=match.status,
        kickoff_at=match.kickoff_at,
        editable=match.status not in ("final", "cancelled"),
        players=players,
        placements=[
            Placement.model_validate(row)
            for row in db.scalars(
                select(FormationPlacement)
                .where(FormationPlacement.match_id == match.id)
                .order_by(FormationPlacement.player_id)
            )
        ],
    )


def save(db: Session, match: Match, body: FormationInput) -> FormationResponse:
    if match.status in ("final", "cancelled"):
        raise HTTPException(409, "This match formation is read-only")
    eligible = {player.id for player, _, _ in roster(db, match)}
    if any(item.player_id not in eligible for item in body.placements):
        raise HTTPException(422, "Player is not eligible for this match season")
    # The caller locks the match row, serializing full replacements and status changes.
    db.execute(delete(FormationPlacement).where(FormationPlacement.match_id == match.id))
    db.add_all(
        [FormationPlacement(match_id=match.id, **item.model_dump()) for item in body.placements]
    )
    db.flush()
    result = board(db, match)
    db.commit()
    return result
