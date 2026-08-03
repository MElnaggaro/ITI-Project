"""Shared request dependencies providing database session and authenticated TenantContext."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generator
from uuid import UUID

from fastapi import Depends, Header, Request
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.exceptions import AuthenticationError, AuthorizationError
from core.security import decode_token
from core.tenant_context import TenantContext
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository

# Lazy engine initialization
_engine = None
_SessionFactory = None


def get_engine():
    global _engine, _SessionFactory
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.application_database_url, pool_pre_ping=True)
        _SessionFactory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_db() -> Generator[Session, None, None]:
    """Provide a database session for request lifecycle handling."""
    get_engine()
    assert _SessionFactory is not None
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Trusted request correlation metadata."""

    request_id: str
    tenant_id: UUID | None = None
    user_id: UUID | None = None


def get_app_settings() -> Settings:
    """Expose the cached typed configuration through FastAPI dependency injection."""
    return get_settings()


def get_request_context(request: Request) -> RequestContext:
    """Return correlation metadata."""
    request_id = getattr(request.state, "request_id", "unknown-request-id")
    return RequestContext(request_id=request_id)


def get_current_tenant_context(
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> TenantContext:
    """Authenticate bearer token and return an immutable TenantContext."""
    request_id = getattr(request.state, "request_id", "unknown-request-id")

    if not authorization:
        raise AuthenticationError(
            public_message="Missing Authorization header.",
            code="missing_authorization",
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise AuthenticationError(
            public_message="Invalid Authorization header format. Expected 'Bearer <token>'.",
            code="invalid_authorization_header",
        )

    token = parts[1]
    payload = decode_token(token, expected_type="access")

    user_id_str = payload.get("sub")
    tenant_id_str = payload.get("tenant_id")

    if not user_id_str or not tenant_id_str:
        raise AuthenticationError(
            public_message="Invalid token claims.",
            code="invalid_claims",
        )

    user_id = UUID(user_id_str)
    tenant_id = UUID(tenant_id_str)

    # Validate active tenant status
    tenant_repo = TenantRepository(db)
    tenant = tenant_repo.get_by_id(tenant_id)
    if not tenant or tenant.status != "active":
        raise AuthenticationError(
            public_message="Tenant is inactive or invalid.",
            code="tenant_inactive",
        )

    # Validate active user status
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(tenant_id, user_id)
    if not user or user.status != "active":
        raise AuthenticationError(
            public_message="User is inactive or invalid.",
            code="user_inactive",
        )

    return TenantContext(
        tenant_id=tenant_id,
        user_id=user_id,
        is_tenant_admin=user.is_tenant_admin,
        request_id=request_id,
    )


def require_authenticated_context(
    context: TenantContext = Depends(get_current_tenant_context),
) -> TenantContext:
    """Require valid authenticated TenantContext."""
    return context


def require_tenant_admin(
    context: TenantContext = Depends(get_current_tenant_context),
) -> TenantContext:
    """Enforce tenant administrator role on protected endpoints."""
    if not context.is_tenant_admin:
        raise AuthorizationError(
            public_message="Tenant administrator privileges required.",
            code="tenant_admin_required",
            status_code=403,
        )
    return context
