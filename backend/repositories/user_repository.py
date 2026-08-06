"""User repository for user management with mandatory tenant scoping."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User
from repositories.base import BaseTenantRepository, to_uuid


class UserRepository(BaseTenantRepository[User]):
    """Repository operations for User records with mandatory tenant predicate."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, User)

    def get_by_tenant_and_email(self, tenant_id: UUID | str, email: str) -> User | None:
        """Fetch user by (tenant_id, email) composite constraint."""
        t_id = to_uuid(tenant_id)
        stmt = (
            select(User)
            .where(User.tenant_id == t_id)
            .where(User.email == email)
        )
        return self.session.scalar(stmt)

    def create(
        self,
        tenant_id: UUID | str,
        email: str,
        password_hash: str | None = None,
        full_name: str | None = None,
        is_tenant_admin: bool = False,
    ) -> User:
        """Create a user bound to a tenant."""
        t_id = to_uuid(tenant_id)
        user = User(
            tenant_id=t_id,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            is_tenant_admin=is_tenant_admin,
        )
        self.session.add(user)
        self.session.flush()
        return user
