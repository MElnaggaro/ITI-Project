"""Repository for Message entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.message import Message
from repositories.base import BaseTenantRepository, to_uuid


class MessageRepository(BaseTenantRepository[Message]):
    """Repository operations for tenant-scoped Message entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Message)

    def create(self, message: Message) -> Message:
        """Persist a new Message record."""
        self.session.add(message)
        self.session.flush()
        return message

    def list_by_conversation(self, tenant_id: UUID | str, conversation_id: UUID | str) -> list[Message]:
        """Fetch all messages for a specific conversation in chronological order."""
        t_id = to_uuid(tenant_id)
        c_id = to_uuid(conversation_id)
        stmt = (
            select(Message)
            .where(Message.tenant_id == t_id)
            .where(Message.conversation_id == c_id)
            .order_by(Message.created_at)
        )
        return list(self.session.scalars(stmt).all())
