"""Repository for AuditLog entities."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.audit_log import AuditLog
from repositories.base import BaseTenantRepository, to_uuid


class AuditLogRepository(BaseTenantRepository[AuditLog]):
    """Repository operations for tenant-scoped AuditLog entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, AuditLog)

    def create(self, audit_log: AuditLog) -> AuditLog:
        """Persist a new AuditLog record."""
        self.session.add(audit_log)
        self.session.flush()
        return audit_log
