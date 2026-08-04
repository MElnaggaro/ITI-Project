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

    # Greetings & General queries check FIRST
    greetings = {"hi", "hello", "hey", "howdy", "who are you", "what can you do", "help", "welcome"}
    if msg_lower in greetings or any(msg_lower.startswith(g) for g in ["hi ", "hello ", "hey "]):
        return "general"

    matches_db = any(kw in msg_lower for kw in db_keywords)
    matches_doc = any(kw in msg_lower for kw in doc_keywords)

    if matches_db and matches_doc:
        return "hybrid"
    elif matches_db:
        return "database"
    elif matches_doc:
        return "document"
    elif has_conn and has_kb:
        return "hybrid"
    elif has_conn:
        return "database"
    elif has_kb:
        return "document"
    elif len(msg_lower) < 3:
        return "clarification"

    return "general"

