"""Source selector node validating connection and knowledge base availability."""

from __future__ import annotations

from agents.state import AgentState


def source_selector_node(state: AgentState) -> AgentState:
    """Validate and set source routing based on intent and available sources."""
    intent = state.detected_intent
    has_db = bool(state.database_connection_ids)
    has_doc = bool(state.knowledge_base_ids)

    if intent == "database" and not has_db:
        state.detected_intent = "clarification"
    elif intent == "document" and not has_doc:
        state.detected_intent = "clarification"
    elif intent == "hybrid":
        if not has_db and not has_doc:
            state.detected_intent = "clarification"
        elif not has_db:
            state.detected_intent = "document"
        elif not has_doc:
            state.detected_intent = "database"

    return state
