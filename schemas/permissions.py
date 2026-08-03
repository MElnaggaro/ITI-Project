"""Pydantic schemas for Table and Column permission grants."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

MaskType = Literal["redact", "last4", "hash"]


class TablePermissionCreate(BaseModel):
    """Payload to create a table permission grant."""

    connection_id: UUID
    table_id: UUID
    role_id: UUID | None = None
    user_id: UUID | None = None
    can_read: bool = True
    can_insert: bool = False
    can_update: bool = False
    can_delete: bool = False
    row_filter: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_subject(self) -> TablePermissionCreate:
        if (self.role_id is not None and self.user_id is not None) or (
            self.role_id is None and self.user_id is None
        ):
            raise ValueError("Table permission must name exactly one of role_id or user_id.")
        return self


class TablePermissionUpdate(BaseModel):
    """Payload to update an existing table permission grant."""

    can_read: bool = True
    can_insert: bool = False
    can_update: bool = False
    can_delete: bool = False
    row_filter: dict[str, Any] = Field(default_factory=dict)


class ColumnPermissionRule(BaseModel):
    """Granular column permission specification."""

    column_id: UUID
    can_read: bool = True
    can_filter: bool = True
    can_aggregate: bool = True
    mask_type: MaskType | None = None


class ColumnPermissionResponse(BaseModel):
    """Column permission output model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    table_permission_id: UUID
    column_id: UUID
    can_read: bool
    can_filter: bool
    can_aggregate: bool
    mask_type: MaskType | None = None


class TablePermissionResponse(BaseModel):
    """Table permission output model."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    connection_id: UUID
    table_id: UUID
    role_id: UUID | None = None
    user_id: UUID | None = None
    can_read: bool
    can_insert: bool
    can_update: bool
    can_delete: bool
    row_filter: dict[str, Any]
    created_at: datetime
    column_permissions: list[ColumnPermissionResponse] = Field(default_factory=list)
