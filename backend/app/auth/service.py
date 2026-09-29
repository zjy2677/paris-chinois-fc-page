import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import SessionToken, User

hasher = PasswordHasher()
# Verify even unknown emails to reduce timing differences in login failures.
DUMMY_HASH = hasher.hash(uuid.uuid4().hex)
COOKIE_NAME = "pcfc_session"


def signing_key():
    secret = get_settings().jwt_secret
    if len(secret) < 32:
        raise HTTPException(503, "Authentication is not configured")
    return secret


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def register(
    db: Session, email: str, password: str, first_name: str, last_name: str, age: int
) -> User:
    signing_key()
    user = User(
        normalized_email=email.strip().casefold(),
        password_hash=hasher.hash(password),
        role="user",
        first_name=first_name,
        last_name=last_name,
        age_at_registration=age,
    )
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Registration unavailable for this email") from None
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.normalized_email == email.strip().casefold()))
    try:
        valid = hasher.verify(user.password_hash if user else DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        valid = False
    if not valid or user is None or not user.active:
        raise HTTPException(401, "Invalid email or password")
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hasher.hash(password)
    return user


def issue_session(db: Session, user: User) -> str:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(seconds=get_settings().auth_ttl_seconds)
    session_id = uuid.uuid4()
    token = jwt.encode(
        {
            "sub": str(user.id),
            "jti": str(session_id),
            "iat": now,
            "exp": expires,
            "iss": "paris-chinois-fc",
            "aud": "paris-chinois-fc-web",
        },
        signing_key(),
        algorithm="HS256",
    )
    db.add(
        SessionToken(
            id=session_id, user_id=user.id, token_hash=token_hash(token), expires_at=expires
        )
    )
    db.commit()
    return token


def resolve_session(db: Session, token: str | None) -> tuple[User, SessionToken]:
    if not token:
        raise HTTPException(401, "Not authenticated")
    try:
        claims = jwt.decode(
            token,
            signing_key(),
            algorithms=["HS256"],
            issuer="paris-chinois-fc",
            audience="paris-chinois-fc-web",
            options={"require": ["sub", "jti", "iat", "exp"]},
        )
        user_id, session_id = uuid.UUID(claims["sub"]), uuid.UUID(claims["jti"])
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(401, "Invalid or expired session") from None
    record = db.get(SessionToken, session_id)
    user = db.get(User, user_id)
    if (
        record is None
        or user is None
        or not user.active
        or record.user_id != user_id
        or record.revoked_at is not None
        or record.expires_at <= datetime.now(timezone.utc)
        or record.token_hash != token_hash(token)
    ):
        raise HTTPException(401, "Invalid or expired session")
    return user, record
