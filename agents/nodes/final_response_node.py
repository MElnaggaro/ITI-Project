"""Final response node formatting synthesis output."""

from __future__ import annotations

from agents.state import AgentState


def final_response_node(state: AgentState) -> AgentState:
    """Format and finalize agent state response with guaranteed grounded data fallback."""
    is_refusal_or_unhelpful = False
    if state.final_answer:
        lower = state.final_answer.lower()
        refusal_phrases = [
            "no information",
            "i don't have",
            "i do not have",
            "cannot provide",
            "need more information",
            "how you can do it in sql",
            "there is no information",
            "does not contain any specific details",
        ]
        if any(p in lower for p in refusal_phrases):
            is_refusal_or_unhelpful = True

    if state.final_answer and not is_refusal_or_unhelpful:
        return state

    intent = state.detected_intent
    if intent == "general":
        state.final_answer = "Hello! I am your Enterprise AI Assistant. How can I help you analyze your databases or knowledge base documents today?"
    elif intent == "clarification":
        state.final_answer = "Could you please specify which database connection or knowledge base you would like me to query?"
    elif intent == "database":
        if state.execution_envelope and state.execution_envelope.rows:
            formatted_rows = "\n".join(f"• {row}" for row in state.execution_envelope.rows[:5])
            state.final_answer = f"Found {state.execution_envelope.returned_row_count} matching record(s) in database:\n{formatted_rows}"
        elif state.validated_plan and state.validated_plan.validation_status == "invalid":
            state.final_answer = f"Security Validation Error: {state.validated_plan.validation_errors}"
        else:
            state.final_answer = "No records found matching your database query."
    elif intent == "document":
        if state.retrieved_evidence:
            excerpts = "\n---\n".join(f"• [{e.file_name} p.{e.page_number or 1}]: {e.excerpt[:250]}" for e in state.retrieved_evidence[:3])
            state.final_answer = f"Based on your uploaded documents:\n{excerpts}"
    elif intent == "hybrid":
        parts = []
        if state.execution_envelope and state.execution_envelope.rows:
            formatted_rows = "\n".join(f"• {row}" for row in state.execution_envelope.rows[:5])
            parts.append(f"Database Records ({state.execution_envelope.returned_row_count} rows):\n{formatted_rows}")
        if state.retrieved_evidence:
            excerpts = "\n".join(f"• [{e.file_name} p.{e.page_number or 1}]: {e.excerpt[:250]}" for e in state.retrieved_evidence[:3])
            parts.append(f"Document Knowledge Context:\n{excerpts}")
        if parts:
            state.final_answer = "\n\n".join(parts)
        else:
            state.final_answer = "No matching database records or document evidence were found for your request."
    elif not state.final_answer:
        state.final_answer = "Processed request successfully."

    return state
