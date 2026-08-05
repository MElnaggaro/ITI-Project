"""Vector store service interfacing with Qdrant / vector index with tenant filtering."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from services.embedding_service import EMBEDDING_DIMENSION


class VectorStoreService:
    """Manages Qdrant / Vector store indexing and tenant-isolated similarity search."""

    def __init__(self) -> None:
        self._index: dict[str, dict[str, Any]] = {}
        self._client: Any = None
        self._collection_name = "document_chunks"

        try:
            from app.config import get_settings
            from qdrant_client import QdrantClient

            settings = get_settings()
            self._collection_name = settings.qdrant_collection_name
            self._client = QdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None,
                timeout=settings.qdrant_timeout_seconds,
            )
        except Exception:
            self._client = None

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

        t_str = str(tenant_id)
        kb_str = str(knowledge_base_id)
        f_str = str(file_id)

        # 1. Try Qdrant client if connected
        if self._client:
            try:
                from qdrant_client.models import PointStruct
                points = [
                    PointStruct(
                        id=str(chunk.id),
                        vector=vec,
                        payload={
                            "chunk_id": str(chunk.id),
                            "tenant_id": t_str,
                            "knowledge_base_id": kb_str,
                            "file_id": f_str,
                            "content": chunk.content,
                            "chunk_index": chunk.chunk_index,
                        },
                    )
                    for chunk, vec in zip(chunks, embeddings)
                ]
                self._client.upsert(collection_name=self._collection_name, points=points)
            except Exception:
                pass

        # 2. In-memory backup / fallback index
        for chunk, vec in zip(chunks, embeddings):
            if len(vec) != EMBEDDING_DIMENSION:
                raise ValueError(f"Vector dimension must be {EMBEDDING_DIMENSION}.")

            chunk_id = str(chunk.id)
            self._index[chunk_id] = {
                "chunk_id": chunk_id,
                "tenant_id": t_str,
                "knowledge_base_id": kb_str,
                "file_id": f_str,
                "vector": vec,
                "content": chunk.content,
                "chunk_index": chunk.chunk_index,
            }

        return len(chunks)

    def delete_file_vectors(self, tenant_id: UUID, file_id: UUID) -> int:
        """Delete all vectors for a file within a tenant."""
        t_str = str(tenant_id)
        f_str = str(file_id)

        if self._client:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                self._client.delete(
                    collection_name=self._collection_name,
                    points_selector=Filter(
                        must=[
                            FieldCondition(key="tenant_id", match=MatchValue(value=t_str)),
                            FieldCondition(key="file_id", match=MatchValue(value=f_str)),
                        ]
                    ),
                )
            except Exception:
                pass

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

        if self._client:
            try:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                search_result = self._client.search(
                    collection_name=self._collection_name,
                    query_vector=query_vector,
                    query_filter=Filter(
                        must=[
                            FieldCondition(key="tenant_id", match=MatchValue(value=t_str)),
                            FieldCondition(key="knowledge_base_id", match=MatchValue(value=kb_str)),
                        ]
                    ),
                    limit=top_k,
                )
                if search_result:
                    return [
                        {
                            "chunk_id": res.payload["chunk_id"],
                            "file_id": res.payload["file_id"],
                            "score": float(res.score),
                            "content": res.payload["content"],
                        }
                        for res in search_result
                    ]
            except Exception:
                pass

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

