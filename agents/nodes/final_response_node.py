"""Final response node formatting synthesis output."""

from __future__ import annotations

from agents.state import AgentState


def final_response_node(state: AgentState) -> AgentState:
    """Format and finalize agent state response."""
    if state.final_answer:
        return state

    intent = state.detected_intent
    if intent == "general":
        state.final_answer = "Hello! I am your Enterprise AI Assistant. How can I help you analyze your databases or knowledge base documents today?"
    elif intent == "clarification":
        state.final_answer = "Could you please specify which database connection or knowledge base you would like me to query?"
    elif intent == "database":
        if state.execution_envelope and state.execution_envelope.rows:
            state.final_answer = f"Found {state.execution_envelope.returned_row_count} database records. Sample data: {state.execution_envelope.rows[:2]}"
        elif state.validated_plan and state.validated_plan.validation_status == "invalid":
            state.final_answer = f"Security Validation Error: {state.validated_plan.validation_errors}"
        else:
            state.final_answer = "No records found matching your database query."
    elif intent == "document":
        if state.retrieved_evidence:
            excerpts = "\n- ".join(e.excerpt[:200] for e in state.retrieved_evidence)
            state.final_answer = f"Based on your documents:\n- {excerpts}"
        else:
            state.final_answer = "No relevant information found in selected knowledge bases."
    else:
        state.final_answer = "Processed request successfully."

    return state
