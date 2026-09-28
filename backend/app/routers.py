from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from . import services
from .config import get_settings
from .database import get_db
from .models import ContactMessage
from .schemas import ContactRequest, MatchDetail, MatchPage, PlayerResponse, StandingsResponse

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(db: DB):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(503, "Database unavailable") from None
    return {"status": "ready"}


@router.get("/matches", response_model=MatchPage)
def matches(
    db: DB,
    team_id: UUID | None = None,
    competition_season_id: UUID | None = None,
    status: Literal["scheduled", "final", "postponed", "cancelled", "unknown"] | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
):
    return services.list_matches(db, team_id, competition_season_id, status, offset, limit)


@router.get("/matches/{match_id}", response_model=MatchDetail)
def match_detail(match_id: UUID, db: DB):
    result = services.match_detail(db, match_id)
    if result is None:
        raise HTTPException(404, "Match not found")
    return result


@router.get("/standings", response_model=StandingsResponse)
def standings(db: DB, competition_season_id: UUID | None = None):
    return services.standings(db, competition_season_id)


@router.get("/players", response_model=list[PlayerResponse])
def players(db: DB, season: str = Query("2026/2027", pattern=r"^\d{4}/\d{4}$")):
    return services.players(db, season)


@router.post("/contact-messages", status_code=202)
def contact(body: ContactRequest, db: DB):
    if not get_settings().contact_enabled:
        raise HTTPException(503, "Contact submissions are not enabled yet")
    db.add(ContactMessage(**body.model_dump()))
    db.commit()
    return {"status": "received"}
