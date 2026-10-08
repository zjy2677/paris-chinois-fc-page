from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from .. import services
from ..auth.dependencies import DB, no_store, require_role, throttle, trusted_origin
from ..models import Player, PlayerPhoto
from ..photo_storage import photo_transaction
from ..profile import MAX_AVATAR_BYTES, avatar_type
from ..schemas import PlayerResponse
from ..storage import StorageUnavailable, get_storage
from . import service
from .schemas import PlayerCreate, PlayerLeaderboardsResponse, PlayerProfileResponse, PlayerUpdate

router = APIRouter(prefix="/api", tags=["Player management"])
admin = [Depends(require_role("admin")), Depends(no_store)]
mutation = [*admin, Depends(trusted_origin), Depends(throttle)]


@router.get("/player-leaderboards", response_model=PlayerLeaderboardsResponse)
def player_leaderboards(db: DB, season: str = Query("2026/2027", pattern=r"^\d{4}/\d{4}$")):
    """Return this season's club scoring and assist leaders from recorded match events."""
    return service.leaderboards(db, season)


@router.get("/players/{player_id}", response_model=PlayerProfileResponse)
def player_profile(player_id: UUID, db: DB):
    return service.profile(db, player_id)


@router.get("/players/{player_id}/photo")
def player_photo(player_id: UUID, db: DB):
    photo = db.get(PlayerPhoto, player_id)
    if photo is None:
        raise HTTPException(404, "Player photo not found")
    try:
        data = get_storage().get(photo.storage_key) if photo.storage_key else photo.data
    except StorageUnavailable as error:
        raise HTTPException(503, "Media storage is unavailable") from error
    if data is None:
        raise HTTPException(404, "Player photo content is unavailable")
    return Response(
        content=data,
        media_type=photo.content_type,
        headers={"Cache-Control": "no-cache"},
    )


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


@router.put("/players/{player_id}/photo", status_code=204, dependencies=mutation)
async def upload_player_photo(player_id: UUID, request: Request, db: DB):
    declared_size = request.headers.get("content-length")
    if declared_size:
        try:
            if int(declared_size) > MAX_AVATAR_BYTES:
                raise HTTPException(413, "Player photo is too large")
        except ValueError as error:
            raise HTTPException(400, "Invalid content length") from error
    buffer = bytearray()
    async for chunk in request.stream():
        if len(buffer) + len(chunk) > MAX_AVATAR_BYTES:
            raise HTTPException(413, "Player photo is too large")
        buffer.extend(chunk)
    data = bytes(buffer)
    if not data:
        raise HTTPException(400, "Player photo is required")
    content_type = avatar_type(request.headers.get("content-type", ""), data)
    await run_in_threadpool(save_player_photo, db, player_id, content_type, data)


def save_player_photo(db, player_id, content_type, data):
    player = db.get(Player, player_id, with_for_update=True)
    if player is None:
        raise HTTPException(404, "Player not found")
    photo = db.scalar(select(PlayerPhoto).where(PlayerPhoto.player_id == player_id))
    with photo_transaction(db) as write:
        storage_key = write.put(f"players/{player_id}", data, content_type)
        if photo is None:
            db.add(
                PlayerPhoto(
                    player_id=player_id,
                    content_type=content_type,
                    data=None if storage_key else data,
                    storage_key=storage_key,
                )
            )
        else:
            write.retire(photo.storage_key)
            photo.content_type = content_type
            photo.data = None if storage_key else data
            photo.storage_key = storage_key
        player.photo_url = None


@router.delete("/players/{player_id}", status_code=204, dependencies=mutation)
def deactivate_player(player_id: UUID, db: DB):
    """Deactivate a player across seasons after the admin mutation checks pass."""
    service.deactivate(db, player_id)
