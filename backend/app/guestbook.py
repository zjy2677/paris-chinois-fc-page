import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from math import ceil
from threading import Lock
from time import monotonic
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from .auth.dependencies import DB, require_role, throttle, trusted_origin
from .config import get_settings
from .models import GuestbookMessage, MediaAsset, User

router = APIRouter(prefix="/api/guestbook", tags=["Guestbook"])
mutation = [Depends(trusted_origin), Depends(throttle)]
COOKIE_NAME = "pcfc_guestbook_visitor"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365
POST_COOLDOWN = timedelta(seconds=30)


# MVP: per-process IP cooldown for the single-worker deployment. A shared limiter
# is needed before adding workers. Trust proxy headers only from configured proxies.
_post_attempts: dict[str, float] = {}
_post_lock = Lock()


def posting_cooldown(request: Request):
    host = request.client.host if request.client else "unknown"
    now = monotonic()
    window = POST_COOLDOWN.total_seconds()
    with _post_lock:
        for key, started in list(_post_attempts.items()):
            if now - started >= window:
                del _post_attempts[key]
        previous = _post_attempts.get(host)
        if previous is not None:
            wait = max(1, ceil(window - (now - previous)))
            raise HTTPException(
                429, "Please wait before posting again", headers={"Retry-After": str(wait)}
            )
        # Fail closed at capacity rather than evicting an active cooldown.
        if len(_post_attempts) >= 4096:
            raise HTTPException(
                429, "Please wait before posting again", headers={"Retry-After": "30"}
            )
        _post_attempts[host] = now


class GuestbookInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    nickname: str = Field(min_length=1, max_length=30)
    body: str = Field(min_length=2, max_length=300)


class GuestbookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    nickname: str
    body: str
    status: Literal["visible", "hidden"]
    created_at: datetime
    photo: dict | None = None


def message_response(db: DB, message: GuestbookMessage) -> GuestbookResponse:
    photo = db.scalar(
        select(MediaAsset)
        .where(MediaAsset.guestbook_message_id == message.id)
        .order_by(MediaAsset.created_at)
    )
    visible_photo = (
        {
            "id": str(photo.id),
            "url": photo.url,
            "caption": photo.caption,
            "alt_text": photo.alt_text,
        }
        if photo is not None and photo.status == "visible"
        else None
    )
    return GuestbookResponse.model_validate(
        {
            "id": message.id,
            "nickname": message.nickname,
            "body": message.body,
            "status": message.status,
            "created_at": message.created_at,
            "photo": visible_photo,
        }
    )


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def visitor(request: Request, response: Response) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if token:
        return token_hash(token)
    token = secrets.token_urlsafe(32)
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=get_settings().auth_cookie_secure,
        samesite="lax",
        path="/api/guestbook",
        max_age=COOKIE_MAX_AGE,
    )
    return token_hash(token)


@router.get("/messages", response_model=list[GuestbookResponse])
def visible_messages(db: DB):
    rows = list(
        db.scalars(
            select(GuestbookMessage)
            .where(GuestbookMessage.status == "visible")
            .order_by(GuestbookMessage.created_at.desc())
            .limit(60)
        ).all()
    )
    return [message_response(db, message) for message in rows]


@router.post("/messages", response_model=GuestbookResponse, status_code=201, dependencies=mutation)
def create_message(body: GuestbookInput, request: Request, response: Response, db: DB):
    posting_cooldown(request)
    fingerprint = visitor(request, response)
    last_created = db.scalar(
        select(GuestbookMessage.created_at)
        .where(GuestbookMessage.visitor_hash == fingerprint)
        .order_by(GuestbookMessage.created_at.desc())
        .limit(1)
    )
    if last_created and datetime.now(timezone.utc) - last_created < POST_COOLDOWN:
        raise HTTPException(429, "Please wait before posting again", headers={"Retry-After": "30"})
    message = GuestbookMessage(
        nickname=body.nickname, body=body.body, visitor_hash=fingerprint, status="visible"
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message_response(db, message)


@router.get("/moderation", response_model=list[GuestbookResponse])
def moderation_messages(db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    rows = list(
        db.scalars(
            select(GuestbookMessage).order_by(GuestbookMessage.created_at.desc()).limit(100)
        ).all()
    )
    return [message_response(db, message) for message in rows]


def set_status(message_id: UUID, status: Literal["visible", "hidden"], db: DB):
    message = db.get(GuestbookMessage, message_id)
    if message is None:
        raise HTTPException(404, "Message not found")
    message.status = status
    photo = db.scalar(select(MediaAsset).where(MediaAsset.guestbook_message_id == message.id))
    if photo is not None:
        photo.status = "visible" if status == "visible" else "hidden"
    db.commit()
    db.refresh(message)
    return message_response(db, message)


@router.post("/messages/{message_id}/hide", response_model=GuestbookResponse, dependencies=mutation)
def hide_message(message_id: UUID, db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    return set_status(message_id, "hidden", db)


@router.post(
    "/messages/{message_id}/restore", response_model=GuestbookResponse, dependencies=mutation
)
def restore_message(message_id: UUID, db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    return set_status(message_id, "visible", db)
