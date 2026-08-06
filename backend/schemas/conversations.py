"""Pydantic schemas for Conversation management."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from schemas.messages import MessageResponse


class ConversationCreate(BaseModel):
    """Payload to create a new conversation."""

    title: str | None = Field(None, max_length=500)
    active_connection_ids: list[UUID] = Field(default_factory=list)
    active_knowledge_base_ids: list[UUID] = Field(default_factory=list)
    settings: dict[str, Any] = Field(default_factory=dict)


class ConversationResponse(BaseModel):
    """Conversation summary output model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    user_id: UUID
    title: str | None = None
    status: str
    active_connection_ids: list[UUID]
    active_knowledge_base_ids: list[UUID]
    settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime | None = None


class ConversationDetailResponse(ConversationResponse):
    """Conversation detail output model containing message history."""

    messages: list[MessageResponse] = Field(default_factory=list)
