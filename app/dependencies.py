"""Shared request dependencies; authentication resolution begins in Phase 03."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Request

from app.config import Settings, get_settings
from app.exceptions import FeatureNotReadyError


@dataclass(frozen=True, slots=True)
class RequestContext:
    """Trusted request metadata; tenant identity is intentionally unavailable yet."""

    request_id: str
    tenant_id: UUID | None = None
    user_id: UUID | None = None


def get_app_settings() -> Settings:
    """Expose the cached typed configuration through FastAPI dependency injection."""

    return get_settings()


def get_request_context(request: Request) -> RequestContext:
    """Return correlation metadata without accepting client-controlled tenant identity."""

    return RequestContext(request_id=request.state.request_id)


def require_authenticated_context() -> RequestContext:
    """Block use of tenant/user context until Phase 03 installs authentication."""

    raise FeatureNotReadyError(
        code="authentication_not_configured",
        public_message="Authentication is not configured yet.",
        status_code=503,
    )
