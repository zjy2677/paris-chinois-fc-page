from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ..auth.dependencies import DB, no_store, require_role, trusted_origin
from ..models import User
from . import service
from .limiter import throttle_rating_write
from .schemas import MyRating, PlayerRatingDetail, PlayerRatingSummary, RatingInput

router = APIRouter(prefix="/api/matches/{match_id}", tags=["Match player ratings"])
member = Annotated[User, Depends(require_role("player", "admin"))]
read_member = [Depends(no_store)]
write_member = [Depends(no_store), Depends(trusted_origin), Depends(throttle_rating_write)]


@router.get("/ratings", response_model=list[PlayerRatingSummary])
def list_ratings(match_id: UUID, db: DB):
    return service.summaries(db, match_id)


@router.get("/players/{player_id}/ratings", response_model=PlayerRatingDetail)
def player_ratings(match_id: UUID, player_id: UUID, db: DB):
    return service.detail(db, match_id, player_id)


@router.get(
    "/players/{player_id}/rating/mine", response_model=MyRating | None, dependencies=read_member
)
def my_rating(match_id: UUID, player_id: UUID, db: DB, user: member):
    return service.mine(db, match_id, player_id, user)


@router.put("/players/{player_id}/rating", status_code=204, dependencies=write_member)
def save_rating(match_id: UUID, player_id: UUID, body: RatingInput, db: DB, user: member):
    service.save(db, match_id, player_id, user, body)


@router.delete("/players/{player_id}/rating", status_code=204, dependencies=write_member)
def delete_rating(match_id: UUID, player_id: UUID, db: DB, user: member):
    service.delete(db, match_id, player_id, user)
