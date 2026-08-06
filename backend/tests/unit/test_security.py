"""Unit tests for Argon2id hashing and PyJWT token security operations."""

from datetime import timedelta
from uuid import uuid4

import pytest

from app.exceptions import AuthenticationError
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_argon2id_password_hashing_and_verification():
    """Verify password hashing with Argon2id and correct password matching."""
    plain = "SuperSecurePassword123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert hashed.startswith("$argon2id$")
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword123!", hashed) is False
    assert verify_password(plain, None) is False
    assert verify_password(plain, "invalid-hash") is False


def test_create_and_decode_access_token():
    """Verify access token creation and decoding."""
    tenant_id = uuid4()
    user_id = uuid4()

    token = create_access_token(
        tenant_id=tenant_id,
        user_id=user_id,
        is_tenant_admin=True,
    )
    assert isinstance(token, str)

    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["is_tenant_admin"] is True
    assert payload["token_type"] == "access"


def test_create_and_decode_refresh_token():
    """Verify refresh token creation and token_type separation."""
    tenant_id = uuid4()
    user_id = uuid4()

    token, jti = create_refresh_token(
        tenant_id=tenant_id,
        user_id=user_id,
        is_tenant_admin=False,
    )
    assert isinstance(token, str)
    assert isinstance(jti, str)

    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["is_tenant_admin"] is False
    assert payload["token_type"] == "refresh"
    assert payload["jti"] == jti

    # Attempting to decode refresh token as access token should fail
    with pytest.raises(AuthenticationError) as exc_info:
        decode_token(token, expected_type="access")
    assert exc_info.value.code == "invalid_token_type"


def test_expired_token_handling():
    """Verify decoding an expired token raises AuthenticationError with token_expired code."""
    tenant_id = uuid4()
    user_id = uuid4()

    token = create_access_token(
        tenant_id=tenant_id,
        user_id=user_id,
        is_tenant_admin=False,
        expires_delta=timedelta(seconds=-10),
    )

    with pytest.raises(AuthenticationError) as exc_info:
        decode_token(token, expected_type="access")
    assert exc_info.value.code == "token_expired"
