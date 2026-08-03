"""Document processing pipeline service orchestrating parsing, chunking, embedding, and vector indexing."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.document_chunk import DocumentChunk
from models.file import File
from repositories.file_repository import FileRepository
from services.chunking_service import ChunkingService
from services.document_processor_service import DocumentProcessorService
from services.embedding_service import EmbeddingService
from services.storage_service import LocalStorageService
from services.vector_store_service import VectorStoreService


class DocumentPipelineService:
    """Orchestrates end-to-end document parsing, chunking, embedding, and indexing."""

    def __init__(
        self,
        session: Session,
        storage: LocalStorageService | None = None,
        vector_store: VectorStoreService | None = None,
    ) -> None:
        self.session = session
        self.file_repo = FileRepository(session)
        self.storage = storage or LocalStorageService()
        self.processor = DocumentProcessorService()
        self.chunker = ChunkingService()
        self.embedder = EmbeddingService()
        self.vector_store = vector_store or VectorStoreService()

    def process_file(self, context: TenantContext, file_id: UUID) -> dict[str, Any]:
        """Run parsing, chunking, embedding, and vector indexing for a file."""
        file_record = self.file_repo.get_by_id(context.tenant_id, file_id)
        if not file_record:
            raise ValueError("File record not found.")

        file_record.processing_status = "processing"
        self.session.flush()

        try:
            # Read file bytes from storage
            file_bytes = Path(file_record.storage_path).read_bytes()

            # 1. Extract Text
            text_content, page_count, extracted_len = self.processor.extract_text(
                file_bytes=file_bytes,
                filename=file_record.original_name,
            )

            file_record.page_count = page_count
            file_record.extracted_text_length = extracted_len

            # 2. Split into chunks
            raw_chunks = self.chunker.split_text_into_chunks(text_content)

            # Clear existing chunks for reprocess idempotency
            self.session.execute(
                delete(DocumentChunk).where(DocumentChunk.file_id == file_record.id)
            )

            # Delete old vector points
            self.vector_store.delete_file_vectors(context.tenant_id, file_record.id)

            # 3. Create DocumentChunk records
            chunk_records: list[DocumentChunk] = []
            embeddings: list[list[float]] = []

            kb_id = file_record.knowledge_base_id or file_record.id

            for c_data in raw_chunks:
                # 4. Generate Embedding (1024 dimensions)
                vec = self.embedder.embed_text(c_data["content"])
                embeddings.append(vec)

                d_chunk = DocumentChunk(
                    tenant_id=file_record.tenant_id,
                    knowledge_base_id=kb_id,
                    file_id=file_record.id,
                    chunk_index=c_data["chunk_index"],
                    content=c_data["content"],
                    content_hash=c_data["content_hash"],
                    page_number=c_data["page_number"],
                    token_count=c_data["token_count"],
                    embedding=vec,
                )
                self.session.add(d_chunk)
                chunk_records.append(d_chunk)

            self.session.flush()

            # 5. Index Vectors in Vector Store
            self.vector_store.upsert_chunks(
                tenant_id=file_record.tenant_id,
                knowledge_base_id=kb_id,
                file_id=file_record.id,
                chunks=chunk_records,
                embeddings=embeddings,
            )

            now = datetime.now(timezone.utc)
            file_record.processing_status = "completed"
            file_record.processed_at = now
            self.session.flush()

            return {
                "file_id": str(file_record.id),
                "status": "completed",
                "page_count": page_count,
                "chunks_count": len(chunk_records),
                "extracted_length": extracted_len,
            }

        except Exception as e:
            file_record.processing_status = "failed"
            file_record.processing_error = str(e).split("\n")[0][:200]
            self.session.flush()
            raise RuntimeError(f"Document pipeline processing failed: {str(e)[:150]}")
