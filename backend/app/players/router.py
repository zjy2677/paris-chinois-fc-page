from uuid import UUID

from fastapi import APIRouter, Depends, Query

from .. import services
from ..auth.dependencies import DB, no_store, require_role, throttle, trusted_origin
from ..schemas import PlayerResponse
from . import service
from .schemas import PlayerCreate, PlayerUpdate

router = APIRouter(prefix="/api", tags=["Player management"])
admin = [Depends(require_role("admin")), Depends(no_store)]
mutation = [*admin, Depends(trusted_origin), Depends(throttle)]


@router.get("/admin/players", response_model=list[PlayerResponse], dependencies=admin)
def admin_players(db: DB, season: str = Query("2026/2027", pattern=r"^\d{4}/\d{4}$")):
    return services.players(db, season, include_inactive=True)


@router.post("/players", response_model=PlayerResponse, status_code=201, dependencies=mutation)
def create_player(body: PlayerCreate, db: DB):
    return service.create(db, body)


@router.patch("/players/{player_id}", response_model=PlayerResponse, dependencies=mutation)
def update_player(
    player_id: UUID, body: PlayerUpdate, db: DB, season: str = Query(..., pattern=r"^\d{4}/\d{4}$")
):
    return service.update(db, player_id, season, body)


@router.delete("/players/{player_id}", status_code=204, dependencies=mutation)
def deactivate_player(player_id: UUID, db: DB):
    service.deactivate(db, player_id)
