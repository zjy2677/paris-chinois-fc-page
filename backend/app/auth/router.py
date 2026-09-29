from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from ..config import get_settings
from ..models import User
from .dependencies import DB, current_user, no_store, throttle, trusted_origin
from .schemas import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from .service import COOKIE_NAME, authenticate, issue_session, register, resolve_session

router = APIRouter(prefix="/api/auth", tags=["Authentication"], dependencies=[Depends(no_store)])
mutation = [Depends(trusted_origin), Depends(throttle)]


def public_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.normalized_email,
        role=user.role,
        first_name=user.first_name,
        last_name=user.last_name,
        age_at_registration=user.age_at_registration,
        avatar_updated_at=user.avatar.updated_at if user.avatar else None,
    )


def set_cookie(response: Response, token: str):
    settings = get_settings()
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite="lax",
        path="/api",
        max_age=settings.auth_ttl_seconds,
    )


@router.post("/register", response_model=UserResponse, status_code=201, dependencies=mutation)
def register_user(body: RegisterRequest, response: Response, db: DB):
    user = register(db, str(body.email), body.password, body.first_name, body.last_name, body.age)
    set_cookie(response, issue_session(db, user))
    return public_user(user)


@router.post("/login", response_model=UserResponse, dependencies=mutation)
def login(body: LoginRequest, response: Response, db: DB):
    user = authenticate(db, str(body.email), body.password)
    set_cookie(response, issue_session(db, user))
    return public_user(user)


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[User, Depends(current_user)]):
    return public_user(user)


@router.post("/logout", status_code=204, dependencies=[Depends(trusted_origin)])
def logout(request: Request, response: Response, db: DB):
    from fastapi import HTTPException

    try:
        _, record = resolve_session(db, request.cookies.get(COOKIE_NAME))
    except HTTPException as exc:
        if exc.status_code != 401:
            raise
    else:
        record.revoked_at = datetime.now(timezone.utc)
        db.commit()
    response.delete_cookie(
        COOKIE_NAME,
        path="/api",
        secure=get_settings().auth_cookie_secure,
        httponly=True,
        samesite="lax",
    )
