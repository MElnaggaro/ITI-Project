"""Pydantic schemas for Role management."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleCreate(BaseModel):
    """Payload to create a new role."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class RoleUpdate(BaseModel):
    """Payload to update an existing role."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class RoleResponse(BaseModel):
    """Role output payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    description: str | None = None
    created_at: datetime


class UserRolesAssignment(BaseModel):
    """Payload to replace user role assignments."""

    role_ids: list[UUID] = Field(..., description="List of role IDs belonging to the tenant")
