"""Document retrieval service executing vector search and evidence reranking."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.document_chunk import DocumentChunk
from models.file import File
from models.knowledge_base import KnowledgeBase
from schemas.knowledge_bases import RetrievedEvidence
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService


class DocumentRetrievalService:
    """Retrieves and reranks document evidence from vector store and PostgreSQL."""

    def __init__(
        self,
        session: Session,
        vector_store: VectorStoreService | None = None,
    ) -> None:
        self.session = session
        self.embedder = EmbeddingService()
        self.vector_store = vector_store or VectorStoreService()

    def retrieve_evidence(
        self,
        context: TenantContext,
        knowledge_base_ids: list[UUID],
        user_query: str,
        top_k: int = 5,
    ) -> list[RetrievedEvidence]:
        """Retrieve citation-ready document evidence for user query."""
        if not knowledge_base_ids or not user_query.strip():
            return []

        # Validate knowledge bases belong to tenant
        valid_kbs = list(
            self.session.scalars(
                select(KnowledgeBase)
                .where(KnowledgeBase.tenant_id == context.tenant_id)
                .where(KnowledgeBase.id.in_(knowledge_base_ids))
            ).all()
        )
        if not valid_kbs:
            return []

        # Generate query embedding
        query_vector = self.embedder.embed_text(user_query)

        all_evidence: list[RetrievedEvidence] = []
        for kb in valid_kbs:
            raw_results = self.vector_store.search(
                tenant_id=context.tenant_id,
                knowledge_base_id=kb.id,
                query_vector=query_vector,
                top_k=top_k,
            )

            for res in raw_results:
                chunk_id = UUID(res["chunk_id"])
                # Load chunk and file details from PostgreSQL for provenance
                chunk_obj = self.session.scalar(
                    select(DocumentChunk)
                    .where(DocumentChunk.tenant_id == context.tenant_id)
                    .where(DocumentChunk.id == chunk_id)
                )
                if not chunk_obj:
                    continue

                file_obj = self.session.scalar(
                    select(File).where(File.id == chunk_obj.file_id)
                )
                file_name = file_obj.original_name if file_obj else "Document"

                all_evidence.append(
                    RetrievedEvidence(
                        chunk_id=chunk_obj.id,
                        file_id=chunk_obj.file_id,
                        file_name=file_name,
                        score=float(res["score"]),
                        excerpt=chunk_obj.content,
                        page_number=chunk_obj.page_number,
                        section_title=chunk_obj.section_title,
                    )
                )

        # Sort and rerank across knowledge bases by similarity score
        all_evidence.sort(key=lambda item: item.score, reverse=True)
        return all_evidence[:top_k]
