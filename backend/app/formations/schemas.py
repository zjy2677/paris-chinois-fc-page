from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Placement(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    player_id: UUID
    placement: Literal["pitch", "bench"]
    x: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    y: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)

    @model_validator(mode="after")
    def coordinates(self):
        if self.placement == "pitch" and (self.x is None or self.y is None):
            raise ValueError("Pitch placements require both coordinates")
        if self.placement == "bench" and (self.x is not None or self.y is not None):
            raise ValueError("Bench placements cannot have coordinates")
        return self


class FormationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    placements: list[Placement] = Field(max_length=100)

    @model_validator(mode="after")
    def unique_players(self):
        ids = [item.player_id for item in self.placements]
        if len(ids) != len(set(ids)):
            raise ValueError("A player can only appear once")
        return self


class BoardPlayer(BaseModel):
    id: UUID
    display_name: str
    chinese_name: str | None
    photo_url: str | None
    has_uploaded_photo: bool
    shirt_number: int | None
    description: str | None
    position: str | None
    goals: int = 0
    assists: int = 0


class FormationResponse(BaseModel):
    match_id: UUID
    status: str
    kickoff_at: datetime | None
    editable: bool
    placements: list[Placement]
    players: list[BoardPlayer]
