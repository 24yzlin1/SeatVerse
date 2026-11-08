from app.core.common import AppError
from app.core.security import issue_token, verify_password
from app.repos.authentication import find_user_by_email, find_user_by_id
from app.types.authentication import (
    AuthenticationPayload,
    Identity,
    MePayload,
    UserPublic,
    UserRow,
)
from app.types.database import DatabaseConnection


def _to_public(row: UserRow) -> UserPublic:
    return UserPublic(
        id=row.id,
        name=row.name,
        email=row.email,
        role=row.role,
    )


def login(
    connection: DatabaseConnection,
    email: str,
    password: str,
) -> AuthenticationPayload:
    user = find_user_by_email(connection, email)
    if user is None or not verify_password(
        password,
        user.password_hash,
    ):
        raise AppError(401, "Invalid email or password")
    token = issue_token(user.id, user.role)
    return AuthenticationPayload(
        token=token,
        user=_to_public(user),
    )


def me(
    connection: DatabaseConnection,
    identity: Identity,
) -> MePayload:
    user = find_user_by_id(
        connection,
        identity.user_id,
    )
    if user is None:
        raise AppError(401, "Session expired, please log in again")
    return MePayload(user=_to_public(user))
