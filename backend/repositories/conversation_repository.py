"""Repository for Conversation entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.conversation import Conversation
from repositories.base import BaseTenantRepository, to_uuid


class ConversationRepository(BaseTenantRepository[Conversation]):
    """Repository operations for tenant-scoped Conversation entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Conversation)

    def create(self, conversation: Conversation) -> Conversation:
        """Persist a new Conversation record."""
        self.session.add(conversation)
        self.session.flush()
        return conversation

    def delete(self, tenant_id: UUID | str, conversation_id: UUID | str) -> bool:
        """Delete a Conversation record from platform database."""
        conv = self.get_by_id(tenant_id, conversation_id)
        if not conv:
            return False
        self.session.delete(conv)
        self.session.flush()
        return True
