# 15. Chat Orchestrator (LangGraph Agent Graph)

## Goal

Define the single LangGraph orchestration graph that turns an authenticated chat request into a grounded general, database, document, hybrid, or clarification answer. The graph must coordinate approved services only; it must never replace tenant authorization, schema filtering, SQL validation, or document-access checks with LLM judgment.

## Depends On

- [x] Phase 03 provides the authenticated user and trusted tenant context.
- [x] Phase 07 provides the request-specific permission-filtered database schema and source selections.
- [x] Phases 08, 09, and 10 provide the generic database agent, AST validation, and controlled execution path.
- [x] Phase 14 provides tenant-filtered document retrieval and reranked evidence.
- [x] Phase 16 provides the persistence interfaces that the graph will call after a response is finalized.

## Assignment References

- [x] Sections 2, 3, 5, 6, 8, 9, 10, 11, 15, and 17.

## Detailed Tasks

- [x] Create agents/state.py with a typed graph state containing trusted tenant_id and user_id, conversation ID, request message, selected connection IDs, selected knowledge-base IDs, recent history, detected intent, approved schema, SQL result handle, retrieved document evidence, citations, answer, status, timing, and safe error fields.
- [x] Create agents/graph.py and agents/nodes/ with one LangGraph graph; do not create an agent, prompt, graph branch, or static prompt per table, tenant, or industry.
- [x] Define a request-classifier node that returns exactly general, database, document, hybrid, or clarification and records a confidence/reason safe for audit.
- [x] Define a source-selector node that validates selected connection and knowledge-base IDs against the active tenant and conversation before any downstream work.
- [x] Load the conversation settings and bounded recent history through tenant-scoped persistence interfaces; never load another tenant's history by identifier alone.
- [x] Route general requests to a grounded non-data answer path, database requests to the generic database-agent path, document requests to retrieval, hybrid requests to both paths, and ambiguous requests to clarification without executing speculative SQL.
- [x] For database routing, request the current user's permission-filtered schema from Phase 07 and pass only that schema plus approved context to the generic database agent.
- [x] Make the database path call generation, validation, backend-owned filter injection, revalidation, and execution in that order; a validation failure becomes a safe response state and never reaches a source database.
- [x] Make the document path retrieve only from selected, tenant-authorized knowledge bases, rerank approved chunks, and retain source identifiers needed for citations.
- [x] Run database execution and document retrieval concurrently only for a hybrid request after authorization has completed independently for both paths.
- [x] Build a hybrid-result merger that compares or combines approved SQL outputs and document evidence without treating model-generated assertions as evidence.
- [x] Build a final-answer node that receives only approved query summaries, masked result fields, and retrieved evidence; prohibit it from receiving raw credentials, hidden schema, excluded columns, row-filter definitions, or unbounded source rows.
- [x] Generate database and document citation candidates from execution and chunk identifiers, then pass them to Phase 17 for durable citation persistence.
- [x] Normalize final response data for Section 9: message_id, answer, intent, sources_used, optional SQL execution details, and source-appropriate citations.
- [x] Record node latency, selected sources, graph status, and safe failures for Phase 19 audit/observability without logging secrets or raw restricted values.
- [x] Keep model/provider configuration behind services/llm interfaces so tests can use deterministic fakes and no provider is hard-coded into graph logic.
- [x] Add explicit cancellation, timeout, and terminal-error transitions so a failed retrieval or query does not produce a fabricated hybrid answer.

## Data Model Touched

- [x] Read and later update conversations, messages, query_executions, message_citations, audit_logs, database_connections, knowledge_bases, document_chunks, table_permissions, and column_permissions through tenant-scoped repositories.

## API Endpoints Touched

- [x] POST /api/chat prepares and invokes the non-streaming graph.
- [x] POST /api/chat/stream prepares the same graph with streaming callbacks supplied by Phase 18.

## Security & Permission Notes

- [x] Tenant and user identity originate only from authentication context, never from graph input supplied by the client or LLM.
- [x] The graph may select services but cannot bypass permission resolution, SQL validation, source read-only credentials, result limits, document filters, or masking.
- [x] A hybrid answer must cite only evidence returned by authorized branches; failure in one branch is disclosed safely rather than silently replaced with invented content.

## Testing Requirements

- [x] Unit-test intent routing for all five Section 5 intent values.
- [x] Unit-test that database-only, document-only, hybrid, general, and clarification paths invoke only their permitted dependencies.
- [x] Integration-test concurrent hybrid execution with tenant-scoped database and knowledge-base selections.
- [x] Test validation/retrieval failures, cancellations, and provider timeouts for safe terminal states with no secret or stack-trace exposure.
- [x] Test that a filtered schema excludes an unauthorized table or column from both the graph state and LLM prompt input.

## Definition of Done

- [x] One reusable graph coordinates all supported intents.
- [x] Hybrid requests combine only approved database and document outputs.
- [x] Every graph path yields a persistable response or a safe error/clarification result.
- [x] No graph path grants the LLM control of authorization or mandatory SQL filters.

## Suggested Day (1–4)

Day 4
