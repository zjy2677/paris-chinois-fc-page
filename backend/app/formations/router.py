from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth.dependencies import DB, current_user, no_store, require_role, throttle, trusted_origin
from . import service
from .schemas import FormationInput, FormationResponse

router = APIRouter(
    prefix="/api/formations", tags=["Match formations"], dependencies=[Depends(no_store)]
)


@router.get("/{match_id}", response_model=FormationResponse)
def get_formation(match_id: UUID, request: Request, db: DB):
    try:
        match = service.get_match(db, match_id)
        if match.status != "final":
            user = current_user(request, db)
            if user.role not in ("player", "admin"):
                raise HTTPException(403, "Insufficient permissions")
        return service.board(db, match)
    except HTTPException as error:
        error.headers = {**(error.headers or {}), "Cache-Control": "no-store"}
        raise


@router.put(
    "/{match_id}",
    response_model=FormationResponse,
    dependencies=[
        Depends(require_role("player", "admin")),
        Depends(trusted_origin),
        Depends(throttle),
    ],
)
def save_formation(match_id: UUID, body: FormationInput, db: DB):
    match = service.get_match(db, match_id, lock=True)
    return service.save(db, match, body)
