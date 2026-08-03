"""User role management API endpoints protected by require_tenant_admin."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, require_tenant_admin
from core.tenant_context import TenantContext
from repositories.role_repository import RoleRepository
from schemas.roles import RoleResponse, UserRolesAssignment

router = APIRouter(prefix="/users", tags=["Users Management"])


@router.put("/{user_id}/roles", response_model=list[RoleResponse])
def replace_user_roles(
    user_id: UUID,
    assignment: UserRolesAssignment,
    context: TenantContext = Depends(require_tenant_admin),
    db: Session = Depends(get_db),
) -> list[RoleResponse]:
    """Atomically replace user role assignments."""
    repo = RoleRepository(db)
    try:
        updated_roles = repo.replace_user_roles(
            tenant_id=context.tenant_id,
            user_id=user_id,
            role_ids=assignment.role_ids,
        )
        return [RoleResponse.model_validate(r) for r in updated_roles]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
