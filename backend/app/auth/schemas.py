from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=254)
    password: str = Field(min_length=1, max_length=256)


class RegisterRequest(LoginRequest):
    password: str = Field(min_length=12, max_length=256)


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: Literal["user", "player", "admin"]
