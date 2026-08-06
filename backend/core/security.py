"""Security helper module providing Argon2id password hashing and JWT token operations."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from uuid import UUID, uuid4

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
import jwt

from app.config import get_settings
from app.exceptions import AuthenticationError

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash password using Argon2id with safe production parameters."""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    """Constant-time-compatible Argon2id password verification."""
    if not hashed_password:
        return False
    try:
        return _ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, InvalidHashError, VerificationError):
        return False


def get_jwt_secret() -> str:
    """Retrieve configured JWT secret key or safe test fallback."""
    settings = get_settings()
    if settings.jwt_secret_key:
        return settings.jwt_secret_key.get_secret_value()
    if settings.app_environment == "test":
        return "test-secret-key-32-chars-long-minimum!"
    raise ValueError("JWT_SECRET_KEY must be configured")


def create_access_token(
    tenant_id: UUID,
    user_id: UUID,
    is_tenant_admin: bool,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token containing trusted identity claims."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(minutes=settings.jwt_access_token_minutes)
    expire = now + delta

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "is_tenant_admin": is_tenant_admin,
        "token_type": "access",
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=settings.jwt_algorithm)


def create_refresh_token(
    tenant_id: UUID,
    user_id: UUID,
    is_tenant_admin: bool,
    expires_delta: timedelta | None = None,
) -> tuple[str, str]:
    """Create a signed JWT refresh token and return (token_string, jti)."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    delta = expires_delta or timedelta(days=settings.jwt_refresh_token_days)
    expire = now + delta
    jti = str(uuid4())

    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "is_tenant_admin": is_tenant_admin,
        "token_type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    token = jwt.encode(payload, get_jwt_secret(), algorithm=settings.jwt_algorithm)
    return token, jti


def decode_token(token: str, expected_type: str = "access") -> dict:
    """Validate token signature, expiration, and token_type claim."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret(),
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationError(
            public_message="Token has expired.",
            code="token_expired",
        )
    except jwt.PyJWTError:
        raise AuthenticationError(
            public_message="Invalid authentication token.",
            code="invalid_token",
        )

    if payload.get("token_type") != expected_type:
        raise AuthenticationError(
            public_message="Invalid token type.",
            code="invalid_token_type",
        )
    return payload
