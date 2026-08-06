"""Classifier node for LangGraph orchestrator."""

from __future__ import annotations

from agents.classifier import classify_request
from agents.state import AgentState


def classifier_node(state: AgentState) -> AgentState:
    """Classify user request intent into general, database, document, hybrid, clarification."""
    state.detected_intent = classify_request(
        user_message=state.user_message,
        database_connection_ids=state.database_connection_ids,
        knowledge_base_ids=state.knowledge_base_ids,
    )
    return state
