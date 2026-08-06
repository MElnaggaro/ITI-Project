"""Pydantic schemas and dataclasses for Knowledge Base management and evidence retrieval."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeBaseCreate(BaseModel):
    """Payload to create a new knowledge base."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    embedding_model: str | None = Field("bge-large-en-v1.5", description="Target 1024-dimension embedding model")
    chunking_config: dict[str, Any] = Field(default_factory=dict)


class KnowledgeBaseResponse(BaseModel):
    """Knowledge base metadata output model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_by: UUID | None = None
    name: str
    description: str | None = None
    embedding_model: str | None = None
    chunking_config: dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class RetrievedEvidence:
    """Citation-ready document evidence excerpt retrieved from vector store."""

    chunk_id: UUID
    file_id: UUID
    file_name: str
    score: float
    excerpt: str
    page_number: int | None = None
    section_title: str | None = None
