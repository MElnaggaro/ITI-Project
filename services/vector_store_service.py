"""Vector store service interfacing with Qdrant / vector index with tenant filtering."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from services.embedding_service import EMBEDDING_DIMENSION


class VectorStoreService:
    """Manages Qdrant / Vector store indexing and tenant-isolated similarity search."""

    def __init__(self) -> None:
        # In-memory vector index store for testing / local baseline execution
        self._index: dict[str, dict[str, Any]] = {}

    def upsert_chunks(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        file_id: UUID,
        chunks: list[Any],
        embeddings: list[list[float]],
    ) -> int:
        """Index chunk vectors with mandatory tenant_id and knowledge_base_id payload filters."""
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks count must match embeddings count.")

        for chunk, vec in zip(chunks, embeddings):
            if len(vec) != EMBEDDING_DIMENSION:
                raise ValueError(f"Vector dimension must be {EMBEDDING_DIMENSION}.")

            chunk_id = str(chunk.id)
            self._index[chunk_id] = {
                "chunk_id": chunk_id,
                "tenant_id": str(tenant_id),
                "knowledge_base_id": str(knowledge_base_id),
                "file_id": str(file_id),
                "vector": vec,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
            }

        return len(chunks)

    def delete_file_vectors(self, tenant_id: UUID, file_id: UUID) -> int:
        """Delete all vectors for a file within a tenant."""
        t_str = str(tenant_id)
        f_str = str(file_id)

        keys_to_delete = [
            cid
            for cid, data in self._index.items()
            if data["tenant_id"] == t_str and data["file_id"] == f_str
        ]

        for cid in keys_to_delete:
            del self._index[cid]

        return len(keys_to_delete)

    def search(
        self,
        tenant_id: UUID,
        knowledge_base_id: UUID,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        """Search vector store enforcing mandatory tenant_id and knowledge_base_id filters."""
        if len(query_vector) != EMBEDDING_DIMENSION:
            raise ValueError(f"Query vector dimension must be {EMBEDDING_DIMENSION}.")

        t_str = str(tenant_id)
        kb_str = str(knowledge_base_id)

        candidates = [
            data
            for data in self._index.values()
            if data["tenant_id"] == t_str and data["knowledge_base_id"] == kb_str
        ]

        def _dot(a: list[float], b: list[float]) -> float:
            return sum(x * y for x, y in zip(a, b))

        scored = []
        for cand in candidates:
            score = _dot(query_vector, cand["vector"])
            scored.append(
                {
                    "chunk_id": cand["chunk_id"],
                    "file_id": cand["file_id"],
                    "score": score,
                    "content": cand["content"],
                }
            )

        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]
