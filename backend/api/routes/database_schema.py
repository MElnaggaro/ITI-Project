"""Cached schema and table inspection API endpoints protected by require_tenant_admin."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_tenant_admin
from core.tenant_context import TenantContext
from models.database_column import DatabaseColumn
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseSchema
from models.database_table import DatabaseTable

router = APIRouter(prefix="/database-connections", tags=["Database Schema"])


@router.get("/{id}/schemas", response_model=list[dict[str, Any]])
def list_cached_schemas(
    id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached schemas for a tenant connection."""
    conn = db.scalar(
        select(DatabaseConnection)
        .where(DatabaseConnection.tenant_id == context.tenant_id)
        .where(DatabaseConnection.id == id)
    )
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found.")

    schemas = list(
        db.scalars(
            select(DatabaseSchema)
            .where(DatabaseSchema.connection_id == conn.id)
            .order_by(DatabaseSchema.schema_name)
        ).all()
    )

    return [
        {
            "id": str(s.id),
            "tenant_id": str(s.tenant_id),
            "connection_id": str(s.connection_id),
            "schema_name": s.schema_name,
            "description": s.description,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in schemas
    ]


@router.get("/{id}/tables", response_model=list[dict[str, Any]])
def list_cached_tables(
    id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    """List cached tables and columns for a tenant connection."""
    conn = db.scalar(
        select(DatabaseConnection)
        .where(DatabaseConnection.tenant_id == context.tenant_id)
        .where(DatabaseConnection.id == id)
    )
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found.")

    tables = list(
        db.scalars(
            select(DatabaseTable)
            .where(DatabaseTable.connection_id == conn.id)
            .order_by(DatabaseTable.table_name)
        ).all()
    )

    result = []
    for t in tables:
        cols = list(
            db.scalars(
                select(DatabaseColumn)
                .where(DatabaseColumn.table_id == t.id)
                .order_by(DatabaseColumn.ordinal_position)
            ).all()
        )
        col_list = [
            {
                "id": str(c.id),
                "column_name": c.column_name,
                "data_type": c.data_type,
                "ordinal_position": c.ordinal_position,
                "is_nullable": c.is_nullable,
                "is_primary_key": c.is_primary_key,
                "is_foreign_key": c.is_foreign_key,
                "is_sensitive": c.is_sensitive,
                "referenced_schema": c.referenced_schema,
                "referenced_table": c.referenced_table,
                "referenced_column": c.referenced_column,
            }
            for c in cols
        ]
        result.append(
            {
                "id": str(t.id),
                "tenant_id": str(t.tenant_id),
                "connection_id": str(t.connection_id),
                "schema_id": str(t.schema_id) if t.schema_id else None,
                "table_name": t.table_name,
                "table_type": t.table_type,
                "is_enabled": t.is_enabled,
                "is_sensitive": t.is_sensitive,
                "primary_key_columns": t.primary_key_columns,
                "columns": col_list,
            }
        )

    return result
