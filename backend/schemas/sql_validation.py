"""Pydantic schemas and dataclasses for SQL validation output."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ValidatedQueryPlan:
    """Immutable, AST-validated, read-only query plan ready for safe execution."""

    generated_sql: str
    normalized_sql: str
    query_type: str  # 'select', 'with'
    validation_status: str  # 'valid', 'invalid'
    validation_errors: list[str] = field(default_factory=list)
    referenced_tables: list[str] = field(default_factory=list)
    referenced_columns: list[str] = field(default_factory=list)
    applied_row_filters: list[dict[str, Any]] = field(default_factory=list)
    final_sql: str | None = None
