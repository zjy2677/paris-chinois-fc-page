from uuid import UUID

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Player, SquadMembership
from ..schemas import PlayerResponse
from .schemas import PlayerCreate, PlayerInput, PlayerUpdate


def response(player: Player, squad: SquadMembership) -> PlayerResponse:
    return PlayerResponse(
        id=player.id,
        display_name=player.display_name,
        photo_url=player.photo_url,
        active=player.active,
        season=squad.season_label,
        shirt_number=squad.shirt_number,
        position=squad.position,
    )


def commit(db: Session):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Shirt number is already assigned in this season, including inactive players"
        ) from None


def create(db: Session, body: PlayerCreate):
    player = Player(
        display_name=body.display_name,
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
    )
    db.add(squad)
    commit(db)
    return response(player, squad)


def update(db: Session, player_id: UUID, season: str, body: PlayerUpdate):
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
        "display_name": player.display_name,
        "photo_url": player.photo_url,
        "active": player.active,
        "shirt_number": squad.shirt_number,
        "position": squad.position,
    }

    try:
        validated = PlayerInput.model_validate(values | changes)
    except ValidationError:
        raise HTTPException(422, "Invalid player details or photo URL") from None
    player.display_name, player.active = validated.display_name, validated.active
    player.photo_url = str(validated.photo_url) if validated.photo_url else None
    squad.shirt_number, squad.position = validated.shirt_number, validated.position
    commit(db)
    return response(player, squad)


def deactivate(db: Session, player_id: UUID):
    player = db.get(Player, player_id, with_for_update=True)
    if player is None:
        raise HTTPException(404, "Player not found")
    player.active = False
    db.commit()
