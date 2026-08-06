"""Pydantic schemas and dataclasses for Query Execution and transient result envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True, slots=True)
class ExecutionResultEnvelope:
    """Transient result envelope returned to the chat orchestrator."""

    execution_id: UUID
    columns: list[str]
    rows: list[dict[str, Any]]
    returned_row_count: int
    execution_time_ms: int
    is_truncated: bool = False


class QueryExecutionResponse(BaseModel):
    """QueryExecution database record response model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    conversation_id: UUID | None = None
    message_id: UUID | None = None
    connection_id: UUID
    generated_sql: str
    normalized_sql: str | None = None
    query_type: str | None = None
    validation_status: str
    validation_errors: list[str] = Field(default_factory=list)
    applied_row_filters: dict[str, Any] = Field(default_factory=dict)
    referenced_tables: list[str] = Field(default_factory=list)
    referenced_columns: list[str] = Field(default_factory=list)
    execution_status: str | None = None
    execution_time_ms: int | None = None
    returned_row_count: int | None = None
    result_preview: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
