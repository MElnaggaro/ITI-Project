"""Pydantic schemas for File upload and lifecycle operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class FileResponse(BaseModel):
    """File metadata response model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID | None = None
    uploaded_by: UUID | None = None
    original_name: str
    stored_name: str
    storage_path: str
    mime_type: str | None = None
    extension: str | None = None
    file_size_bytes: int | None = None
    checksum: str | None = None
    processing_status: str
    processing_error: str | None = None
    page_count: int | None = None
    extracted_text_length: int | None = None
    metadata_: dict[str, Any] = {}
    created_at: datetime
    processed_at: datetime | None = None


class FileAssociateRequest(BaseModel):
    """Payload to associate a file with a knowledge base."""

    file_id: UUID
