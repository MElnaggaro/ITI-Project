"""Request intent classifier for ChatOrchestrator pipeline."""

from __future__ import annotations

from uuid import UUID

from schemas.chat import IntentType


def classify_request(
    user_message: str,
    database_connection_ids: list[UUID] | None = None,
    knowledge_base_ids: list[UUID] | None = None,
) -> IntentType:
    """Classify user request into one of: general, database, document, hybrid, clarification."""
    msg_lower = user_message.strip().lower()
    has_conn = bool(database_connection_ids)
    has_kb = bool(knowledge_base_ids)

    # Keywords detection
    db_keywords = {"sql", "table", "database", "orders", "users", "select", "count", "show tables", "customers", "total sales"}
    doc_keywords = {"document", "report", "pdf", "file", "excerpt", "policy", "knowledge", "text", "summary"}

    matches_db = any(kw in msg_lower for kw in db_keywords)
    matches_doc = any(kw in msg_lower for kw in doc_keywords)

    if (has_conn and has_kb) or (matches_db and matches_doc):
        return "hybrid"
    elif has_conn or matches_db:
        return "database"
    elif has_kb or matches_doc:
        return "document"
    elif msg_lower in {"what", "help", "hello", "hi", "hey"}:
        return "general"
    elif len(msg_lower) < 3:
        return "clarification"

    return "general"
