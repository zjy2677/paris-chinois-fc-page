import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from . import services
from .auth.dependencies import require_role, throttle, trusted_origin
from .config import get_settings
from .database import get_db
from .models import (
    CompetitionSeason,
    ContactMessage,
    HomepageLike,
    Match,
    MatchEvent,
    MatchReport,
    Player,
    Team,
    User,
)
from .schemas import (
    ContactRequest,
    HomepageLikeResponse,
    ManualMatchCreate,
    MatchDetail,
    MatchPage,
    MatchRecordUpdate,
    PlayerResponse,
    StandingsResponse,
)

router = APIRouter(prefix="/api")
DB = Annotated[Session, Depends(get_db)]
LIKE_COOKIE_NAME = "pcfc_visitor"
LIKE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365
like_mutation = [Depends(trusted_origin), Depends(throttle)]
admin_mutation = [Depends(trusted_origin), Depends(throttle)]


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


@router.put(
    "/admin/matches/{match_id}/record",
    response_model=MatchDetail,
    dependencies=admin_mutation,
)
def update_match_record(
    match_id: UUID,
    body: MatchRecordUpdate,
    db: DB,
    user: Annotated[User, Depends(require_role("admin"))],
):
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(404, "Match not found")
    if (body.home_score is None) != (body.away_score is None):
        raise HTTPException(422, "Both scores must be supplied together")
    if match.source_type == "manual" and body.home_score is not None:
        match.home_score, match.away_score, match.status = body.home_score, body.away_score, "final"
    club = db.scalar(select(Team).where(Team.fla_team_id == 322))
    if club is None:
        raise HTTPException(409, "Club team is unavailable")
    club_score = match.home_score if match.home_team_id == club.id else match.away_score
    goal_count = sum(event.event_type == "goal" for event in body.events)
    if goal_count != (club_score or 0):
        raise HTTPException(
            422,
            f"Club goal records ({goal_count}) must equal the club score ({club_score or 0})",
        )
    if any(event.event_type != "goal" and event.player_id is None for event in body.events):
        raise HTTPException(422, "Card events require a player")
    player_ids = {event.player_id for event in body.events if event.player_id} | {
        event.assist_player_id for event in body.events if event.assist_player_id
    }
    existing = (
        set(db.scalars(select(Player.id).where(Player.id.in_(player_ids)))) if player_ids else set()
    )
    if existing != player_ids:
        raise HTTPException(422, "Every event player must exist")
    if any(event.event_type != "goal" and event.assist_player_id for event in body.events):
        raise HTTPException(422, "Only goals can have an assist")
    report = db.scalar(select(MatchReport).where(MatchReport.match_id == match_id))
    if report is None:
        report = MatchReport(match_id=match_id, updated_by=user.id)
        db.add(report)
    report.description = body.description or None
    report.updated_by = user.id
    db.execute(delete(MatchEvent).where(MatchEvent.match_id == match_id))
    db.add_all(
        MatchEvent(match_id=match_id, sequence=index, **event.model_dump())
        for index, event in enumerate(body.events)
    )
    db.commit()
    return services.match_detail(db, match_id)


@router.post(
    "/admin/matches",
    response_model=MatchDetail,
    status_code=201,
    dependencies=admin_mutation,
)
def create_manual_match(
    body: ManualMatchCreate,
    db: DB,
    user: Annotated[User, Depends(require_role("admin"))],
):
    if (body.home_score is None) != (body.away_score is None):
        raise HTTPException(422, "Both scores must be supplied together")
    club = db.scalar(select(Team).where(Team.fla_team_id == 322))
    if club is None:
        raise HTTPException(409, "Club team must be synchronized before creating matches")
    opponent = db.scalar(
        select(Team).where(Team.fla_team_id.is_(None), Team.name == body.opponent_name)
    )
    if opponent is None:
        opponent = Team(fla_team_id=None, name=body.opponent_name, short_name=None, logo_url=None)
        db.add(opponent)
        db.flush()
    competition = db.scalar(
        select(CompetitionSeason).where(
            CompetitionSeason.fla_championship_id.is_(None),
            CompetitionSeason.fla_cup_id.is_(None),
            CompetitionSeason.competition_name == body.competition_name,
            CompetitionSeason.season_label == body.season_label,
        )
    )
    if competition is None:
        competition = CompetitionSeason(
            fla_championship_id=None,
            fla_cup_id=None,
            fla_season_id=0,
            competition_name=body.competition_name,
            division="Manual",
            season_label=body.season_label,
        )
        db.add(competition)
        db.flush()
    now = datetime.now(timezone.utc)
    match = Match(
        competition_season_id=competition.id,
        source_key=f"manual:{uuid.uuid4()}",
        home_team_id=club.id if body.is_home else opponent.id,
        away_team_id=opponent.id if body.is_home else club.id,
        venue_id=None,
        matchday=None,
        leg="Friendly",
        kickoff_at=body.kickoff_at,
        status="final" if body.home_score is not None else "scheduled",
        home_score=body.home_score,
        away_score=body.away_score,
        source_url="",
        last_synced_at=now,
        source_type="manual",
    )
    db.add(match)
    db.flush()
    if body.description:
        db.add(MatchReport(match_id=match.id, description=body.description, updated_by=user.id))
    db.commit()
    return services.match_detail(db, match.id)


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
