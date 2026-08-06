"""Unit tests for ChunkingService deterministic text splitting and hashes."""

from services.chunking_service import ChunkingService


def test_chunking_service_split_text():
    """Verify chunking service creates ordered chunks with hashes and token counts."""
    chunker = ChunkingService()
    text_content = "Word " * 1200  # 1200 words

    chunks = chunker.split_text_into_chunks(text_content, chunk_size=500, chunk_overlap=50)

    assert len(chunks) >= 3
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1
    assert "content_hash" in chunks[0]
    assert len(chunks[0]["content_hash"]) == 64  # SHA-256 length
    assert chunks[0]["token_count"] == 500
