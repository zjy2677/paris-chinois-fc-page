import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from .auth.dependencies import DB, require_role, throttle, trusted_origin
from .config import get_settings
from .models import GuestbookMessage, User

router = APIRouter(prefix="/api/guestbook", tags=["Guestbook"])
mutation = [Depends(trusted_origin), Depends(throttle)]
COOKIE_NAME = "pcfc_guestbook_visitor"
COOKIE_MAX_AGE = 60 * 60 * 24 * 365
POST_COOLDOWN = timedelta(seconds=30)


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
    return list(
        db.scalars(
            select(GuestbookMessage)
            .where(GuestbookMessage.status == "visible")
            .order_by(GuestbookMessage.created_at.desc())
            .limit(60)
        ).all()
    )


@router.post("/messages", response_model=GuestbookResponse, status_code=201, dependencies=mutation)
def create_message(body: GuestbookInput, request: Request, response: Response, db: DB):
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
    return message


@router.get("/moderation", response_model=list[GuestbookResponse])
def moderation_messages(db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    return list(
        db.scalars(
            select(GuestbookMessage).order_by(GuestbookMessage.created_at.desc()).limit(100)
        ).all()
    )


def set_status(message_id: UUID, status: Literal["visible", "hidden"], db: DB):
    message = db.get(GuestbookMessage, message_id)
    if message is None:
        raise HTTPException(404, "Message not found")
    message.status = status
    db.commit()
    db.refresh(message)
    return message


@router.post("/messages/{message_id}/hide", response_model=GuestbookResponse, dependencies=mutation)
def hide_message(message_id: UUID, db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    return set_status(message_id, "hidden", db)


@router.post(
    "/messages/{message_id}/restore", response_model=GuestbookResponse, dependencies=mutation
)
def restore_message(message_id: UUID, db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    return set_status(message_id, "visible", db)
