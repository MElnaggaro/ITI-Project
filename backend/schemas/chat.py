"""Pydantic schemas for Chat request, response, and citations (Section 9 contract)."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

IntentType = Literal["general", "database", "document", "hybrid", "clarification"]


class ChatRequest(BaseModel):
    """Chat input request model matching Section 9 contract."""

    message: str = Field(..., min_length=1, description="User question or prompt")
    conversation_id: UUID | None = None
    database_connection_ids: list[UUID] = Field(default_factory=list)
    knowledge_base_ids: list[UUID] = Field(default_factory=list)
    stream: bool = False


class SQLDetail(BaseModel):
    """Nested SQL execution detail matching Section 9 response contract."""

    query_execution_id: UUID | None = None
    query: str | None = None
    row_count: int | None = None


class Citation(BaseModel):
    """Source citation matching Section 9 response contract shapes."""

    type: str  # 'document' or 'database'
    file_name: str | None = None
    page: int | None = None
    table: str | None = None


class ChatResponse(BaseModel):
    """Chat answer response envelope matching Section 9 contract."""

    message_id: UUID
    conversation_id: UUID
    answer: str
    intent: IntentType
    sources_used: list[str] = Field(default_factory=list)
    sql: SQLDetail | None = None
    citations: list[Citation] = Field(default_factory=list)


# Internal citation model used by CitationService (not part of Section 9 contract)
class SourceCitation(BaseModel):
    """Internal citation provenance linking answer back to SQL queries or document chunks."""

    citation_type: str  # 'sql' or 'document'
    title: str
    source_reference: str
    page_number: int | None = None
    relevance_score: float | None = None
