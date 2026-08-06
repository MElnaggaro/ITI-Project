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


from services.documents.query_rewriter import QueryRewriterService
from services.documents.reranker import EvidenceReRankerService


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
        self.query_rewriter = QueryRewriterService()
        self.reranker = EvidenceReRankerService()

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

        from uuid import UUID as PyUUID
        t_uuid = PyUUID(str(context.tenant_id)) if not isinstance(context.tenant_id, PyUUID) else context.tenant_id
        kb_uuids = [PyUUID(str(k)) if not isinstance(k, PyUUID) else k for k in knowledge_base_ids]

        # Validate knowledge bases belong to tenant
        valid_kbs = list(
            self.session.scalars(
                select(KnowledgeBase)
                .where(KnowledgeBase.tenant_id == t_uuid)
                .where(KnowledgeBase.id.in_(kb_uuids))
            ).all()
        )
        if not valid_kbs:
            return []

        # 1. Rewrite query for vector search optimization
        rewritten_query = self.query_rewriter.rewrite_query(user_query) or user_query

        # 2. Generate query embedding
        query_vector = self.embedder.embed_text(rewritten_query)

        all_evidence: list[RetrievedEvidence] = []
        for kb in valid_kbs:
            raw_results = self.vector_store.search(
                tenant_id=context.tenant_id,
                knowledge_base_id=kb.id,
                query_vector=query_vector,
                top_k=top_k * 10,
            )

            for res in raw_results:
                chunk_id = UUID(res["chunk_id"])
                chunk_obj = self.session.scalar(
                    select(DocumentChunk)
                    .where(DocumentChunk.tenant_id == t_uuid)
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

        # 3. Apply Evidence ReRanker across candidates
        return self.reranker.rerank(query=user_query, candidates=all_evidence, top_k=top_k)

