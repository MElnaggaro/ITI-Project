"""Table and Column permission management API endpoints protected by require_tenant_admin."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_tenant_admin
from core.tenant_context import TenantContext
from repositories.permission_repository import PermissionRepository
from schemas.permissions import (
    ColumnPermissionResponse,
    ColumnPermissionRule,
    TablePermissionCreate,
    TablePermissionResponse,
    TablePermissionUpdate,
)
from services.permission_service import validate_row_filter_dsl

router = APIRouter(prefix="/permissions", tags=["Permissions Management"])


@router.get("/table", response_model=list[TablePermissionResponse])
def list_table_permissions(
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[TablePermissionResponse]:
    """List all table permission grants for the active tenant."""
    repo = PermissionRepository(db)
    perms = repo.list_by_tenant(context.tenant_id)
    result = []
    for p in perms:
        col_perms = repo.get_column_permissions(p.id)
        col_responses = [ColumnPermissionResponse.model_validate(cp) for cp in col_perms]
        resp = TablePermissionResponse.model_validate(p)
        resp.column_permissions = col_responses
        result.append(resp)
    return result


@router.post("/table", response_model=TablePermissionResponse, status_code=status.HTTP_201_CREATED)
def create_table_permission(
    data: TablePermissionCreate,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> TablePermissionResponse:
    """Create a new table permission grant."""
    try:
        validate_row_filter_dsl(data.row_filter)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    repo = PermissionRepository(db)
    try:
        perm = repo.create_table_permission(context.tenant_id, data)
        return TablePermissionResponse.model_validate(perm)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/table/{permission_id}", response_model=TablePermissionResponse)
def get_table_permission(
    permission_id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> TablePermissionResponse:
    """Get a specific table permission by ID."""
    repo = PermissionRepository(db)
    perm = repo.get_by_id(context.tenant_id, permission_id)
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table permission grant not found.")
    col_perms = repo.get_column_permissions(perm.id)
    resp = TablePermissionResponse.model_validate(perm)
    resp.column_permissions = [ColumnPermissionResponse.model_validate(cp) for cp in col_perms]
    return resp


@router.put("/table/{permission_id}", response_model=TablePermissionResponse)
def update_table_permission(
    permission_id: UUID,
    data: TablePermissionUpdate,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> TablePermissionResponse:
    """Update an existing table permission grant."""
    try:
        validate_row_filter_dsl(data.row_filter)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    repo = PermissionRepository(db)
    perm = repo.update_table_permission(context.tenant_id, permission_id, data)
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table permission grant not found.")
    col_perms = repo.get_column_permissions(perm.id)
    resp = TablePermissionResponse.model_validate(perm)
    resp.column_permissions = [ColumnPermissionResponse.model_validate(cp) for cp in col_perms]
    return resp


@router.delete("/table/{permission_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_table_permission(
    permission_id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a table permission grant."""
    repo = PermissionRepository(db)
    success = repo.delete_table_permission(context.tenant_id, permission_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table permission grant not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/table/{permission_id}/columns", response_model=list[ColumnPermissionResponse])
def replace_column_permissions(
    permission_id: UUID,
    rules: list[ColumnPermissionRule],
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[ColumnPermissionResponse]:
    """Atomically replace column rules for a table permission grant."""
    repo = PermissionRepository(db)
    try:
        created_rules = repo.replace_column_permissions(
            tenant_id=context.tenant_id,
            permission_id=permission_id,
            rules=rules,
        )
        return [ColumnPermissionResponse.model_validate(cp) for cp in created_rules]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
