"""Request-specific ResolvedSchema dataclass models for Text-to-SQL generation and validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import sqlglot.expressions as exp


@dataclass(frozen=True, slots=True)
class ResolvedColumn:
    """Column contract details exposed to the text-to-SQL agent."""

    column_id: UUID
    column_name: str
    data_type: str
    is_primary_key: bool
    is_foreign_key: bool
    can_read: bool
    can_filter: bool
    can_aggregate: bool
    mask_type: str | None = None


@dataclass(frozen=True, slots=True)
class ResolvedRelationship:
    """Foreign key relationship connecting two permitted tables."""

    source_table_id: UUID
    source_table_name: str
    source_column_name: str
    target_table_id: UUID
    target_table_name: str
    target_column_name: str


@dataclass(slots=True)
class ResolvedTable:
    """Table contract details exposed to the text-to-SQL agent."""

    table_id: UUID
    schema_name: str
    table_name: str
    table_type: str
    description: str | None
    can_read: bool
    can_insert: bool
    can_update: bool
    can_delete: bool
    columns: dict[str, ResolvedColumn] = field(default_factory=dict)
    primary_key_columns: list[str] = field(default_factory=list)
    compiled_row_filters: list[exp.Expression] = field(default_factory=list)
    raw_row_filters: list[dict[str, Any]] = field(default_factory=list)


@dataclass(slots=True)
class ResolvedSchema:
    """Request-specific, short-lived schema context for text-to-SQL generation."""

    tenant_id: UUID
    user_id: UUID
    connection_id: UUID
    database_type: str
    tables: dict[str, ResolvedTable] = field(default_factory=dict)
    relationships: list[ResolvedRelationship] = field(default_factory=list)

    def is_empty(self) -> bool:
        """Return True if no readable tables exist for caller."""
        return len(self.tables) == 0
