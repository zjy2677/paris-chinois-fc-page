from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request

from ..auth.dependencies import DB, current_user, no_store, require_role, throttle, trusted_origin
from ..auth.service import COOKIE_NAME
from ..models import User
from . import service
from .schemas import FormationInput, FormationResponse

router = APIRouter(
    prefix="/api/formations", tags=["Match formations"], dependencies=[Depends(no_store)]
)


@router.get("/{match_id}", response_model=FormationResponse)
def get_formation(match_id: UUID, request: Request, db: DB):
    try:
        match = service.get_match(db, match_id)
        can_edit_final = False
        if match.status != "final":
            user = current_user(request, db)
            if user.role not in ("player", "admin"):
                raise HTTPException(403, "Insufficient permissions")
        elif request.cookies.get(COOKIE_NAME):
            try:
                can_edit_final = current_user(request, db).role == "admin"
            except HTTPException as error:
                if error.status_code != 401:
                    raise
        return service.board(db, match, can_edit_final=can_edit_final)
    except HTTPException as error:
        error.headers = {**(error.headers or {}), "Cache-Control": "no-store"}
        raise


@router.put(
    "/{match_id}",
    response_model=FormationResponse,
    dependencies=[
        Depends(trusted_origin),
        Depends(throttle),
    ],
)
def save_formation(
    match_id: UUID,
    body: FormationInput,
    db: DB,
    user: Annotated[User, Depends(require_role("player", "admin"))],
):
    match = service.get_match(db, match_id, lock=True)
    return service.save(db, match, body, can_edit_final=user.role == "admin")
