from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RatingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stars: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)

    @field_validator("comment")
    @classmethod
    def clean_comment(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None


class PlayerRatingSummary(BaseModel):
    player_id: UUID
    display_name: str
    chinese_name: str | None
    photo_url: str | None
    has_uploaded_photo: bool
    shirt_number: int | None
    participation: Literal["start", "sub", "absent"]
    average_stars: float | None
    rating_count: int


class RatingItem(BaseModel):
    id: UUID
    stars: int
    comment: str | None
    author_name: str
    created_at: datetime
    updated_at: datetime


class PlayerRatingDetail(BaseModel):
    summary: PlayerRatingSummary
    ratings: list[RatingItem]


class MyRating(BaseModel):
    stars: int
    comment: str | None
