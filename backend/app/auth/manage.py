"""Owner-only local management command. Never expose through an HTTP endpoint."""

import argparse
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..database import get_engine
from ..models import SessionToken, User


def main():
    parser = argparse.ArgumentParser(
        description="Set an existing account's role using trusted database access"
    )
    parser.add_argument("email")
    parser.add_argument("role", choices=["user", "player", "admin"])
    args = parser.parse_args()
    with Session(get_engine()) as db, db.begin():
        user = db.scalar(select(User).where(User.normalized_email == args.email.strip().casefold()))
        if user is None:
            parser.error("Account not found; register it on the website first")
        old = user.role
        user.role = args.role
        db.execute(
            update(SessionToken)
            .where(SessionToken.user_id == user.id, SessionToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        print(f"{user.normalized_email}: {old} -> {args.role}. Existing sessions revoked.")


if __name__ == "__main__":
    main()
