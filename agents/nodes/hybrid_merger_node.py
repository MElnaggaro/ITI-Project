"""Hybrid Merger node combining database query results and document evidence."""

from __future__ import annotations

from agents.state import AgentState


def hybrid_merger_node(state: AgentState) -> AgentState:
    """Merge database records and document evidence for hybrid intent queries."""
    if state.detected_intent != "hybrid":
        return state

    parts = []
    if state.execution_envelope and state.execution_envelope.rows:
        parts.append(
            f"Database Records ({state.execution_envelope.returned_row_count} rows): {state.execution_envelope.rows[:2]}"
        )

    if state.retrieved_evidence:
        excerpts = [f"[{e.file_name} p.{e.page_number or 1}]: {e.excerpt[:200]}" for e in state.retrieved_evidence[:2]]
        parts.append("Document Evidence:\n- " + "\n- ".join(excerpts))

    if parts:
        # We don't overwrite state.final_answer here. 
        # We let the LLM synthesize it in the graph.
        pass
    else:
        # Only set final_answer if absolutely nothing was found, short-circuiting the LLM
        state.final_answer = "No matching database records or document evidence were found for your request."

    return state
