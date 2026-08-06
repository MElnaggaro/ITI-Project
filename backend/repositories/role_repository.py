"""Role repository for tenant-scoped role CRUD and user assignment."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.role import Role
from models.user import User
from models.user_role import UserRole
from repositories.base import BaseTenantRepository, to_uuid


class RoleRepository(BaseTenantRepository[Role]):
    """Repository operations for tenant-scoped Role entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Role)

    def get_by_name(self, tenant_id: UUID | str, name: str) -> Role | None:
        """Fetch role by (tenant_id, name) unique constraint."""
        t_id = to_uuid(tenant_id)
        stmt = (
            select(Role)
            .where(Role.tenant_id == t_id)
            .where(Role.name == name)
        )
        return self.session.scalar(stmt)

    def create(self, tenant_id: UUID | str, name: str, description: str | None = None) -> Role:
        """Create a new role in a tenant."""
        t_id = to_uuid(tenant_id)
        role = Role(tenant_id=t_id, name=name, description=description)
        self.session.add(role)
        self.session.flush()
        return role

    def update(self, tenant_id: UUID | str, role_id: UUID | str, name: str, description: str | None = None) -> Role | None:
        """Update an existing role."""
        role = self.get_by_id(tenant_id, role_id)
        if not role:
            return None
        role.name = name
        role.description = description
        self.session.flush()
        return role

    def delete(self, tenant_id: UUID | str, role_id: UUID | str) -> bool:
        """Delete a role by ID."""
        role = self.get_by_id(tenant_id, role_id)
        if not role:
            return False
        self.session.delete(role)
        self.session.flush()
        return True

    def get_user_roles(self, tenant_id: UUID | str, user_id: UUID | str) -> list[Role]:
        """Fetch all roles assigned to a user within a tenant."""
        t_id = to_uuid(tenant_id)
        u_id = to_uuid(user_id)
        stmt = (
            select(Role)
            .join(UserRole, Role.id == UserRole.role_id)
            .where(Role.tenant_id == t_id)
            .where(UserRole.user_id == u_id)
        )
        return list(self.session.scalars(stmt).all())

    def replace_user_roles(self, tenant_id: UUID | str, user_id: UUID | str, role_ids: list[UUID]) -> list[Role]:
        """Atomically replace role assignments for a user."""
        t_id = to_uuid(tenant_id)
        u_id = to_uuid(user_id)

        # Validate user belongs to tenant
        user = self.session.scalar(select(User).where(User.tenant_id == t_id).where(User.id == u_id))
        if not user:
            raise ValueError(f"User {user_id} not found in tenant {tenant_id}")

        # Validate all role_ids belong to tenant
        valid_roles = list(
            self.session.scalars(
                select(Role).where(Role.tenant_id == t_id).where(Role.id.in_(role_ids))
            ).all()
        )
        if len(valid_roles) != len(set(role_ids)):
            raise ValueError("One or more role IDs are invalid or belong to another tenant.")

        # Delete existing user_roles
        self.session.execute(delete(UserRole).where(UserRole.user_id == u_id))

        # Insert new user_roles
        for role in valid_roles:
            ur = UserRole(user_id=u_id, role_id=role.id)
            self.session.add(ur)

        self.session.flush()
        return valid_roles
