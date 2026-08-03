"""Pydantic schemas and dataclasses for candidate SQL generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class SQLGenerationRequest(BaseModel):
    """Internal text-to-SQL generation request payload."""

    connection_id: UUID
    user_prompt: str


@dataclass(frozen=True, slots=True)
class SQLCandidate:
    """Generated candidate SQL output and generation metadata."""

    candidate_sql: str
    model_name: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    referenced_table_candidates: list[str] | None = None
