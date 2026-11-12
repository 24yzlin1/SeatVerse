import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
import jwt

_JWT_ALGORITHM = "HS256"
_TOKEN_TIME_TO_LIVE_SECONDS = 86400
_SCRYPT_COST_FACTOR = 2**14
_SCRYPT_BLOCK_SIZE_FACTOR = 8
_SCRYPT_PARALLELIZATION_FACTOR = 1
_SCRYPT_DERIVED_KEY_LENGTH = 32
_SCRYPT_SALT_LENGTH = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SCRYPT_SALT_LENGTH)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_COST_FACTOR,
        r=_SCRYPT_BLOCK_SIZE_FACTOR,
        p=_SCRYPT_PARALLELIZATION_FACTOR,
        dklen=_SCRYPT_DERIVED_KEY_LENGTH,
    )
    return (
        f"scrypt${_SCRYPT_COST_FACTOR}${_SCRYPT_BLOCK_SIZE_FACTOR}"
        f"${_SCRYPT_PARALLELIZATION_FACTOR}${salt.hex()}${derived_key.hex()}"
    )


def verify_password(password: str, stored_password_hash: str) -> bool:
    parts = stored_password_hash.split("$")
    if len(parts) != 6 or parts[0] != "scrypt":
        return False
    _, cost_text, block_text, parallel_text, salt_hex, expected_hex = parts
    try:
        derived_key = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=int(cost_text),
            r=int(block_text),
            p=int(parallel_text),
            dklen=_SCRYPT_DERIVED_KEY_LENGTH,
        )
    except ValueError:
        return False
    return hmac.compare_digest(derived_key.hex(), expected_hex)


def _get_jwt_secret_key() -> str:
    secret_key = os.environ.get("SEATVERSE_JWT_SECRET")
    if not secret_key:
        raise RuntimeError("Missing environment variable SEATVERSE_JWT_SECRET")
    return secret_key


@dataclass(frozen=True)
class TokenClaims:
    user_id: int
    role: str
    expiration: int


def issue_token(
    user_id: int,
    role: str,
    time_to_live_seconds: int = _TOKEN_TIME_TO_LIVE_SECONDS,
) -> str:
    issued_at = int(time.time())
    payload: dict[str, object] = {
        "sub": str(user_id),
        "role": role,
        "iat": issued_at,
        "exp": issued_at + time_to_live_seconds,
    }
    return jwt.encode(payload, _get_jwt_secret_key(), _JWT_ALGORITHM)


def parse_token(token: str) -> TokenClaims | None:
    try:
        claims = jwt.decode(
            token,
            _get_jwt_secret_key(),
            algorithms=[_JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError:
        return None
    subject = claims.get("sub")
    role = claims.get("role")
    expiration = claims.get("exp")
    if not isinstance(subject, str):
        return None
    try:
        user_id = int(subject)
    except ValueError:
        return None
    if not isinstance(role, str):
        return None
    if not isinstance(expiration, int) or isinstance(expiration, bool):
        return None
    return TokenClaims(user_id=user_id, role=role, expiration=expiration)
