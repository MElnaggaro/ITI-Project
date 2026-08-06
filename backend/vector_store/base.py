"""Vector-store contract; implementation is owned by Phases 13 and 14."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID


class TenantVectorStore(Protocol):
    """Future retrieval calls must require tenant and knowledge-base filters."""

    async def search(
        self,
        tenant_id: UUID,
        knowledge_base_ids: tuple[UUID, ...],
        query: str,
    ) -> object:
        """Retrieve only document evidence allowed to the active tenant."""
