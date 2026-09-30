from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

Minute = Annotated[int, Field(ge=0, strict=True)]
StoppageMinute = Annotated[int, Field(gt=0, strict=True)]
GoalType = Literal["regular", "penalty", "own_goal"]


class GoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    team_id: UUID
    scorer_id: UUID | None = None
    assist_player_id: UUID | None = None
    minute: Minute | None = None
    stoppage_minute: StoppageMinute | None = None
    goal_type: GoalType = "regular"

    @model_validator(mode="after")
    def validate_goal(self):
        if self.scorer_id is not None and self.scorer_id == self.assist_player_id:
            raise ValueError("A scorer cannot assist their own goal")
        if self.goal_type == "own_goal" and self.assist_player_id is not None:
            raise ValueError("An own goal cannot have an assist")
        if self.stoppage_minute is not None and self.minute is None:
            raise ValueError("Stoppage time requires a match minute")
        return self


class GoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    team_id: UUID | None = None
    scorer_id: UUID | None = None
    assist_player_id: UUID | None = None
    minute: Minute | None = None
    stoppage_minute: StoppageMinute | None = None
    goal_type: GoalType | None = None


class GoalPlayer(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    display_name: str


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    match_id: UUID
    team_id: UUID
    scorer_id: UUID | None
    assist_player_id: UUID | None
    scorer: GoalPlayer | None
    assist_player: GoalPlayer | None
    minute: int | None
    stoppage_minute: int | None
    goal_type: GoalType
    created_at: datetime
    updated_at: datetime
