from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TeamResponse(ORMResponse):
    id: UUID
    fla_team_id: int
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


class VideoResponse(ORMResponse):
    embed_url: str | None = None
    id: UUID
    title: str | None
    published_at: datetime | None


class MatchDetail(MatchResponse):
    videos: list[VideoResponse]


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
