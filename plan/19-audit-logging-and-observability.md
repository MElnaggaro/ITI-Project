# 19. Audit Logging and Observability

## Goal

Provide tenant-aware auditability and operational visibility for authentication, connections, schema access, file processing, chat, SQL validation/execution, citations, and failures without exposing credentials, sensitive values, source records, prompts, or internal stack traces.

## Depends On

- [x] Phase 02 provides audit_logs and the timestamp/status fields on core entities.
- [x] Phase 03 provides authenticated user, tenant context, request IDs, and safe exception handling.
- [x] Phases 05 through 18 provide the lifecycle events, execution metadata, worker jobs, and chat outcomes to observe.

## Assignment References

- [x] Sections 2, 7.3, 7.6, 7.8, 7.9, 7.10, 10, 11, 12, 14, and 15.

## Detailed Tasks

- [x] Map every audit_logs field exactly: id, tenant_id, user_id, action, resource_type, resource_id, ip_address, user_agent, request_id, details, and created_at.
- [x] Create an audit logging service with a typed event vocabulary for login, token refresh, connection CRUD/test, schema sync, permission change, file lifecycle, knowledge-base action, conversation action, chat lifecycle, SQL validation/execution, citation access, and security denial.
- [x] Capture trusted tenant/user/request context automatically; callers must not supply arbitrary tenant_id or user_id values.
- [x] Define structured details allow-lists per event type and reject or redact encrypted credentials, connection strings, authorization headers, raw source rows, document payloads, hidden schema, row-filter values, and sensitive query literals.
- [x] Record generated SQL, normalized SQL, validation decisions, referenced objects, execution status, and timing in query_executions as required by Section 10; log only identifiers/status summaries in audit_logs unless a protected policy permits more.
- [x] Add request ID propagation through FastAPI requests, Celery jobs, LangGraph nodes, database adapters, object storage, Qdrant operations, and SSE events.
- [x] Configure structured application logging with redaction filters before logs leave the process.
- [x] Configure Prometheus metrics for HTTP request count/latency/errors, authentication failures, connection tests, schema-sync jobs, upload/processing jobs, retrieval latency, graph paths, SQL validation denials, query duration/row limits, SSE connections, and worker failures.
- [x] Configure OpenTelemetry traces across API, worker, graph, source-database, Qdrant, MinIO, Redis, and LLM provider boundaries; include tenant-safe attributes only.
- [x] Plan Grafana dashboards for service health, queue backlog, error rate, p95 latency, document-processing status, SQL safety denials, database execution duration, and tenant-safe workload trends.
- [x] Define health and readiness checks for the API and each required dependency; preserve the Section 4 health route as a future implementation artifact.
- [x] Define alert candidates for repeated authorization denials, unsafe SQL attempts, source connection failures, job backlog, vector/index drift, high error rate, and dependency unavailability.
- [x] Define retention/access controls for audit data and prevent routine users from querying another tenant's audit history.
- [x] Ensure public API error responses use stable user-safe messages while protected logs/traces contain correlation IDs and diagnostics.

## Data Model Touched

- [x] audit_logs.
- [x] query_executions validation/execution fields.
- [x] database_connections test/sync status fields.
- [x] files processing fields.
- [x] messages latency/status/error fields.

## API Endpoints Touched

- [x] GET /api/health or the Section 4 health-route equivalent is planned as a baseline operational endpoint and labeled as non-Section-8.
- [x] Every Section 8 endpoint emits tenant-scoped audit and telemetry events.

## Security & Permission Notes

- [x] Audit data is sensitive and must be tenant-scoped, access-controlled, and redacted.
- [x] Observability must never become a secondary copy of customer business data or connection secrets.
- [x] Log security denials and validation decisions without leaking the denied resource's protected details.

## Testing Requirements

- [x] Unit-test redaction filters for credentials, tokens, connection strings, sensitive columns, and raw query result values.
- [x] Integration-test request ID propagation through an API request, worker job, graph, query execution, and SSE finalization.
- [x] Test required query execution audit fields are captured for success, validation rejection, timeout, and source error.
- [x] Test health/readiness responses under dependency failure without stack traces.
- [x] Test tenant audit records cannot be retrieved or correlated by another tenant.

## Definition of Done

- [x] All critical lifecycle actions produce structured, tenant-safe audit events (see [docs/ACCEPTANCE_CRITERIA_RELIABILITY.md](file:///d:/PROJECTS/ITI%20Project/docs/ACCEPTANCE_CRITERIA_RELIABILITY.md)).
- [x] Metrics, traces, and dashboards have planned ownership and redaction safeguards.
- [x] Errors are observable to operators without exposing secrets to users or logs.

## Suggested Day (1–4)

Day 4
