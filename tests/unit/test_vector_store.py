"""Unit tests for VectorStoreService tenant filtering and vector search."""

from dataclasses import dataclass
from uuid import uuid4

import pytest

from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService


@dataclass
class DummyChunk:
    id: any
    content: str
    chunk_index: int


def test_vector_store_tenant_isolation_and_search():
    """Verify vector search isolates results by tenant_id and knowledge_base_id."""
    v_store = VectorStoreService()
    embedder = EmbeddingService()

    tenant_a = uuid4()
    tenant_b = uuid4()
    kb_a = uuid4()

    chunk_a = DummyChunk(id=uuid4(), content="Tenant A information about finances.", chunk_index=0)
    chunk_b = DummyChunk(id=uuid4(), content="Tenant B secret data.", chunk_index=0)

    vec_a = embedder.embed_text(chunk_a.content)
    vec_b = embedder.embed_text(chunk_b.content)

    v_store.upsert_chunks(tenant_a, kb_a, uuid4(), [chunk_a], [vec_a])
    v_store.upsert_chunks(tenant_b, uuid4(), uuid4(), [chunk_b], [vec_b])

    # Search for tenant_a
    results = v_store.search(tenant_a, kb_a, vec_a, top_k=5)
    assert len(results) == 1
    assert results[0]["chunk_id"] == str(chunk_a.id)

    # Search for tenant_a on non-existent KB returns empty
    empty_results = v_store.search(tenant_a, uuid4(), vec_a, top_k=5)
    assert len(empty_results) == 0
