"""Unit tests for DocumentRetrievalService vector search and evidence reranking."""

from uuid import uuid4

from core.security import hash_password
from core.tenant_context import TenantContext
from models.document_chunk import DocumentChunk
from models.file import File
from models.knowledge_base import KnowledgeBase
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from services.document_retrieval_service import DocumentRetrievalService
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService


def test_document_retrieval_service_evidence(db_session):
    """Verify document evidence retrieval returns citation-ready excerpts."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Ret Tenant", "ret-tenant")
    user = user_repo.create(tenant.id, "ret@user.com", hash_password("pass"))

    kb = KnowledgeBase(id=uuid4(), tenant_id=tenant.id, name="KB Docs")
    f_obj = File(id=uuid4(), tenant_id=tenant.id, knowledge_base_id=kb.id, original_name="q3_report.pdf", stored_name="s_q3.pdf", storage_path="/tmp/q3.pdf", processing_status="completed")
    chunk = DocumentChunk(id=uuid4(), tenant_id=tenant.id, knowledge_base_id=kb.id, file_id=f_obj.id, chunk_index=0, content="Q3 revenue grew by 15 percent.", page_number=2)

    db_session.add_all([kb, f_obj, chunk])
    db_session.commit()

    embedder = EmbeddingService()
    v_store = VectorStoreService()
    vec = embedder.embed_text(chunk.content)
    v_store.upsert_chunks(tenant.id, kb.id, f_obj.id, [chunk], [vec])

    context = TenantContext(tenant_id=tenant.id, user_id=user.id)
    retriever = DocumentRetrievalService(db_session, vector_store=v_store)

    evidence = retriever.retrieve_evidence(context, [kb.id], "revenue growth", top_k=3)

    assert len(evidence) == 1
    assert evidence[0].file_name == "q3_report.pdf"
    assert "Q3 revenue" in evidence[0].excerpt
    assert evidence[0].page_number == 2
