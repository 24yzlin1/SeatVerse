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
    """`GET /authentication/me` 的 payload 就是 user 对象本身（auth.md §14.2 规则 4）。

    不能包一层 `{ "user": ... }`：前端 `bootstrap()` 直接用返回值覆盖 user 缓存，
    多包一层会让 `role` 读不到，刷新后主办方会被当成普通用户。
    """
    user = find_user_by_id(identity.user_id)
    if user is None:
        raise AppError(401, "Session expired, please log in again")
    return _to_public(user)
