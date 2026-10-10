"""Keep rating writes separate from the shared login-attempt budget."""

from collections import OrderedDict
from threading import Lock
from time import monotonic
from typing import Annotated

from fastapi import Depends, HTTPException

from ..auth.dependencies import require_role
from ..models import User

_attempts: OrderedDict[str, tuple[float, int]] = OrderedDict()
_lock = Lock()


def throttle_rating_write(
    user: Annotated[User, Depends(require_role("player", "admin"))],
):
    """Allow a member to rate the full squad without consuming login attempts."""
    key = str(user.id)
    now = monotonic()
    with _lock:
        start, count = _attempts.pop(key, (now, 0))
        if now - start >= 60:
            start, count = now, 0
        _attempts[key] = (start, count + 1)
        while len(_attempts) > 4096:
            _attempts.popitem(last=False)
        if count >= 60:
            raise HTTPException(429, "Too many rating attempts", headers={"Retry-After": "60"})
