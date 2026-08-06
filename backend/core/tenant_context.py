"""Trusted tenant context type derived from authenticated requests."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TenantContext:
    """Server-derived, immutable tenant and user identity, never client-supplied."""

    tenant_id: UUID
    user_id: UUID
    is_tenant_admin: bool = False
    request_id: str | None = None
