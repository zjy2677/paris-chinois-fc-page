from uuid import UUID

from fastapi import APIRouter, Depends, Query

from .. import services
from ..auth.dependencies import DB, no_store, require_role, throttle, trusted_origin
from ..schemas import PlayerResponse
from . import service
from .schemas import PlayerCreate, PlayerProfileResponse, PlayerUpdate

router = APIRouter(prefix="/api", tags=["Player management"])
admin = [Depends(require_role("admin")), Depends(no_store)]
mutation = [*admin, Depends(trusted_origin), Depends(throttle)]


@router.get("/players/{player_id}", response_model=PlayerProfileResponse)
def player_profile(player_id: UUID, db: DB):
    return service.profile(db, player_id)


@router.get("/admin/players", response_model=list[PlayerResponse], dependencies=admin)
def admin_players(db: DB, season: str = Query("2026/2027", pattern=r"^\d{4}/\d{4}$")):
    """Return the season squad, including inactive players, for an authorized admin."""
    return services.players(db, season, include_inactive=True)


@router.post("/players", response_model=PlayerResponse, status_code=201, dependencies=mutation)
def create_player(body: PlayerCreate, db: DB):
    """Create a player and season membership after the admin mutation checks pass."""
    return service.create(db, body)


@router.patch("/players/{player_id}", response_model=PlayerResponse, dependencies=mutation)
def update_player(
    player_id: UUID, body: PlayerUpdate, db: DB, season: str = Query(..., pattern=r"^\d{4}/\d{4}$")
):
    """Update player and season details after the admin mutation checks pass."""
    return service.update(db, player_id, season, body)


@router.delete("/players/{player_id}", status_code=204, dependencies=mutation)
def deactivate_player(player_id: UUID, db: DB):
    """Deactivate a player across seasons after the admin mutation checks pass."""
    service.deactivate(db, player_id)
