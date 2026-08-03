"""Repository for QueryExecution records."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.query_execution import QueryExecution
from repositories.base import BaseTenantRepository


class QueryExecutionRepository(BaseTenantRepository[QueryExecution]):
    """Repository operations for tenant-scoped QueryExecution audit records."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, QueryExecution)

    def create(self, record: QueryExecution) -> QueryExecution:
        """Persist a new QueryExecution audit record."""
        self.session.add(record)
        self.session.flush()
        return record
