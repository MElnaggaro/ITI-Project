"""Database connection management API endpoints protected by require_tenant_admin."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_tenant_admin
from core.tenant_context import TenantContext
from schemas.database_connections import (
    ConnectionTestResponse,
    DatabaseConnectionCreate,
    DatabaseConnectionResponse,
    DatabaseConnectionUpdate,
)
from services.connection_service import ConnectionService
from services.schema_sync_service import SchemaSyncService

router = APIRouter(prefix="/database-connections", tags=["Database Connections"])


@router.get("", response_model=list[DatabaseConnectionResponse])
def list_database_connections(
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[DatabaseConnectionResponse]:
    """List all tenant-scoped database connections."""
    service = ConnectionService(db)
    return service.list_connections(context.tenant_id)


@router.post("", response_model=DatabaseConnectionResponse, status_code=status.HTTP_201_CREATED)
def create_database_connection(
    data: DatabaseConnectionCreate,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> DatabaseConnectionResponse:
    """Create a new database connection with encrypted credentials."""
    service = ConnectionService(db)
    try:
        return service.create_connection(context, data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{id}", response_model=DatabaseConnectionResponse)
def get_database_connection(
    id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> DatabaseConnectionResponse:
    """Get database connection metadata by ID."""
    service = ConnectionService(db)
    conn = service.get_connection(context.tenant_id, id)
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found.")
    return conn


@router.put("/{id}", response_model=DatabaseConnectionResponse)
def update_database_connection(
    id: UUID,
    data: DatabaseConnectionUpdate,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> DatabaseConnectionResponse:
    """Update database connection configuration."""
    service = ConnectionService(db)
    try:
        updated = service.update_connection(context, id, data)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found.")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_database_connection(
    id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a database connection record from the platform database."""
    service = ConnectionService(db)
    success = service.delete_connection(context.tenant_id, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database connection not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/test", response_model=ConnectionTestResponse)
def test_database_connection(
    id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> ConnectionTestResponse:
    """Perform a read-only connectivity test probe (`SELECT 1`)."""
    service = ConnectionService(db)
    try:
        return service.test_connection(context, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/{id}/sync-schema", response_model=dict[str, Any], status_code=status.HTTP_202_ACCEPTED)
def sync_database_schema(
    id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Trigger catalog introspection and atomic metadata cache synchronization."""
    sync_service = SchemaSyncService(db)
    try:
        return sync_service.sync_schema(context, id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
