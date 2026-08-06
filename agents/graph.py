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


from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import Session

from agents.nodes.classifier_node import classifier_node
from agents.nodes.database_agent_node import database_agent_node
from agents.nodes.document_agent_node import document_agent_node
from agents.nodes.final_response_node import final_response_node
from agents.nodes.hybrid_merger_node import hybrid_merger_node
from agents.nodes.source_selector_node import source_selector_node
from agents.state import AgentState


class ChatOrchestrator:
    """Orchestrates multi-intent chat pipeline using modular nodes and parallel hybrid execution."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def run(self, state: AgentState) -> AgentState:
        """Run state graph pipeline: Request -> Classifier -> Source Selector -> Agents -> Merger -> Synthesis."""
        # 1. Classifier Node
        state = classifier_node(state)

        # 2. Source Selector Node
        state = source_selector_node(state)
        intent = state.detected_intent

        # 3. Agent Execution (Parallel execution in Hybrid mode)
        if intent == "hybrid":
            with ThreadPoolExecutor(max_workers=2) as executor:
                db_future = executor.submit(database_agent_node, state, self.db)
                doc_future = executor.submit(document_agent_node, state, self.db)
                state = db_future.result()
                state = doc_future.result()
            state = hybrid_merger_node(state)
        elif intent == "database":
            state = database_agent_node(state, self.db)
        elif intent == "document":
            state = document_agent_node(state, self.db)

        # 4. Final Answer Synthesis Node
        synth_answer = self._synthesize_answer(state)
        if synth_answer:
            state.final_answer = synth_answer
        state = final_response_node(state)

        return state

    def stream_run(self, state: AgentState):
        """Run state graph pipeline and yield streaming answer tokens."""
        # 1. Classifier Node
        state = classifier_node(state)

        # 2. Source Selector Node
        state = source_selector_node(state)
        intent = state.detected_intent
        yield {"event": "intent", "data": intent}

        # 3. Agent Execution
        if intent == "hybrid":
            with ThreadPoolExecutor(max_workers=2) as executor:
                db_future = executor.submit(database_agent_node, state, self.db)
                doc_future = executor.submit(document_agent_node, state, self.db)
                state = db_future.result()
                state = doc_future.result()
            state = hybrid_merger_node(state)
        elif intent == "database":
            state = database_agent_node(state, self.db)
        elif intent == "document":
            state = document_agent_node(state, self.db)

        # 4. Final Answer Synthesis Node with Streaming
        if intent in ("general", "clarification"):
            synth_answer = ""
            state.final_answer = synth_answer
            state = final_response_node(state)
            yield {"event": "done", "state": state}
            return

        sql_context = None
        if state.execution_envelope and state.execution_envelope.rows:
            sql_context = f"Generated SQL: {state.generated_sql}\nRows ({state.execution_envelope.returned_row_count}): {state.execution_envelope.rows[:5]}"

        doc_context = None
        if state.retrieved_evidence:
            doc_context = "\n".join([f"[{e.file_name} p.{e.page_number or 1}]: {e.excerpt}" for e in state.retrieved_evidence[:10]])

        try:
            from services.llm.ollama_service import OllamaLLMService
            ollama_svc = OllamaLLMService()
            if ollama_svc.is_enabled():
                accumulated_answer = ""
                for chunk_text in ollama_svc.stream_synthesize_answer(
                    user_message=state.user_message,
                    intent=intent,
                    sql_context=sql_context,
                    document_context=doc_context,
                ):
                    accumulated_answer += chunk_text
                    ans_clean = ollama_svc.clean_thinking_tags(accumulated_answer)
                    if "Final answer:" in ans_clean:
                        ans_clean = ans_clean.split("Final answer:")[-1].strip()
                    
                    yield {"event": "answer", "data": ans_clean}
                
                state.final_answer = ollama_svc.clean_thinking_tags(accumulated_answer)
        except Exception as e:
            state.final_answer = f"Error during streaming synthesis: {e}"

        state = final_response_node(state)
        yield {"event": "done", "state": state}


    def _synthesize_answer(self, state: AgentState) -> str:
        intent = state.detected_intent

        if intent in ("general", "clarification"):
            return ""

        sql_context = None
        if state.execution_envelope and state.execution_envelope.rows:
            sql_context = f"Generated SQL: {state.generated_sql}\nRows ({state.execution_envelope.returned_row_count}): {state.execution_envelope.rows[:5]}"

        doc_context = None
        if state.retrieved_evidence:
            doc_context = "\n".join([f"[{e.file_name} p.{e.page_number or 1}]: {e.excerpt}" for e in state.retrieved_evidence[:10]])

        # Try Ollama (qwen3.5:4b) Answer Synthesis if available
        try:
            from services.llm.ollama_service import OllamaLLMService

            ollama_svc = OllamaLLMService()
            if ollama_svc.is_enabled():
                answer = ollama_svc.synthesize_answer(
                    user_message=state.user_message,
                    intent=intent,
                    sql_context=sql_context,
                    document_context=doc_context,
                )
                if answer:
                    ans_clean = answer.strip()
                    if "Final answer:" in ans_clean:
                        ans_clean = ans_clean.split("Final answer:")[-1].strip()
                    return ans_clean
        except Exception as e:
            # Capture the error on the state so the final_response_node can format a fallback
            if not state.error_message:
                state.error_message = str(e)
            elif str(e) not in state.error_message:
                state.error_message += f"\n{str(e)}"

        return ""


