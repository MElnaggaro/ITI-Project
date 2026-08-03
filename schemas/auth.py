"""Pydantic schemas for authentication requests and responses."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    """Client login request payload."""

    tenant_code: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Authentication token response payload."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request payload."""

    refresh_token: str = Field(..., min_length=1)


class UserMeResponse(BaseModel):
    """Authenticated user profile representation for GET /api/auth/me."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    tenant_code: str
    tenant_name: str
    email: str
    full_name: str | None = None
    is_tenant_admin: bool
    status: str
