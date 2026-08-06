"""Repository for MessageCitation entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.citation import MessageCitation
from repositories.base import BaseTenantRepository, to_uuid


class CitationRepository(BaseTenantRepository[MessageCitation]):
    """Repository operations for tenant-scoped MessageCitation entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, MessageCitation)

    def create(self, citation: MessageCitation) -> MessageCitation:
        """Persist a new MessageCitation record."""
        self.session.add(citation)
        self.session.flush()
        return citation

    def list_by_message(self, tenant_id: UUID | str, message_id: UUID | str) -> list[MessageCitation]:
        """Fetch all citations for a specific message."""
        t_id = to_uuid(tenant_id)
        m_id = to_uuid(message_id)
        stmt = (
            select(MessageCitation)
            .where(MessageCitation.tenant_id == t_id)
            .where(MessageCitation.message_id == m_id)
        )
        return list(self.session.scalars(stmt).all())
