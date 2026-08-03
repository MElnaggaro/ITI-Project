"""Unified Chat Orchestrator pipeline and node execution graph."""

from __future__ import annotations

from sqlalchemy.orm import Session

from agents.classifier import classify_request
from agents.state import AgentState
from services.document_retrieval_service import DocumentRetrievalService
from services.query_execution_service import QueryExecutionService
from services.schema_resolution_service import SchemaResolutionService
from services.sql_generator_service import SQLGeneratorService
from services.sql_validator_service import SQLValidatorService


class ChatOrchestrator:
    """Orchestrates multi-intent chat pipeline across SQL and Document RAG engines."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.schema_resolver = SchemaResolutionService(db)
        self.sql_generator = SQLGeneratorService()
        self.sql_validator = SQLValidatorService()
        self.query_executor = QueryExecutionService(db)
        self.doc_retriever = DocumentRetrievalService(db)

    def run(self, state: AgentState) -> AgentState:
        """Run state machine graph for chat request."""
        # 1. Intent Classification
        state.detected_intent = classify_request(
            user_message=state.user_message,
            connection_ids=state.connection_ids,
            knowledge_base_ids=state.knowledge_base_ids,
        )

        intent = state.detected_intent

        # 2. Database Branch
        if intent in {"database", "hybrid"} and state.connection_ids:
            try:
                conn_id = state.connection_ids[0]
                state.resolved_schema = self.schema_resolver.resolve_schema(state.context, conn_id)

                if not state.resolved_schema.is_empty():
                    candidate = self.sql_generator.generate_candidate(
                        state.context, state.user_message, state.resolved_schema
                    )
                    state.generated_sql = candidate.candidate_sql

                    plan = self.sql_validator.validate_and_rewrite(
                        candidate.candidate_sql, state.resolved_schema
                    )
                    state.validated_plan = plan

                    if plan.validation_status == "valid":
                        envelope = self.query_executor.execute_plan(
                            context=state.context,
                            connection_id=conn_id,
                            validated_plan=plan,
                            resolved_schema=state.resolved_schema,
                            conversation_id=state.conversation_id,
                            message_id=state.message_id,
                        )
                        state.execution_envelope = envelope
                        state.sources_used.append(
                            {
                                "citation_type": "sql",
                                "title": "SQL Query Result",
                                "source_reference": plan.final_sql or plan.generated_sql,
                            }
                        )
            except Exception as e:
                state.error_message = f"Database pipeline error: {str(e)[:150]}"

        # 3. Document Branch
        if intent in {"document", "hybrid"} and state.knowledge_base_ids:
            try:
                evidence = self.doc_retriever.retrieve_evidence(
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
                        }
                    )
            except Exception as e:
                state.error_message = f"Document pipeline error: {str(e)[:150]}"

        # 4. Final Answer Synthesis
        state.final_answer = self._synthesize_answer(state)
        return state

    def _synthesize_answer(self, state: AgentState) -> str:
        intent = state.detected_intent

        if intent == "general":
            return "Hello! I am your AI Assistant. How can I help you analyze your databases or knowledge base documents today?"

        elif intent == "clarification":
            return "Could you please specify which database connection or knowledge base you would like me to query?"

        elif intent == "database":
            if state.execution_envelope and state.execution_envelope.rows:
                rows_summary = f"Found {state.execution_envelope.returned_row_count} records."
                return f"Based on the database query, here are the results: {rows_summary} Sample data: {state.execution_envelope.rows[:2]}"
            elif state.validated_plan and state.validated_plan.validation_status == "invalid":
                return f"I generated a database query, but it failed security validation: {state.validated_plan.validation_errors}"
            return "No records found in the database for your query."

        elif intent == "document":
            if state.retrieved_evidence:
                excerpts = "\n- ".join(e.excerpt[:200] for e in state.retrieved_evidence)
                return f"Based on your documents, here is the relevant information:\n- {excerpts}"
            return "No relevant information was found in the selected knowledge bases."

        elif intent == "hybrid":
            parts = []
            if state.execution_envelope:
                parts.append(f"Database Query Results ({state.execution_envelope.returned_row_count} rows): {state.execution_envelope.rows[:1]}")
            if state.retrieved_evidence:
                parts.append(f"Document Evidence: {state.retrieved_evidence[0].excerpt[:150]}")

            if parts:
                return "Here is the combined information:\n" + "\n".join(parts)
            return "No database records or document evidence matched your request."

        return "I have processed your request."
