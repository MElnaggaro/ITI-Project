"""Pydantic schemas for Chat request, response, and citations."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

IntentType = Literal["general", "database", "document", "hybrid", "clarification"]


class ChatRequest(BaseModel):
    """Chat input request model."""

    message: str = Field(..., min_length=1, description="User question or prompt")
    conversation_id: UUID | None = None
    connection_ids: list[UUID] = Field(default_factory=list)
    knowledge_base_ids: list[UUID] = Field(default_factory=list)


class SourceCitation(BaseModel):
    """Citation provenance linking answer back to SQL queries or document chunks."""

    citation_type: str  # 'sql' or 'document'
    title: str
    source_reference: str
    page_number: int | None = None
    relevance_score: float | None = None


class ChatResponse(BaseModel):
    """Chat answer response envelope."""

    message_id: UUID
    conversation_id: UUID
    answer: str
    detected_intent: IntentType
    sources_used: list[SourceCitation] = Field(default_factory=list)
    generated_sql: str | None = None
    execution_time_ms: int | None = None
    row_count: int | None = None
