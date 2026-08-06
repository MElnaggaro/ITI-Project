"""Tenant repository for tenant lookup and management."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.tenant import Tenant
from repositories.base import to_uuid


class TenantRepository:
    """Repository operations for Tenant identity records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, tenant_id: UUID | str) -> Tenant | None:
        """Fetch tenant by UUID primary key."""
        t_id = to_uuid(tenant_id)
        stmt = select(Tenant).where(Tenant.id == t_id)
        return self.session.scalar(stmt)

    def get_by_code(self, code: str) -> Tenant | None:
        """Fetch tenant by unique code."""
        stmt = select(Tenant).where(Tenant.code == code)
        return self.session.scalar(stmt)

    def create(self, name: str, code: str, settings: dict | None = None) -> Tenant:
        """Create a new tenant record."""
        tenant = Tenant(
            name=name,
            code=code,
            settings=settings or {},
        )
        self.session.add(tenant)
        self.session.flush()
        return tenant
