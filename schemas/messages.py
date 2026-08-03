"""Pydantic schemas for Message persistence and response."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageResponse(BaseModel):
    """Message output response model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    conversation_id: UUID
    parent_message_id: UUID | None = None
    role: str
    message_type: str
    content: str
    structured_content: dict[str, Any] | None = None
    detected_intent: str | None = None
    selected_sources: list[dict[str, Any]] = Field(default_factory=list)
    model_name: str | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_ms: int | None = None
    status: str
    error_message: str | None = None
    created_at: datetime
