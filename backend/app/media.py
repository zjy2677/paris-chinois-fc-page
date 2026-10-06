import urllib.parse
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from .auth.dependencies import DB, current_user, require_role, throttle, trusted_origin
from .guestbook import COOKIE_NAME, token_hash
from .models import AlbumPhoto, BlogPost, GuestbookMessage, Match, MediaAsset, PhotoAlbum, User

router = APIRouter(prefix="/api/media", tags=["Media"])
mutation = [Depends(trusted_origin), Depends(throttle)]
MAX_IMAGE_BYTES = 8 * 1024 * 1024
MAX_PHOTOS_PER_CONTENT = 20
ALLOWED_TYPES = {
    "image/png": b"\x89PNG\r\n\x1a\n",
    "image/jpeg": b"\xff\xd8\xff",
    "image/webp": b"RIFF",
}


class PhotoResponse(BaseModel):
    id: UUID
    url: str
    caption: str | None
    alt_text: str


class AlbumInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=2, max_length=180)
    description: str | None = Field(default=None, max_length=2000)
    event_date: datetime | None = None


class AlbumResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    event_date: datetime | None
    created_at: datetime
    photos: list[PhotoResponse]


def photo_response(asset: MediaAsset) -> PhotoResponse:
    return PhotoResponse(
        id=asset.id,
        url=f"/api/media/photos/{asset.id}/content",
        caption=asset.caption,
        alt_text=asset.alt_text,
    )


def image_type(content_type: str, data: bytes) -> str:
    normalized = content_type.split(";", 1)[0].strip().lower()
    signature = ALLOWED_TYPES.get(normalized)
    if signature is None or not data.startswith(signature):
        raise HTTPException(415, "Only PNG, JPEG, and WebP images are supported")
    if normalized == "image/webp" and data[8:12] != b"WEBP":
        raise HTTPException(415, "Invalid WebP image")
    return normalized


async def read_image(request: Request) -> tuple[str, bytes]:
    declared = request.headers.get("content-length")
    if declared:
        try:
            if int(declared) > MAX_IMAGE_BYTES:
                raise HTTPException(413, "Image is too large")
        except ValueError as error:
            raise HTTPException(400, "Invalid content length") from error
    buffer = bytearray()
    async for chunk in request.stream():
        if len(buffer) + len(chunk) > MAX_IMAGE_BYTES:
            raise HTTPException(413, "Image is too large")
        buffer.extend(chunk)
    data = bytes(buffer)
    if not data:
        raise HTTPException(400, "Image is required")
    return image_type(request.headers.get("content-type", ""), data), data


def metadata(value: str | None) -> str | None:
    if value is None:
        return None
    decoded = urllib.parse.unquote(value).strip()
    return decoded or None


def album_response(db: DB, album: PhotoAlbum) -> AlbumResponse:
    photos = db.scalars(
        select(MediaAsset)
        .join(AlbumPhoto, AlbumPhoto.media_id == MediaAsset.id)
        .where(AlbumPhoto.album_id == album.id, MediaAsset.status == "visible")
        .order_by(AlbumPhoto.position, MediaAsset.created_at)
    ).all()
    return AlbumResponse(
        id=album.id,
        title=album.title,
        description=album.description,
        event_date=album.event_date,
        created_at=album.created_at,
        photos=[photo_response(photo) for photo in photos],
    )


@router.get("/albums", response_model=list[AlbumResponse])
def albums(db: DB):
    rows = db.scalars(
        select(PhotoAlbum).order_by(PhotoAlbum.event_date.desc(), PhotoAlbum.created_at.desc())
    ).all()
    return [album_response(db, album) for album in rows]


@router.get("/albums/{album_id}", response_model=AlbumResponse)
def album(album_id: UUID, db: DB):
    row = db.get(PhotoAlbum, album_id)
    if row is None:
        raise HTTPException(404, "Album not found")
    return album_response(db, row)


@router.post("/albums", response_model=AlbumResponse, status_code=201, dependencies=mutation)
def create_album(body: AlbumInput, db: DB, user: Annotated[User, Depends(require_role("admin"))]):
    row = PhotoAlbum(created_by=user.id, **body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return album_response(db, row)


async def new_asset(
    request: Request,
    db: DB,
    user_id: UUID | None,
    caption: str | None,
    alt_text: str | None,
    status: str = "visible",
    **links,
) -> MediaAsset:
    content_type, data = await read_image(request)
    asset = MediaAsset(
        uploaded_by=user_id,
        content_type=content_type,
        size_bytes=len(data),
        data=data,
        caption=metadata(caption),
        alt_text=metadata(alt_text) or "",
        status=status,
        **links,
    )
    db.add(asset)
    db.flush()
    return asset


@router.post(
    "/albums/{album_id}/photos",
    response_model=PhotoResponse,
    status_code=201,
    dependencies=mutation,
)
async def upload_album_photo(
    album_id: UUID,
    request: Request,
    db: DB,
    user: Annotated[User, Depends(require_role("admin"))],
    caption: str | None = Query(default=None, max_length=900),
    alt: str | None = Query(default=None, max_length=900),
):
    if db.get(PhotoAlbum, album_id) is None:
        raise HTTPException(404, "Album not found")
    count = (
        db.scalar(
            select(func.count()).select_from(AlbumPhoto).where(AlbumPhoto.album_id == album_id)
        )
        or 0
    )
    if count >= MAX_PHOTOS_PER_CONTENT:
        raise HTTPException(409, "Photo limit reached")
    asset = await new_asset(request, db, user.id, caption, alt)
    db.add(AlbumPhoto(album_id=album_id, media_id=asset.id, position=count))
    db.commit()
    return photo_response(asset)


@router.post(
    "/blog/{post_id}/photos", response_model=PhotoResponse, status_code=201, dependencies=mutation
)
async def upload_blog_photo(
    post_id: UUID,
    request: Request,
    db: DB,
    user: Annotated[User, Depends(current_user)],
    caption: str | None = Query(default=None, max_length=900),
    alt: str | None = Query(default=None, max_length=900),
):
    post = db.get(BlogPost, post_id)
    if post is None:
        raise HTTPException(404, "Post not found")
    if post.author_id != user.id and user.role != "admin":
        raise HTTPException(403, "Not your post")
    if post.status not in ("draft", "rejected"):
        raise HTTPException(409, "Only editable posts accept photos")
    count = (
        db.scalar(
            select(func.count()).select_from(MediaAsset).where(MediaAsset.blog_post_id == post_id)
        )
        or 0
    )
    if count >= MAX_PHOTOS_PER_CONTENT:
        raise HTTPException(409, "Photo limit reached")
    asset = await new_asset(
        request, db, user.id, caption, alt, blog_post_id=post_id, position=count
    )
    db.commit()
    return photo_response(asset)


@router.post(
    "/matches/{match_id}/photos",
    response_model=PhotoResponse,
    status_code=201,
    dependencies=mutation,
)
async def upload_match_photo(
    match_id: UUID,
    request: Request,
    db: DB,
    user: Annotated[User, Depends(require_role("admin"))],
    caption: str | None = Query(default=None, max_length=900),
    alt: str | None = Query(default=None, max_length=900),
):
    if db.get(Match, match_id) is None:
        raise HTTPException(404, "Match not found")
    count = (
        db.scalar(
            select(func.count()).select_from(MediaAsset).where(MediaAsset.match_id == match_id)
        )
        or 0
    )
    if count >= MAX_PHOTOS_PER_CONTENT:
        raise HTTPException(409, "Photo limit reached")
    asset = await new_asset(request, db, user.id, caption, alt, match_id=match_id, position=count)
    db.commit()
    return photo_response(asset)


@router.post(
    "/guestbook/{message_id}/photo",
    response_model=PhotoResponse,
    status_code=201,
    dependencies=mutation,
)
async def upload_guestbook_photo(
    message_id: UUID,
    request: Request,
    db: DB,
    caption: str | None = Query(default=None, max_length=900),
    alt: str | None = Query(default=None, max_length=900),
):
    message = db.get(GuestbookMessage, message_id)
    token = request.cookies.get(COOKIE_NAME)
    if message is None or token is None or message.visitor_hash != token_hash(token):
        raise HTTPException(404, "Message not found")
    exists = db.scalar(select(MediaAsset.id).where(MediaAsset.guestbook_message_id == message_id))
    if exists:
        raise HTTPException(409, "A message can have one photo")
    asset = await new_asset(
        request, db, None, caption, alt, status="pending", guestbook_message_id=message_id
    )
    message.status = "hidden"
    db.commit()
    return photo_response(asset)


@router.get("/photos/{photo_id}/content")
def photo_content(photo_id: UUID, db: DB):
    asset = db.get(MediaAsset, photo_id)
    if asset is None or asset.status != "visible":
        raise HTTPException(404, "Photo not found")
    allowed = asset.match_id is not None
    if asset.blog_post_id:
        allowed = (
            allowed
            or db.scalar(
                select(BlogPost.id).where(
                    BlogPost.id == asset.blog_post_id, BlogPost.status == "published"
                )
            )
            is not None
        )
    if asset.guestbook_message_id:
        allowed = (
            allowed
            or db.scalar(
                select(GuestbookMessage.id).where(
                    GuestbookMessage.id == asset.guestbook_message_id,
                    GuestbookMessage.status == "visible",
                )
            )
            is not None
        )
    allowed = (
        allowed
        or db.scalar(select(AlbumPhoto.media_id).where(AlbumPhoto.media_id == asset.id)) is not None
    )
    if not allowed:
        raise HTTPException(404, "Photo not found")
    return Response(
        content=asset.data,
        media_type=asset.content_type,
        headers={"Cache-Control": "public, max-age=86400", "X-Content-Type-Options": "nosniff"},
    )


@router.delete("/photos/{photo_id}", status_code=204, dependencies=mutation)
def delete_photo(photo_id: UUID, db: DB, user: Annotated[User, Depends(current_user)]):
    asset = db.get(MediaAsset, photo_id)
    if asset is None:
        raise HTTPException(404, "Photo not found")
    if user.role != "admin" and asset.uploaded_by != user.id:
        raise HTTPException(403, "Not your photo")
    db.delete(asset)
    db.commit()
