import hashlib
import secrets
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from . import services
from .auth.dependencies import throttle, trusted_origin
from .config import get_settings
from .database import get_db
from .models import ContactMessage, HomepageLike
from .schemas import (
    ContactRequest,
    HomepageLikeResponse,
    MatchDetail,
    MatchPage,
    PlayerResponse,
    StandingsResponse,
)

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
LIKE_COOKIE_NAME = "pcfc_visitor"
LIKE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365
like_mutation = [Depends(trusted_origin), Depends(throttle)]


def visitor_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def like_count(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(HomepageLike)) or 0


def set_visitor_cookie(response: Response, token: str):
    response.set_cookie(
        LIKE_COOKIE_NAME,
        token,
        httponly=True,
        secure=get_settings().auth_cookie_secure,
        samesite="lax",
        path="/api/likes",
        max_age=LIKE_COOKIE_MAX_AGE,
    )


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


@router.get("/likes", response_model=HomepageLikeResponse)
def homepage_like_status(request: Request, db: DB):
    token = request.cookies.get(LIKE_COOKIE_NAME)
    fingerprint = visitor_hash(token) if token else None
    liked = bool(
        fingerprint
        and db.scalar(select(HomepageLike.id).where(HomepageLike.visitor_hash == fingerprint))
    )
    return HomepageLikeResponse(count=like_count(db), liked=liked)


@router.post(
    "/likes", response_model=HomepageLikeResponse, status_code=201, dependencies=like_mutation
)
def like_homepage(request: Request, response: Response, db: DB):
    token = request.cookies.get(LIKE_COOKIE_NAME)
    if not token:
        token = secrets.token_urlsafe(32)
        set_visitor_cookie(response, token)
    fingerprint = visitor_hash(token)
    try:
        db.add(HomepageLike(visitor_hash=fingerprint))
        db.commit()
    except IntegrityError:
        db.rollback()
    return HomepageLikeResponse(count=like_count(db), liked=True)


@router.delete("/likes", response_model=HomepageLikeResponse, dependencies=like_mutation)
def unlike_homepage(request: Request, db: DB):
    token = request.cookies.get(LIKE_COOKIE_NAME)
    fingerprint = visitor_hash(token) if token else None
    if fingerprint:
        db.execute(delete(HomepageLike).where(HomepageLike.visitor_hash == fingerprint))
        db.commit()
    return HomepageLikeResponse(count=like_count(db), liked=False)


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
