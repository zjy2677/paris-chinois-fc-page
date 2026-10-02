from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TeamResponse(ORMResponse):
    id: UUID
    fla_team_id: int | None
    name: str
    logo_url: str | None


class VenueResponse(ORMResponse):
    name: str
    address: str
    timezone: str


class MatchResponse(BaseModel):
    id: UUID
    competition_season_id: UUID
    home_team: TeamResponse
    away_team: TeamResponse
    venue: VenueResponse | None
    kickoff_at: datetime | None
    competition_name: str
    competition_kind: str
    matchday: int | None
    leg: str
    status: str
    home_score: int | None
    away_score: int | None
    source_url: str
    last_synced_at: datetime
    source_type: str


class MatchEventResponse(BaseModel):
    id: UUID
    event_type: str
    player_id: UUID
    player_name: str
    assist_player_id: UUID | None
    assist_player_name: str | None
    minute: int | None
    sequence: int


class VideoResponse(ORMResponse):
    embed_url: str | None = None
    id: UUID
    title: str | None
    published_at: datetime | None


class MatchDetail(MatchResponse):
    videos: list[VideoResponse]
    description: str | None
    events: list[MatchEventResponse]


class MatchEventInput(BaseModel):
    event_type: Literal["goal", "yellow_card", "red_card"]
    player_id: UUID
    assist_player_id: UUID | None = None
    minute: int | None = Field(None, ge=0, le=130)


class MatchRecordUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    description: str | None = Field(None, max_length=10000)
    home_score: int | None = Field(None, ge=0, le=99)
    away_score: int | None = Field(None, ge=0, le=99)
    events: list[MatchEventInput] = Field(default_factory=list, max_length=100)


class ManualMatchCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    opponent_name: str = Field(min_length=1, max_length=200)
    competition_name: str = Field(default="Friendly", min_length=1, max_length=200)
    season_label: str = Field(default="2026/2027", pattern=r"^\d{4}/\d{4}$")
    kickoff_at: datetime | None = None
    is_home: bool = True
    home_score: int | None = Field(None, ge=0, le=99)
    away_score: int | None = Field(None, ge=0, le=99)
    description: str | None = Field(None, max_length=10000)


class MatchPage(BaseModel):
    items: list[MatchResponse]
    offset: int
    limit: int
    total: int


class StandingResponse(BaseModel):
    team: TeamResponse
    position: int
    played: int
    wins: int
    draws: int
    losses: int
    goal_difference: int
    points: int


class StandingsResponse(BaseModel):
    competition_season_id: UUID | None
    source_url: str | None
    fetched_at: datetime | None
    last_successful_sync: datetime | None
    rows: list[StandingResponse]


class PlayerResponse(BaseModel):
    id: UUID
    display_name: str
    photo_url: str | None
    season: str
    shirt_number: int | None
    position: str


class ContactRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr = Field(max_length=254)
    subject: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=5000)


class HomepageLikeResponse(BaseModel):
    count: int
    liked: bool
