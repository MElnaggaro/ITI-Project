"""Repository contracts and base class that enforce mandatory tenant scope on all operations."""

from __future__ import annotations

from typing import Generic, Protocol, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.base import Base

EntityT = TypeVar("EntityT", bound=Base)


def to_uuid(val: UUID | str) -> UUID:
    """Normalize string or UUID inputs into a Python UUID instance."""
    if isinstance(val, UUID):
        return val
    return UUID(str(val))


class TenantScopedRepositoryProtocol(Protocol[EntityT]):
    """Repository interface requiring explicit trusted tenant scope."""

    def get_by_id(self, tenant_id: UUID | str, resource_id: UUID | str) -> EntityT | None:
        """Return a resource only when it belongs to the supplied tenant."""
        ...


class BaseTenantRepository(Generic[EntityT]):
    """Base repository enforcing tenant_id scoping on query execution."""

    def __init__(self, session: Session, model_cls: type[EntityT]) -> None:
        self.session = session
        self.model_cls = model_cls

    def get_by_id(self, tenant_id: UUID | str, resource_id: UUID | str) -> EntityT | None:
        """Fetch entity matching both primary key AND tenant_id."""
        t_id = to_uuid(tenant_id)
        r_id = to_uuid(resource_id)

        stmt = (
            select(self.model_cls)
            .where(self.model_cls.id == r_id)  # type: ignore[attr-defined]
            .where(self.model_cls.tenant_id == t_id)  # type: ignore[attr-defined]
        )
        return self.session.scalar(stmt)

    def list_by_tenant(
        self,
        tenant_id: UUID | str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[EntityT]:
        """Fetch list of entities belonging to tenant_id."""
        t_id = to_uuid(tenant_id)
        stmt = (
            select(self.model_cls)
            .where(self.model_cls.tenant_id == t_id)  # type: ignore[attr-defined]
            .limit(limit)
            .offset(offset)
        )
        return list(self.session.scalars(stmt).all())
