"""Repository for DatabaseConnection entities."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.database_connection import DatabaseConnection
from repositories.base import BaseTenantRepository, to_uuid


class ConnectionRepository(BaseTenantRepository[DatabaseConnection]):
    """Repository operations for tenant-scoped DatabaseConnection entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, DatabaseConnection)

    def get_by_name(self, tenant_id: UUID | str, name: str) -> DatabaseConnection | None:
        """Fetch connection by (tenant_id, name) unique constraint."""
        t_id = to_uuid(tenant_id)
        stmt = (
            select(DatabaseConnection)
            .where(DatabaseConnection.tenant_id == t_id)
            .where(DatabaseConnection.name == name)
        )
        return self.session.scalar(stmt)

    def create(self, connection: DatabaseConnection) -> DatabaseConnection:
        """Create a new DatabaseConnection record."""
        self.session.add(connection)
        self.session.flush()
        return connection

    def update_test_status(
        self,
        tenant_id: UUID | str,
        connection_id: UUID | str,
        status: str,
        message: str,
        tested_at: datetime,
    ) -> DatabaseConnection | None:
        """Update test status and last_tested_at timestamp."""
        conn = self.get_by_id(tenant_id, connection_id)
        if not conn:
            return None
        conn.status = status
        conn.last_test_message = message
        conn.last_tested_at = tested_at
        self.session.flush()
        return conn

    def delete(self, tenant_id: UUID | str, connection_id: UUID | str) -> bool:
        """Delete a DatabaseConnection record from platform database."""
        conn = self.get_by_id(tenant_id, connection_id)
        if not conn:
            return False
        self.session.delete(conn)
        self.session.flush()
        return True
