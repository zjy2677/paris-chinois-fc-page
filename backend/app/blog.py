from datetime import datetime, timezone
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .auth.dependencies import DB, current_user, require_role, throttle, trusted_origin
from .models import BlogPost, MediaAsset, User


class BlogPhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    url: str
    caption: str | None
    alt_text: str


router = APIRouter(prefix="/api/blog", tags=["Blog"])
mutation = [Depends(trusted_origin), Depends(throttle)]


class BlogPostInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=3, max_length=180)
    body: str = Field(min_length=20, max_length=20000)
    submit: bool = False


class BlogPostUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    title: str = Field(min_length=3, max_length=180)
    body: str = Field(min_length=20, max_length=20000)


class BlogPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    title: str
    body: str
    status: Literal["draft", "pending", "published", "rejected"]
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    photos: list[BlogPhotoResponse] = Field(default_factory=list)


class BlogPostPage(BaseModel):
    items: list[BlogPostResponse]
    total: int


def owned_post(db: Session, post_id: UUID, user: User) -> BlogPost:
    post = db.get(BlogPost, post_id, with_for_update=True)
    if post is None:
        raise HTTPException(404, "Post not found")
    if post.author_id != user.id and user.role != "admin":
        raise HTTPException(403, "Not your post")
    return post


def post_response(db: Session, post: BlogPost) -> BlogPostResponse:
    photos = db.scalars(
        select(MediaAsset)
        .where(MediaAsset.blog_post_id == post.id, MediaAsset.status == "visible")
        .order_by(MediaAsset.position, MediaAsset.created_at)
    ).all()
    return BlogPostResponse.model_validate(
        {
            "id": post.id,
            "title": post.title,
            "body": post.body,
            "status": post.status,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "published_at": post.published_at,
            "photos": photos,
        }
    )


@router.get("/posts", response_model=BlogPostPage)
def published_posts(db: DB, offset: int = Query(0, ge=0), limit: int = Query(12, ge=1, le=50)):
    condition = BlogPost.status == "published"
    items = db.scalars(
        select(BlogPost)
        .where(condition)
        .order_by(BlogPost.published_at.desc(), BlogPost.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    total = db.scalar(select(func.count()).select_from(BlogPost).where(condition)) or 0
    return BlogPostPage(items=[post_response(db, post) for post in items], total=total)


@router.get("/mine", response_model=list[BlogPostResponse])
def my_posts(db: DB, user: Annotated[User, Depends(current_user)]):
    posts = list(
        db.scalars(
            select(BlogPost)
            .where(BlogPost.author_id == user.id)
            .order_by(BlogPost.updated_at.desc())
        ).all()
    )
    return [post_response(db, post) for post in posts]


@router.get("/moderation", response_model=list[BlogPostResponse])
def moderation_queue(db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    posts = list(
        db.scalars(
            select(BlogPost).where(BlogPost.status == "pending").order_by(BlogPost.updated_at.asc())
        ).all()
    )
    return [post_response(db, post) for post in posts]


@router.get("/posts/{post_id}", response_model=BlogPostResponse)
def published_post(post_id: UUID, db: DB):
    post = db.get(BlogPost, post_id)
    if post is None or post.status != "published":
        raise HTTPException(404, "Post not found")
    return post_response(db, post)


@router.post("/posts", response_model=BlogPostResponse, status_code=201, dependencies=mutation)
def create_post(body: BlogPostInput, db: DB, user: Annotated[User, Depends(current_user)]):
    values = body.model_dump(exclude={"submit"})
    post = BlogPost(author_id=user.id, status="pending" if body.submit else "draft", **values)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_response(db, post)


@router.patch("/posts/{post_id}", response_model=BlogPostResponse, dependencies=mutation)
def update_post(
    post_id: UUID,
    body: BlogPostUpdate,
    db: DB,
    user: Annotated[User, Depends(current_user)],
):
    post = owned_post(db, post_id, user)
    if post.status not in ("draft", "rejected"):
        raise HTTPException(409, "Only draft or rejected posts can be edited")
    for field, value in body.model_dump().items():
        setattr(post, field, value)
    post.status = "draft"
    db.commit()
    db.refresh(post)
    return post_response(db, post)


@router.post("/posts/{post_id}/submit", response_model=BlogPostResponse, dependencies=mutation)
def submit_post(post_id: UUID, db: DB, user: Annotated[User, Depends(current_user)]):
    post = owned_post(db, post_id, user)
    if post.status not in ("draft", "rejected"):
        raise HTTPException(409, "Post cannot be submitted")
    post.status = "pending"
    db.commit()
    db.refresh(post)
    return post_response(db, post)


@router.post("/posts/{post_id}/publish", response_model=BlogPostResponse, dependencies=mutation)
def publish_post(post_id: UUID, db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    post = db.get(BlogPost, post_id, with_for_update=True)
    if post is None:
        raise HTTPException(404, "Post not found")
    if post.status != "pending":
        raise HTTPException(409, "Only pending posts can be moderated")
    post.status = "published"
    post.published_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(post)
    return post_response(db, post)


@router.post("/posts/{post_id}/reject", response_model=BlogPostResponse, dependencies=mutation)
def reject_post(post_id: UUID, db: DB, _: Annotated[User, Depends(require_role("admin"))]):
    post = db.get(BlogPost, post_id, with_for_update=True)
    if post is None:
        raise HTTPException(404, "Post not found")
    if post.status != "pending":
        raise HTTPException(409, "Only pending posts can be moderated")
    post.status = "rejected"
    post.published_at = None
    db.commit()
    db.refresh(post)
    return post_response(db, post)
