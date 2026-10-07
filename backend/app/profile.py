from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select

from .auth.dependencies import DB, current_user, throttle, trusted_origin
from .models import User, UserAvatar
from .storage import StorageUnavailable, get_storage

router = APIRouter(prefix="/api/profile", tags=["Profile"])
mutation = [Depends(trusted_origin), Depends(throttle)]
MAX_AVATAR_BYTES = 2 * 1024 * 1024
ALLOWED_TYPES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "image/webp": b"RIFF",
}


def avatar_type(content_type: str, data: bytes) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    signature = ALLOWED_TYPES.get(normalized)
    if signature is None or not data.startswith(signature):
        raise HTTPException(415, "Only PNG, JPEG, and WebP images are supported")
    if normalized == "image/webp" and data[8:12] != b"WEBP":
        raise HTTPException(415, "Invalid WebP image")
    return normalized


@router.get("/avatar")
def get_avatar(db: DB, user: Annotated[User, Depends(current_user)]):
    avatar = db.scalar(select(UserAvatar).where(UserAvatar.user_id == user.id))
    if avatar is None:
        raise HTTPException(404, "Profile picture not found")
    try:
        data = get_storage().get(avatar.storage_key) if avatar.storage_key else avatar.data
    except StorageUnavailable as error:
        raise HTTPException(503, "Media storage is unavailable") from error
    if data is None:
        raise HTTPException(404, "Profile picture content is unavailable")
    return Response(
        content=data,
        media_type=avatar.content_type,
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.put("/avatar", dependencies=mutation, status_code=204)
async def upload_avatar(request: Request, db: DB, user: Annotated[User, Depends(current_user)]):
    declared_size = request.headers.get("content-length")
    if declared_size:
        try:
            if int(declared_size) > MAX_AVATAR_BYTES:
                raise HTTPException(413, "Profile picture is too large")
        except ValueError as error:
            raise HTTPException(400, "Invalid content length") from error
    buffer = bytearray()
    async for chunk in request.stream():
        if len(buffer) + len(chunk) > MAX_AVATAR_BYTES:
            raise HTTPException(413, "Profile picture is too large")
        buffer.extend(chunk)
    data = bytes(buffer)
    if not data:
        raise HTTPException(400, "Profile picture is required")
    content_type = avatar_type(request.headers.get("content-type", ""), data)
    storage = get_storage()
    if storage.configured and not storage.enabled:
        raise HTTPException(503, "R2 storage configuration is incomplete")
    avatar = db.scalar(select(UserAvatar).where(UserAvatar.user_id == user.id))
    storage_key = f"avatars/{user.id}" if storage.enabled else None
    if storage.enabled:
        try:
            storage.put(storage_key, data, content_type)
        except StorageUnavailable as error:
            raise HTTPException(503, "Media storage is unavailable") from error
    if avatar is None:
        db.add(
            UserAvatar(
                user_id=user.id,
                content_type=content_type,
                data=None if storage.enabled else data,
                storage_key=storage_key,
            )
        )
    else:
        avatar.content_type = content_type
        avatar.data = None if storage.enabled else data
        avatar.storage_key = storage_key
    db.commit()


@router.delete("/avatar", dependencies=mutation, status_code=204)
def delete_avatar(db: DB, user: Annotated[User, Depends(current_user)]):
    avatar = db.scalar(select(UserAvatar).where(UserAvatar.user_id == user.id))
    if avatar is not None:
        if avatar.storage_key:
            try:
                get_storage().delete(avatar.storage_key)
            except StorageUnavailable as error:
                raise HTTPException(503, "Media storage is unavailable") from error
        db.delete(avatar)
        db.commit()
