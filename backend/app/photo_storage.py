"""Coordinate photo transactions with immutable R2 objects and retryable cleanup."""

import logging
from contextlib import contextmanager
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import StorageDeletion
from .storage import StorageUnavailable, get_storage

logger = logging.getLogger(__name__)


def queue_deletion(db: Session, key: str | None) -> None:
    if key:
        db.merge(StorageDeletion(storage_key=key))


def retry_deletions(db: Session, keys: list[str] | None = None, limit: int = 20) -> None:
    """Run after commit; failed deletes stay queued without failing the user's update."""
    storage = get_storage()
    if not storage.enabled:
        return
    try:
        query = select(StorageDeletion).order_by(StorageDeletion.created_at).limit(limit)
        if keys is not None:
            query = query.where(StorageDeletion.storage_key.in_(keys))
        rows = db.scalars(query.with_for_update(skip_locked=True)).all()
        for row in rows:
            try:
                storage.delete(row.storage_key)
            except StorageUnavailable:
                logger.warning("R2 cleanup deferred for %s", row.storage_key)
            else:
                db.delete(row)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("R2 cleanup deferred; retry with python -m app.photo_storage")


class PhotoWrite:
    def __init__(self, db: Session):
        self.db = db
        self.uploaded: list[str] = []
        self.obsolete: list[str] = []

    def put(self, prefix: str, data: bytes, content_type: str) -> str | None:
        storage = get_storage()
        if storage.configured and not storage.enabled:
            raise HTTPException(503, "R2 storage configuration is incomplete")
        if not storage.enabled:
            return None
        key = f"{prefix}/{uuid4()}"
        # A timed-out PUT may already have succeeded: clean up attempted writes too.
        self.uploaded.append(key)
        try:
            storage.put(key, data, content_type)
        except StorageUnavailable as error:
            raise HTTPException(503, "Media storage is unavailable") from error
        return key

    def retire(self, key: str | None) -> None:
        if key:
            queue_deletion(self.db, key)
            self.obsolete.append(key)


@contextmanager
def photo_transaction(db: Session):
    """Commit pointers before retiring objects; compensate uploads on rollback."""
    write = PhotoWrite(db)
    try:
        yield write
        db.commit()
    except Exception as error:
        # Log before cleanup so a secondary failure cannot obscure the original type.
        logger.error(
            "Photo transaction failed exception_type=%s cause_type=%s",
            type(error).__name__,
            type(error.__cause__).__name__ if error.__cause__ else "none",
        )
        db.rollback()
        if write.uploaded:
            try:
                for key in write.uploaded:
                    queue_deletion(db, key)
                db.commit()
            except Exception:
                db.rollback()
                # If both databases are unavailable, retain exact keys in server logs.
                logger.exception("Could not queue uncommitted R2 uploads: %s", write.uploaded)
                for key in write.uploaded:
                    try:
                        get_storage().delete(key)
                    except StorageUnavailable:
                        logger.error("R2 object needs manual cleanup: %s", key)
            else:
                retry_deletions(db, write.uploaded)
        raise
    else:
        if write.obsolete:
            retry_deletions(db, write.obsolete)


if __name__ == "__main__":
    from .database import get_engine

    # Bounded batches; safe to rerun after a storage outage, using backend credentials.
    with Session(get_engine()) as session:
        retry_deletions(session, limit=100)
