from collections import OrderedDict
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import User
from .service import COOKIE_NAME, resolve_session

DB = Annotated[Session, Depends(get_db)]


def no_store(response: Response):
    response.headers["Cache-Control"] = "no-store"


def trusted_origin(request: Request):
    # All browser authentication mutations require an explicitly trusted origin.
    if request.headers.get("origin") not in get_settings().cors_origins:
        raise HTTPException(403, "Untrusted request origin")


# MVP: bounded, per-process throttling. Use a shared rate limiter before multi-worker deployment.
_attempts: OrderedDict[str, tuple[float, int]] = OrderedDict()
_lock = Lock()


def throttle(request: Request):
    key = request.client.host if request.client else "unknown"
    now = monotonic()
    with _lock:
        start, count = _attempts.pop(key, (now, 0))
        if now - start >= 60:
            start, count = now, 0
        _attempts[key] = (start, count + 1)
        while len(_attempts) > 4096:
            _attempts.popitem(last=False)
        if count >= 10:
            raise HTTPException(429, "Too many attempts", headers={"Retry-After": "60"})


def current_user(request: Request, db: DB) -> User:
    return resolve_session(db, request.cookies.get(COOKIE_NAME))[0]


def require_role(*roles: str):
    def check(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user

    return check
