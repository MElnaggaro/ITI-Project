"""Role management API endpoints protected by require_tenant_admin dependency."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_tenant_admin
from core.tenant_context import TenantContext
from repositories.role_repository import RoleRepository
from schemas.roles import RoleCreate, RoleResponse, RoleUpdate

router = APIRouter(prefix="/roles", tags=["Roles Management"])


@router.get("", response_model=list[RoleResponse])
def list_roles(
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    """List all tenant-scoped roles for the active tenant."""
    repo = RoleRepository(db)
    roles = repo.list_by_tenant(context.tenant_id)
    return [RoleResponse.model_validate(r) for r in roles]


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    data: RoleCreate,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> RoleResponse:
    """Create a new tenant-scoped role."""
    repo = RoleRepository(db)
    existing = repo.get_by_name(context.tenant_id, data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{data.name}' already exists in this tenant.",
        )
    role = repo.create(context.tenant_id, data.name, data.description)
    return RoleResponse.model_validate(role)


@router.put("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: UUID,
    data: RoleUpdate,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> RoleResponse:
    """Update an existing role."""
    repo = RoleRepository(db)
    role = repo.update(context.tenant_id, role_id, data.name, data.description)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return RoleResponse.model_validate(role)


@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_role(
    role_id: UUID,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a role by ID."""
    repo = RoleRepository(db)
    success = repo.delete(context.tenant_id, role_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
