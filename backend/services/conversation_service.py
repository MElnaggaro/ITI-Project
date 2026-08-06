"""Conversation Service handling tenant-scoped session CRUD and message history retrieval."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.conversation import Conversation
from repositories.conversation_repository import ConversationRepository
from repositories.message_repository import MessageRepository
from schemas.conversations import ConversationCreate, ConversationDetailResponse, ConversationResponse
from schemas.messages import MessageResponse


class ConversationService:
    """Service managing tenant chat conversations."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.msg_repo = MessageRepository(session)

    def create_conversation(
        self,
        context: TenantContext,
        data: ConversationCreate,
    ) -> ConversationResponse:
        """Create a new tenant-scoped conversation."""
        conv = Conversation(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            title=data.title or "New Conversation",
            status="active",
            active_connection_ids=[str(cid) for cid in data.active_connection_ids],
            active_knowledge_base_ids=[str(kbid) for kbid in data.active_knowledge_base_ids],
            settings=data.settings,
        )

        created = self.conv_repo.create(conv)
        return ConversationResponse.model_validate(created)

    def list_conversations(self, tenant_id: UUID) -> list[ConversationResponse]:
        """List all conversations for a tenant."""
        convs = self.conv_repo.list_by_tenant(tenant_id)
        return [ConversationResponse.model_validate(c) for c in convs]

    def get_conversation_detail(self, context: TenantContext, conversation_id: UUID) -> ConversationDetailResponse | None:
        """Get conversation metadata and its message history."""
        conv = self.conv_repo.get_by_id(context.tenant_id, conversation_id)
        if not conv:
            return None

        messages = self.msg_repo.list_by_conversation(context.tenant_id, conversation_id)
        msg_responses = [MessageResponse.model_validate(m) for m in messages]

        resp = ConversationDetailResponse.model_validate(conv)
        resp.messages = msg_responses
        return resp

    def delete_conversation(self, tenant_id: UUID, conversation_id: UUID) -> bool:
        """Delete a conversation and its messages."""
        return self.conv_repo.delete(tenant_id, conversation_id)
