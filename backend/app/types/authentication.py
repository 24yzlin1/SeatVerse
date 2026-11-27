from dataclasses import dataclass
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

UserRole = Literal["user", "organizer"]


@dataclass(frozen=True)
class UserRow:
    id: int
    name: str
    email: str
    password_hash: str
    role: UserRole
    created_at: str
    avatar_url: str  # 新增


class UserPublic(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole = "user"
    avatar_url: str = Field(default="", alias="avatarUrl")  # 新增


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str
    email: str
    password: str


class AuthenticationPayload(BaseModel):
    token: str
    user: UserPublic


class Identity(BaseModel):
    user_id: int
    role: UserRole


class UserAvatarRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    avatar_url: str = Field(default="", alias="avatarUrl")  