from fastapi import APIRouter, Depends, Header

from app.core.authentication import login as login_core
from app.core.authentication import me as me_core
from app.core.common import AppError
from app.core.security import parse_token
from app.repos.database import get_connection
from app.scope.common import ok
from app.types.authentication import (
    AuthenticationPayload,
    Identity,
    LoginRequest,
    MePayload,
    UserRole,
)
from app.types.common import ResponsePayload

router = APIRouter(prefix="/api/authentication", tags=["authentication"])


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise AppError(400, "Invalid email format")
    return email


def require_identity(
    authorization: str | None = Header(default=None),
) -> Identity:
    if authorization is None or not authorization.startswith("Bearer "):
        raise AppError(401, "Please log in first")
    claims = parse_token(authorization[7:].strip())
    if claims is None:
        raise AppError(401, "Token expired or invalid, please log in again")
    if claims.role != "user" and claims.role != "organizer":
        raise AppError(401, "Invalid session, please log in again")
    return Identity(user_id=claims.user_id, role=claims.role)


def require_role(role: UserRole) -> object:
    def dependency(identity: Identity = Depends(require_identity)) -> Identity:
        if identity.role != role:
            raise AppError(403, "Forbidden")
        return identity

    return dependency


@router.post("/login")
def login(body: LoginRequest) -> ResponsePayload[AuthenticationPayload]:
    email = _normalize_email(body.email)
    if not body.password:
        raise AppError(400, "Password is required")
    connection = get_connection()
    try:
        payload = login_core(connection, email, body.password)
    finally:
        connection.close()
    return ok(payload)


@router.get("/me")
def me(identity: Identity = Depends(require_identity)) -> ResponsePayload[MePayload]:
    connection = get_connection()
    try:
        payload = me_core(connection, identity)
    finally:
        connection.close()
    return ok(payload)
