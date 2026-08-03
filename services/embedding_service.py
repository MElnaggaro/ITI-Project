"""Embedding service generating and validating 1024-dimension float vectors."""

from __future__ import annotations

import hashlib
import random

EMBEDDING_DIMENSION = 1024


class EmbeddingService:
    """Generates 1024-dimension embeddings for document chunks and search queries."""

    def __init__(self, model_name: str = "bge-large-en-v1.5") -> None:
        self.model_name = model_name

    def embed_text(self, text: str) -> list[float]:
        """Generate deterministic 1024-dimension normalized float vector."""
        if not text:
            raise ValueError("Cannot embed empty text.")

        # Seed deterministic pseudo-random vector from text sha256 hash for tests/offline mode
        seed_int = int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)
        rng = random.Random(seed_int)

        vector = [rng.uniform(-1.0, 1.0) for _ in range(EMBEDDING_DIMENSION)]
        # L2 Normalize
        norm = (sum(v * v for v in vector)) ** 0.5
        normalized_vector = [v / norm for v in vector]

        self.validate_dimension(normalized_vector)
        return normalized_vector

    def validate_dimension(self, vector: list[float]) -> None:
        """Assert vector dimension is exactly 1024."""
        if len(vector) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Embedding dimension mismatch: expected {EMBEDDING_DIMENSION}, got {len(vector)}."
            )
