"""Authentication service orchestrating login, token refresh, and user profile resolution."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.config import get_settings
from app.exceptions import AuthenticationError
from core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)

from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from schemas.auth import LoginRequest, RefreshTokenRequest, TokenResponse, UserMeResponse
from services.redis_service import get_redis_auth_store


class AuthService:
    """Service handling authentication lifecycle and identity validation."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.tenant_repo = TenantRepository(session)
        self.user_repo = UserRepository(session)
        self.auth_store = get_redis_auth_store()
        self.settings = get_settings()

    def login(self, request: LoginRequest, client_ip: str = "unknown") -> TokenResponse:
        """Authenticate user by tenant_code, email, and password."""
        # 1. Rate limiting check
        rate_key = f"{request.tenant_code}:{request.email}:{client_ip}"
        if not self.auth_store.check_rate_limit(rate_key, max_attempts=10, window_seconds=300):
            raise AuthenticationError(
                public_message="Too many authentication attempts. Please try again later.",
                code="rate_limit_exceeded",
                status_code=429,
            )

        # 2. Look up tenant by code
        tenant = self.tenant_repo.get_by_code(request.tenant_code)
        if not tenant or tenant.status != "active":
            raise AuthenticationError(
                public_message="Invalid credentials or inactive account.",
                code="invalid_credentials",
            )

        # 3. Look up user by (tenant_id, email)
        user = self.user_repo.get_by_tenant_and_email(tenant.id, request.email)
        if not user or user.status != "active":
            raise AuthenticationError(
                public_message="Invalid credentials or inactive account.",
                code="invalid_credentials",
            )

        # 4. Verify password hash using Argon2id
        if not verify_password(request.password, user.password_hash):
            raise AuthenticationError(
                public_message="Invalid credentials or inactive account.",
                code="invalid_credentials",
            )

        # 5. Issue access and refresh tokens
        access_token = create_access_token(
            tenant_id=tenant.id,
            user_id=user.id,
            is_tenant_admin=user.is_tenant_admin,
        )
        refresh_token, refresh_jti = create_refresh_token(
            tenant_id=tenant.id,
            user_id=user.id,
            is_tenant_admin=user.is_tenant_admin,
        )

        # 6. Store refresh token JTI in Redis
        ttl_seconds = self.settings.jwt_refresh_token_days * 86400
        self.auth_store.store_refresh_token(
            jti=refresh_jti,
            user_id=user.id,
            tenant_id=tenant.id,
            ttl_seconds=ttl_seconds,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.jwt_access_token_minutes * 60,
        )

    def refresh(self, request: RefreshTokenRequest) -> TokenResponse:
        """Rotate refresh token and issue new token pair."""
        # 1. Decode refresh token JWT
        payload = decode_token(request.refresh_token, expected_type="refresh")

        jti = payload.get("jti")
        user_id_str = payload.get("sub")
        tenant_id_str = payload.get("tenant_id")

        if not jti or not user_id_str or not tenant_id_str:
            raise AuthenticationError(
                public_message="Invalid refresh token claims.",
                code="invalid_refresh_token",
            )

        # 2. Check token exists in Redis store
        if not self.auth_store.is_refresh_token_valid(jti):
            raise AuthenticationError(
                public_message="Refresh token is expired or has been revoked.",
                code="token_revoked",
            )

        user_id = UUID(user_id_str)
        tenant_id = UUID(tenant_id_str)

        # 3. Check tenant and user active status in database
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant or tenant.status != "active":
            self.auth_store.revoke_refresh_token(jti)
            raise AuthenticationError(
                public_message="Tenant is inactive.",
                code="tenant_inactive",
            )

        user = self.user_repo.get_by_id(tenant_id, user_id)
        if not user or user.status != "active":
            self.auth_store.revoke_refresh_token(jti)
            raise AuthenticationError(
                public_message="User is inactive.",
                code="user_inactive",
            )

        # 4. Revoke old refresh token JTI (atomic rotation)
        self.auth_store.revoke_refresh_token(jti)

        # 5. Issue new access and refresh tokens
        new_access = create_access_token(
            tenant_id=tenant.id,
            user_id=user.id,
            is_tenant_admin=user.is_tenant_admin,
        )
        new_refresh, new_jti = create_refresh_token(
            tenant_id=tenant.id,
            user_id=user.id,
            is_tenant_admin=user.is_tenant_admin,
        )

        # 6. Store new refresh token JTI
        ttl_seconds = self.settings.jwt_refresh_token_days * 86400
        self.auth_store.store_refresh_token(
            jti=new_jti,
            user_id=user.id,
            tenant_id=tenant.id,
            ttl_seconds=ttl_seconds,
        )

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=self.settings.jwt_access_token_minutes * 60,
        )

    def get_user_me(self, tenant_id: UUID, user_id: UUID) -> UserMeResponse:
        """Fetch current user identity and tenant metadata for GET /api/auth/me."""
        tenant = self.tenant_repo.get_by_id(tenant_id)
        if not tenant:
            raise AuthenticationError(
                public_message="Tenant not found.",
                code="tenant_not_found",
            )

        user = self.user_repo.get_by_id(tenant_id, user_id)
        if not user:
            raise AuthenticationError(
                public_message="User not found.",
                code="user_not_found",
            )

        return UserMeResponse(
            id=user.id,
            tenant_id=tenant.id,
            tenant_code=tenant.code,
            tenant_name=tenant.name,
            email=user.email,
            full_name=user.full_name,
            is_tenant_admin=user.is_tenant_admin,
            status=user.status,
        )
