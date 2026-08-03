"""Repository contracts that make tenant scope explicit before resource lookup."""

from __future__ import annotations

from typing import Protocol, TypeVar
from uuid import UUID

EntityT = TypeVar("EntityT")


class TenantScopedRepository(Protocol[EntityT]):
    """Every future repository operation must accept trusted tenant scope."""

    async def get_by_id(self, tenant_id: UUID, resource_id: UUID) -> EntityT | None:
        """Return a resource only when it belongs to the supplied tenant."""
