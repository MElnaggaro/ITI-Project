"""Repository for KnowledgeBase entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.knowledge_base import KnowledgeBase
from repositories.base import BaseTenantRepository, to_uuid


class KnowledgeBaseRepository(BaseTenantRepository[KnowledgeBase]):
    """Repository operations for tenant-scoped KnowledgeBase entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, KnowledgeBase)

    def get_by_name(self, tenant_id: UUID | str, name: str) -> KnowledgeBase | None:
        """Fetch KnowledgeBase by (tenant_id, name) unique constraint."""
        t_id = to_uuid(tenant_id)
        stmt = (
            select(KnowledgeBase)
            .where(KnowledgeBase.tenant_id == t_id)
            .where(KnowledgeBase.name == name)
        )
        return self.session.scalar(stmt)

    def create(self, kb: KnowledgeBase) -> KnowledgeBase:
        """Persist a new KnowledgeBase entity."""
        self.session.add(kb)
        self.session.flush()
        return kb
