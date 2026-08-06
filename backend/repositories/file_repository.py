"""Repository for File model metadata persistence."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from models.file import File
from repositories.base import BaseTenantRepository, to_uuid


class FileRepository(BaseTenantRepository[File]):
    """Repository operations for tenant-scoped File metadata entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, File)

    def create(self, file_record: File) -> File:
        """Persist a new File metadata record."""
        self.session.add(file_record)
        self.session.flush()
        return file_record

    def delete(self, tenant_id: UUID | str, file_id: UUID | str) -> bool:
        """Delete a File record from platform database."""
        f_record = self.get_by_id(tenant_id, file_id)
        if not f_record:
            return False
        self.session.delete(f_record)
        self.session.flush()
        return True
