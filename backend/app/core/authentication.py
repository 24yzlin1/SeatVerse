from datetime import datetime, timezone
from app.core.common import AppError
from app.core.security import hash_password, issue_token, verify_password
from app.repos.authentication import find_user_by_email, find_user_by_id, insert_user
from app.types.authentication import (
    AuthenticationPayload,
    Identity,
    UserPublic,
    UserRole,
    UserRow,
)
from app.repos.database import UniqueConstraintViolationError


def _to_public(row: UserRow) -> UserPublic:
    return UserPublic(id=row.id, name=row.name, email=row.email, role=row.role)


def register(
    name: str, email: str, password: str, role: UserRole
) -> AuthenticationPayload:
    existing_user = find_user_by_email(email)
    if existing_user is not None:
        raise AppError(409, "Email is already registered")
    password_hash = hash_password(password)
    created_at = datetime.now(timezone.utc).isoformat()
    try:
        user = insert_user(
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            created_at=created_at,
        )
    except UniqueConstraintViolationError:
        raise AppError(409, "Email is already registered") from None
    token = issue_token(user.id, user.role)
    return AuthenticationPayload(token=token, user=_to_public(user))


def login(
    email: str,
    password: str,
) -> AuthenticationPayload:
    user = find_user_by_email(email)
    if user is None or not verify_password(password, user.password_hash):
        raise AppError(401, "Invalid email or password")
    token = issue_token(user.id, user.role)
    return AuthenticationPayload(token=token, user=_to_public(user))


def me(identity: Identity) -> UserPublic:
    """The payload of `GET /authentication/me` is the user object itself (auth.md §14.2 rule 4).

    Do not wrap it in `{ "user": ... }`: the frontend `bootstrap()` uses the returned
    value to overwrite the user cache directly. An extra layer would make `role`
    unreadable, and after a refresh an organizer would be treated as a regular user.
    """
    user = find_user_by_id(identity.user_id)
    if user is None:
        raise AppError(401, "Session expired, please log in again")
    return _to_public(user)
