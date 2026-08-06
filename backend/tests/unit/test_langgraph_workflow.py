"""Unit tests for LangGraph modular state nodes and ChatOrchestrator pipeline."""

from uuid import uuid4
from core.tenant_context import TenantContext
from agents.state import AgentState
from agents.nodes.classifier_node import classifier_node
from agents.nodes.source_selector_node import source_selector_node
from agents.nodes.hybrid_merger_node import hybrid_merger_node
from agents.nodes.final_response_node import final_response_node


def test_classifier_node():
    """Verify classifier node sets detected_intent on AgentState."""
    ctx = TenantContext(tenant_id=uuid4(), user_id=uuid4(), request_id="req-123")
    state = AgentState(
        context=ctx,
        conversation_id=uuid4(),
        message_id=uuid4(),
        user_message="SELECT * FROM orders",
    )
    res_state = classifier_node(state)
    assert res_state.detected_intent == "database"


def test_source_selector_node():
    """Verify source selector node adjusts intent if requested sources are unattached."""
    ctx = TenantContext(tenant_id=uuid4(), user_id=uuid4(), request_id="req-123")
    state = AgentState(
        context=ctx,
        conversation_id=uuid4(),
        message_id=uuid4(),
        user_message="Summarize policy report",
        detected_intent="document",
        knowledge_base_ids=[],
    )
    res_state = source_selector_node(state)
    assert res_state.detected_intent == "clarification"


def test_hybrid_merger_and_final_response():
    """Verify hybrid merger combines database and document results."""
    ctx = TenantContext(tenant_id=uuid4(), user_id=uuid4(), request_id="req-123")
    state = AgentState(
        context=ctx,
        conversation_id=uuid4(),
        message_id=uuid4(),
        user_message="Compare sales and policy",
        detected_intent="hybrid",
    )
    merged_state = hybrid_merger_node(state)
    final_state = final_response_node(merged_state)
    assert "No matching database records or document evidence" in final_state.final_answer
