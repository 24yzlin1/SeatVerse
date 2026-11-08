from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

UserRole = Literal["user", "organizer"]


@dataclass(frozen=True)
class UserRow:
    id: int
    name: str
    email: str
    password_hash: str
    role: UserRole
    created_at: str


class UserPublic(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthenticationPayload(BaseModel):
    token: str
    user: UserPublic


class MePayload(BaseModel):
    user: UserPublic


class Identity(BaseModel):
    user_id: int
    role: UserRole
