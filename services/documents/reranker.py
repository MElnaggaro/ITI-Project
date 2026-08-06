"""Evidence ReRanker service for scoring and reordering retrieved document chunks."""

from __future__ import annotations

from schemas.knowledge_bases import RetrievedEvidence


class EvidenceReRankerService:
    """Reranks vector search candidate chunks using text cross-encoder or hybrid score fusion."""

    def rerank(
        self,
        query: str,
        candidates: list[RetrievedEvidence],
        top_k: int = 10,
    ) -> list[RetrievedEvidence]:
        """Rerank candidates based on similarity score and lexical overlap relevance."""
        if not candidates:
            return []

        query_terms = set(query.lower().split())

        def _calculate_score(item: RetrievedEvidence) -> float:
            base_vector_score = item.score
            content_lower = item.excerpt.lower()
            overlap_count = sum(1 for term in query_terms if term in content_lower)
            lexical_boost = (overlap_count / max(1, len(query_terms))) * 0.2
            return base_vector_score + lexical_boost

        reranked = sorted(
            candidates,
            key=lambda item: _calculate_score(item),
            reverse=True,
        )

        return reranked[:top_k]
