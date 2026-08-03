"""Unit tests for EmbeddingService 1024-dimension vector generation and validation."""

import pytest

from services.embedding_service import EMBEDDING_DIMENSION, EmbeddingService


def test_embedding_dimension_and_normalization():
    """Verify generated vector has exactly 1024 dimensions and normalized values."""
    embedder = EmbeddingService()
    vec = embedder.embed_text("Sample paragraph text for vector embedding test.")

    assert len(vec) == EMBEDDING_DIMENSION
    # Assert vector is L2 normalized
    norm = sum(v * v for v in vec) ** 0.5
    assert abs(norm - 1.0) < 1e-4


def test_embedding_dimension_validation_rejection():
    """Verify validator rejects vectors with wrong dimensions."""
    embedder = EmbeddingService()

    with pytest.raises(ValueError, match="Embedding dimension mismatch"):
        embedder.validate_dimension([0.1] * 512)

    with pytest.raises(ValueError, match="Cannot embed empty text"):
        embedder.embed_text("")
