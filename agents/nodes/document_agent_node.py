"""Document Agent node managing query rewriting, evidence retrieval, reranking, and citation generation."""

from __future__ import annotations

from sqlalchemy.orm import Session

from agents.state import AgentState
from services.document_retrieval_service import DocumentRetrievalService


def document_agent_node(state: AgentState, db: Session) -> AgentState:
    """Execute Document Agent pipeline: Query Rewriter -> Vector Retriever -> Evidence ReRanker -> Citation Generator."""
    if not state.knowledge_base_ids:
        return state

    try:
        doc_retriever = DocumentRetrievalService(db)
        evidence = doc_retriever.retrieve_evidence(
            context=state.context,
            knowledge_base_ids=state.knowledge_base_ids,
            user_query=state.user_message,
            top_k=3,
        )
        state.retrieved_evidence = evidence
        for item in evidence:
            state.sources_used.append(
                {
                    "citation_type": "document",
                    "title": item.file_name,
                    "source_reference": f"Page {item.page_number or 1}",
                    "page_number": item.page_number,
                    "relevance_score": item.score,
                    "file_name": item.file_name,
                }
            )
    except Exception as e:
        state.error_message = f"Document Agent Error: {str(e)[:150]}"

    return state
