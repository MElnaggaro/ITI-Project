"""Deterministic chunking service splitting extracted text into ordered chunks with SHA-256 hashes."""

from __future__ import annotations

import hashlib
from typing import Any


class ChunkingService:
    """Splits text content into structured, ordered document chunks."""

    def split_text_into_chunks(
        self,
        text_content: str,
        chunk_size: int = 200,
        chunk_overlap: int = 30,
    ) -> list[dict[str, Any]]:
        """Split text into ordered chunk objects with chunk_index and content_hash."""
        words = text_content.split()
        if not words:
            return []

        chunks: list[dict[str, Any]] = []
        step = max(1, chunk_size - chunk_overlap)
        chunk_index = 0

        for i in range(0, len(words), step):
            chunk_words = words[i : i + chunk_size]
            chunk_text = " ".join(chunk_words)
            if not chunk_text.strip():
                continue

            content_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()
            token_count = len(chunk_words)

            chunks.append(
                {
                    "chunk_index": chunk_index,
                    "content": chunk_text,
                    "content_hash": content_hash,
                    "token_count": token_count,
                    "page_number": 1,
                }
            )
            chunk_index += 1

        return chunks
