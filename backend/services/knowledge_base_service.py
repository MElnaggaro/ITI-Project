"""Knowledge Base Service for tenant-scoped KB creation and listing."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.knowledge_base import KnowledgeBase
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from schemas.knowledge_bases import KnowledgeBaseCreate, KnowledgeBaseResponse


class KnowledgeBaseService:
    """Service managing tenant Knowledge Bases."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.repo = KnowledgeBaseRepository(session)

    def create_kb(
        self,
        context: TenantContext,
        data: KnowledgeBaseCreate,
    ) -> KnowledgeBaseResponse:
        """Create a new tenant-scoped Knowledge Base."""
        existing = self.repo.get_by_name(context.tenant_id, data.name)
        if existing:
            raise ValueError(f"Knowledge Base with name '{data.name}' already exists in this tenant.")

        kb = KnowledgeBase(
            tenant_id=context.tenant_id,
            created_by=context.user_id,
            name=data.name,
            description=data.description,
            embedding_model=data.embedding_model,
            chunking_config=data.chunking_config,
        )

        created = self.repo.create(kb)
        return KnowledgeBaseResponse.model_validate(created)

    def list_kbs(self, tenant_id: UUID) -> list[KnowledgeBaseResponse]:
        """List all Knowledge Bases for a tenant."""
        kbs = self.repo.list_by_tenant(tenant_id)
        return [KnowledgeBaseResponse.model_validate(kb) for kb in kbs]

    def get_kb(self, tenant_id: UUID, kb_id: UUID) -> KnowledgeBaseResponse | None:
        """Get Knowledge Base metadata by ID."""
        kb = self.repo.get_by_id(tenant_id, kb_id)
        if not kb:
            return None
        return KnowledgeBaseResponse.model_validate(kb)
