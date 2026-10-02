from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

Position = Literal["Goalkeepers", "Defenders", "Midfielders", "Forwards"]
Season = Annotated[str, Field(pattern=r"^\d{4}/\d{4}$")]
ShirtNumber = Annotated[int, Field(gt=0, le=2147483647, strict=True)]


class PlayerInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str = Field(min_length=1, max_length=150)
    photo_url: HttpUrl | None = None
    description: str | None = Field(default=None, max_length=2000)
    shirt_number: ShirtNumber | None = None
    position: Position
    active: bool = Field(default=True, strict=True)

    @field_validator("photo_url")
    @classmethod
    def secure_photo(cls, value):
        """Accept null or an HTTPS photo URL without credentials and at most 2048 characters."""
        if value is not None and (value.scheme != "https" or value.username or value.password):
            raise ValueError("Use a public HTTPS photo URL without credentials")
        if value is not None and len(str(value)) > 2048:
            raise ValueError("Photo URL is too long")
        return value


class PlayerCreate(PlayerInput):
    season: Season

    @field_validator("season")
    @classmethod
    def consecutive_season(cls, value):
        """Return the season label if its end year immediately follows its start year."""
        start, end = map(int, value.split("/"))
        if end != start + 1:
            raise ValueError("Season years must be consecutive")
        return value


class PlayerUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str | None = Field(default=None, min_length=1, max_length=150)
    photo_url: HttpUrl | None = None
    description: str | None = Field(default=None, max_length=2000)
    shirt_number: ShirtNumber | None = None
    position: Position | None = None
    active: bool | None = Field(default=None, strict=True)

    @model_validator(mode="after")
    def required_fields_cannot_be_cleared(self):
        """Reject empty updates and explicit nulls for name, position, or active status."""
        for name in ("display_name", "position", "active"):
            if name in self.model_fields_set and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        if not self.model_fields_set:
            raise ValueError("Provide at least one player field")
        return self


class SquadSeasonResponse(BaseModel):
    season: str
    position: str
    shirt_number: int | None


class PlayerProfileResponse(BaseModel):
    id: UUID
    display_name: str
    photo_url: str | None
    description: str | None
    active: bool
    squads: list[SquadSeasonResponse]
    goals: int
    assists: int
