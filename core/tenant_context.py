"""Trusted tenant context types; token resolution is implemented in Phase 03."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.exceptions import FeatureNotReadyError


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Server-derived tenant and user identity, never client-selected."""

    tenant_id: UUID
    user_id: UUID


def tenant_context_not_ready() -> None:
    """Fail closed until authenticated tenant resolution is available."""

    raise FeatureNotReadyError(
        code="tenant_context_not_configured",
        public_message="Tenant context is not configured yet.",
        status_code=503,
    )
