from fastapi import APIRouter, Depends, Header

from app.core.authentication import register as register_core
from app.core.authentication import login as login_core
from app.core.authentication import me as me_core
from app.core.common import AppError
from app.core.security import parse_token
from app.scope.common import ok
from app.types.authentication import (
    AuthenticationPayload,
    Identity,
    LoginRequest,
    MePayload,
    RegisterRequest,
    UserRole,
)
from app.types.common import ResponsePayload

router = APIRouter(prefix="/authentication", tags=["authentication"])


def _normalize_email(value: str) -> str:
    email = value.strip().lower()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise AppError(400, "Invalid email format")
    return email


def _normalize_name(value: str) -> str:
    name = value.strip()
    if not name:
        raise AppError(400, "Name is required")
    if len(name) > 50:
        raise AppError(400, "Name must be at most 50 characters")
    return name


def _validate_registration_role(value: str | None) -> None:
    if value is not None:
        raise AppError(
            400,
            "Organizer registration is not available; only ordinary users can register",
        )


def _validate_password(value: str) -> None:
    if not value:
        raise AppError(400, "Password is required")
    if len(value) < 8:
        raise AppError(400, "Password must be at least 8 characters")
    if len(value) > 128:
        raise AppError(400, "Password must be at most 128 characters")


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


@router.post("/register")
def register(body: RegisterRequest) -> ResponsePayload[AuthenticationPayload]:
    _validate_registration_role(body.role)
    name = _normalize_name(body.name)
    email = _normalize_email(body.email)
    _validate_password(body.password)
    return ok(register_core(name, email, body.password, body.role))


@router.post("/login")
def login(body: LoginRequest) -> ResponsePayload[AuthenticationPayload]:
    email = _normalize_email(body.email)
    if not body.password:
        raise AppError(400, "Password is required")
    return ok(login_core(email, body.password))


@router.get("/me")
def me(identity: Identity = Depends(require_identity)) -> ResponsePayload[MePayload]:
    return ok(me_core(identity))
