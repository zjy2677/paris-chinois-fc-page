"""Player attribute persistence, independent of season memberships."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Player, PlayerAttribute
from .schemas import AttributeInput


def require_player(db: Session, player_id: UUID):
    if db.get(Player, player_id) is None:
        raise HTTPException(404, "Player not found")


def list_attributes(db: Session, player_id: UUID):
    require_player(db, player_id)
    return db.scalars(
        select(PlayerAttribute)
        .where(PlayerAttribute.player_id == player_id)
        .order_by(PlayerAttribute.created_at, PlayerAttribute.id)
    ).all()


def create(db: Session, player_id: UUID, body: AttributeInput):
    require_player(db, player_id)
    attribute = PlayerAttribute(player_id=player_id, **body.model_dump())
    db.add(attribute)
    db.commit()
    db.refresh(attribute)
    return attribute


def get_attribute(db: Session, player_id: UUID, attribute_id: UUID):
    attribute = db.scalar(
        select(PlayerAttribute)
        .where(PlayerAttribute.id == attribute_id, PlayerAttribute.player_id == player_id)
        .with_for_update()
    )
    if attribute is None:
        raise HTTPException(404, "Player attribute not found")
    return attribute


def update(db: Session, player_id: UUID, attribute_id: UUID, body: AttributeInput):
    attribute = get_attribute(db, player_id, attribute_id)
    for key, value in body.model_dump().items():
        setattr(attribute, key, value)
    db.commit()
    db.refresh(attribute)
    return attribute


def delete(db: Session, player_id: UUID, attribute_id: UUID):
    db.delete(get_attribute(db, player_id, attribute_id))
    db.commit()
