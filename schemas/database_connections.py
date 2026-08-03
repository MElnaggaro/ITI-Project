"""Pydantic schemas for DatabaseConnection management."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DatabaseConnectionCreate(BaseModel):
    """Payload to create a database connection."""

    name: str = Field(..., min_length=1, max_length=200)
    database_type: str = Field(..., description="Source database dialect (e.g. postgresql)")
    host: str | None = None
    port: int | None = Field(None, ge=1, le=65535)
    database_name: str | None = None
    username: str | None = None
    password: str | None = Field(None, description="Plaintext password to be encrypted")
    connection_string: str | None = Field(None, description="Plaintext connection string to be encrypted")
    ssl_enabled: bool = False
    ssl_settings: dict[str, Any] = Field(default_factory=dict)
    connection_options: dict[str, Any] = Field(default_factory=dict)


class DatabaseConnectionUpdate(BaseModel):
    """Payload to update an existing database connection."""

    name: str = Field(..., min_length=1, max_length=200)
    host: str | None = None
    port: int | None = Field(None, ge=1, le=65535)
    database_name: str | None = None
    username: str | None = None
    password: str | None = Field(None, description="Updated plaintext password to be encrypted")
    connection_string: str | None = Field(None, description="Updated plaintext connection string to be encrypted")
    ssl_enabled: bool = False
    ssl_settings: dict[str, Any] = Field(default_factory=dict)
    connection_options: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class DatabaseConnectionResponse(BaseModel):
    """Database connection metadata response with redacted secrets."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    created_by: UUID | None = None
    name: str
    database_type: str
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    username: str | None = None
    ssl_enabled: bool
    ssl_settings: dict[str, Any]
    connection_options: dict[str, Any]
    status: str
    last_tested_at: datetime | None = None
    last_test_message: str | None = None
    schema_sync_status: str | None = None
    last_schema_sync_at: datetime | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ConnectionTestResponse(BaseModel):
    """Connectivity probe result response."""

    connection_id: UUID
    status: str
    message: str
    tested_at: datetime
