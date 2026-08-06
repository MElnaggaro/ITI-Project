"""File Service handling upload validation, storage, and lifecycle metadata."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.file import File
from models.knowledge_base import KnowledgeBase
from repositories.file_repository import FileRepository
from schemas.files import FileResponse
from services.storage_service import LocalStorageService

ALLOWED_EXTENSIONS = frozenset(
    {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"}
)

ALLOWED_MIME_TYPES = frozenset(
    {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "text/plain",
        "application/octet-stream",
    }
)


class FileService:
    """Service orchestrating file uploads and lifecycle operations."""

    def __init__(self, session: Session, storage: LocalStorageService | None = None) -> None:
        self.session = session
        self.repo = FileRepository(session)
        self.storage = storage or LocalStorageService()

    def upload_file(
        self,
        context: TenantContext,
        file_bytes: bytes,
        filename: str,
        content_type: str | None = None,
        knowledge_base_id: UUID | None = None,
    ) -> FileResponse:
        """Validate and upload file bytes, creating durable metadata record."""
        if not file_bytes:
            raise ValueError("Uploaded file is empty.")

        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension '{ext}' is not supported. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValueError(f"MIME type '{content_type}' is not supported.")

        if knowledge_base_id:
            kb = self.session.scalar(
                select(KnowledgeBase)
                .where(KnowledgeBase.tenant_id == context.tenant_id)
                .where(KnowledgeBase.id == knowledge_base_id)
            )
            if not kb:
                raise ValueError("Knowledge base not found or belongs to another tenant.")

        stored_name, storage_path, checksum = self.storage.save_file(
            tenant_id=context.tenant_id,
            file_bytes=file_bytes,
            original_name=filename,
        )

        file_record = File(
            tenant_id=context.tenant_id,
            knowledge_base_id=knowledge_base_id,
            uploaded_by=context.user_id,
            original_name=filename,
            stored_name=stored_name,
            storage_path=storage_path,
            mime_type=content_type or "application/octet-stream",
            extension=ext,
            file_size_bytes=len(file_bytes),
            checksum=checksum,
            processing_status="pending",
        )

        created = self.repo.create(file_record)
        return FileResponse.model_validate(created)

    def list_files(self, tenant_id: UUID) -> list[FileResponse]:
        """List all files for a tenant."""
        files = self.repo.list_by_tenant(tenant_id)
        return [FileResponse.model_validate(f) for f in files]

    def get_file(self, tenant_id: UUID, file_id: UUID) -> FileResponse | None:
        """Get file metadata detail."""
        f_record = self.repo.get_by_id(tenant_id, file_id)
        if not f_record:
            return None
        return FileResponse.model_validate(f_record)

    def delete_file(self, tenant_id: UUID, file_id: UUID) -> bool:
        """Delete file metadata, storage object, and vectors."""
        f_record = self.repo.get_by_id(tenant_id, file_id)
        if not f_record:
            return False

        # 1. Delete vectors from Qdrant
        try:
            from services.vector_store_service import VectorStoreService
            vs = VectorStoreService()
            vs.delete_file_vectors(tenant_id, file_id)
        except Exception as e:
            # Continue deletion even if vector store fails
            print(f"Failed to delete vectors for {file_id}: {e}")

        # 2. Delete file from local storage
        self.storage.delete_file(f_record.storage_path)
        
        # 3. Delete from DB repository
        result = self.repo.delete(tenant_id, file_id)
        
        # 4. Explicitly commit to fix the UI refresh bug
        self.session.commit()
        return result

    def reprocess_file(self, tenant_id: UUID, file_id: UUID) -> FileResponse:
        """Reset file processing status to pending."""
        f_record = self.repo.get_by_id(tenant_id, file_id)
        if not f_record:
            raise ValueError("File not found.")

        f_record.processing_status = "pending"
        f_record.processing_error = None
        self.session.flush()

        return FileResponse.model_validate(f_record)

    def associate_file_with_kb(
        self,
        tenant_id: UUID,
        file_id: UUID,
        knowledge_base_id: UUID,
    ) -> FileResponse:
        """Associate a file with a knowledge base."""
        f_record = self.repo.get_by_id(tenant_id, file_id)
        if not f_record:
            raise ValueError("File not found.")

        kb = self.session.scalar(
            select(KnowledgeBase)
            .where(KnowledgeBase.tenant_id == tenant_id)
            .where(KnowledgeBase.id == knowledge_base_id)
        )
        if not kb:
            raise ValueError("Knowledge base not found.")

        f_record.knowledge_base_id = kb.id
        self.session.flush()
        return FileResponse.model_validate(f_record)
