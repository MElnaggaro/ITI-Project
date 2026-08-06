"""Database Agent node managing schema resolution, SQL generation, validation, and execution."""

from __future__ import annotations

from sqlalchemy.orm import Session

from agents.state import AgentState
from services.connection_router_service import ConnectionRouterService
from services.query_execution_service import QueryExecutionService
from services.schema_resolution_service import SchemaResolutionService
from services.sql_generator_service import SQLGeneratorService
from services.sql_validator_service import SQLValidatorService


def database_agent_node(state: AgentState, db: Session) -> AgentState:
    """Execute Database Agent pipeline: Schema Retriever -> SQL Generator -> SQL Validator -> Query Executor."""
    if not state.database_connection_ids:
        return state

    try:
        # Route to the best connection (including active tenant fallback)
        router = ConnectionRouterService(db)
        conn_id = router.select_best_connection(state.user_message, state.database_connection_ids)

            
        if not conn_id:
            state.error_message = "No valid database connection could be selected."
            return state
        schema_resolver = SchemaResolutionService(db)
        state.resolved_schema = schema_resolver.resolve_schema(state.context, conn_id)

        if state.resolved_schema and not state.resolved_schema.is_empty():
            sql_generator = SQLGeneratorService()
            candidate = sql_generator.generate_candidate(
                state.context, state.user_message, state.resolved_schema
            )
            state.generated_sql = candidate.candidate_sql

            sql_validator = SQLValidatorService(dialect=state.resolved_schema.database_type)
            plan = sql_validator.validate_and_rewrite(
                candidate.candidate_sql, state.resolved_schema
            )
            state.validated_plan = plan

            # Audit validation decision (Control 21)
            from services.audit_service import AuditService
            audit_svc = AuditService(db)
            audit_svc.log_event(
                context=state.context,
                action="sql_validation_decision",
                resource_type="database_connection",
                resource_id=conn_id,
                details={
                    "generated_sql": candidate.candidate_sql,
                    "normalized_sql": plan.normalized_sql,
                    "query_type": plan.query_type,
                    "validation_status": plan.validation_status,
                    "validation_errors": plan.validation_errors,
                    "referenced_tables": plan.referenced_tables,
                    "referenced_columns": plan.referenced_columns,
                },
            )

            if plan.validation_status == "valid":
                query_executor = QueryExecutionService(db)
                envelope = query_executor.execute_plan(
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
                        "table": plan.referenced_tables[0] if plan.referenced_tables else None,
                    }
                )
    except Exception as e:
        error_str = str(e)
        if state.detected_intent == "hybrid" and "LLM could not generate SQL" in error_str:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning("Gracefully ignoring SQL failure in Hybrid mode. Error: %s", error_str)
        else:
            state.error_message = f"Database Agent Error: {error_str[:150]}"

    return state
