"""Object-storage contract; implementation is owned by Phase 11."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class TenantObjectStorage(Protocol):
    """Storage paths must derive from trusted tenant and resource identifiers."""

    def object_key(self, tenant_id: UUID, resource_id: UUID, name: str) -> str:
        """Build a tenant-qualified key without accepting arbitrary prefixes."""
