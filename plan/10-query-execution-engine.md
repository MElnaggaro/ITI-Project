# 10. Query Execution Engine

## Goal

Execute only the immutable validated-query plans against authorized live customer databases using read-only, time-limited, resource-bounded connections. Return transient approved results to the chat orchestrator while recording sanitized execution traceability without copying customer business data into the platform database.

## Depends On

- [ ] Phase 03 provides tenant and authenticated-user context.
- [ ] Phase 05 provides encrypted connection metadata, secure decryption boundaries, connection testing, and database adapters.
- [ ] Phase 07 provides the resolved authorization scope for the selected connection.
- [ ] Phase 09 provides a final parsed, authorized, rewritten, parameterized validated-query plan.

## Assignment References

- [ ] Section 2: controlled validated SQL execution.
- [ ] Section 3: Query Executor component and live customer databases boundary.
- [ ] Section 5, steps 5 and 9: execute approved SQL and save execution details.
- [ ] Sections 7.3 and 7.9: connection metadata and query_executions.
- [ ] Sections 10, 15, and 17: controlled credentials, limits, traceability, and no business-data copying.

## Detailed Tasks

- [ ] Define an execution request that accepts only the Phase 09 validated-query plan, authenticated tenant context, and selected connection_id; reject raw SQL, client-created filters, and unvalidated bind maps.
- [ ] Resolve the connection by tenant_id and connection_id, require active/tested status, and verify the selected source adapter supports the validated dialect.
- [ ] Decrypt credentials only inside the connection factory immediately before use; never return, serialize, log, cache, or include them in exceptions.
- [ ] Use normal-chat source credentials that are read-only and configure a read-only transaction/session where the source dialect supports it.
- [ ] Execute SQL through parameter binding only, using the final AST-rewritten SQL and combined trusted bind parameters from validation.
- [ ] Apply adapter-level connection timeout, statement timeout, cancellation, maximum returned-row count, maximum result-byte size, and bounded cursor/fetch settings from server configuration.
- [ ] Stop retrieval when a configured row or result-size limit is reached, report the bounded status to the orchestrator, and close/cancel the source operation safely.
- [ ] Keep full source results transient and scoped to the current request; do not copy customer business records to PostgreSQL, Redis, logs, vector storage, object storage, or background-job payloads.
- [ ] Create and update one tenant-scoped query_executions record for the request, including generated/normalized SQL, validation decision, applied-filter metadata, referenced objects, execution status, timing, returned row count, and sanitized error fields.
- [ ] If result_preview is retained, store only a configured small, redacted, column-masked, size-bounded preview needed for traceability; never store full customer result sets or protected raw values.
- [ ] Return a typed transient result envelope containing approved rows, column metadata, truncation status, execution ID, and safe timing information for the final-answer generator.
- [ ] Map source failures to stable statuses such as connection unavailable, timeout, canceled, permission denied, syntax/dialect mismatch, and execution failed; do not expose source hostnames, credentials, raw driver traces, or internal stack traces.
- [ ] Ensure transaction rollback where applicable, cursor cleanup, connection release, cancellation handling, and audit correlation on every success, timeout, client disconnect, and exception path.
- [ ] Keep a clear boundary for future non-read-only workflows: they require a separately approved design and cannot reuse the normal chat executor.

## Data Model Touched

- [ ] Read database_connections connection settings, status, and encrypted secret fields only within the secure connection factory.
- [ ] Create/update query_executions fields: tenant_id, conversation_id, message_id, connection_id, generated_sql, normalized_sql, query_type, validation fields, applied_row_filters, referenced objects, execution_status, execution_time_ms, returned_row_count, result_preview, error_code, error_message, and created_at.
- [ ] Emit correlated audit_logs records without credentials, unmasked sensitive values, or unrestricted source result rows.

## API Endpoints Touched

- [ ] No Section 8 endpoint is implemented directly in this phase; POST /api/chat and POST /api/chat/stream call the executor through the orchestrator in Phase 15.
- [ ] GET /api/messages/{id}/sql is implemented later as a tenant-authorized traceability read, not as a route for executing arbitrary SQL.

## Security & Permission Notes

- [ ] The executor must trust only the final Phase 09 plan and must repeat tenant/connection ownership checks at its boundary.
- [ ] Enforce least-privilege read-only source credentials, timeouts, row/result limits, safe cancellation, and redacted errors.
- [ ] Mask sensitive columns in transient result serialization, query previews, logs, and final-answer inputs according to resolved column permissions.
- [ ] The database application never becomes a replica of a customer database; all retained values are explicitly bounded and approved.

## Testing Requirements

- [ ] Integration-test PostgreSQL execution with a read-only source role for valid parameterized SELECT queries.
- [ ] Integration-test timeout, cancellation, row-limit, and result-size-limit behavior without leaking partial unbounded results.
- [ ] Test that a raw generated statement cannot reach the executor unless represented by a final validated plan.
- [ ] Test tenant/connection ownership checks, inactive connections, unsupported adapters, and safe source-error mapping.
- [ ] Test result-preview redaction and bounds, including sensitive columns and large result sets.
- [ ] Test query_executions and audit records for required traceability fields while asserting credentials, filter values, and full business rows are absent.

## Definition of Done

- [ ] The PostgreSQL baseline adapter executes only validated, parameterized, read-only plans under bounded resources.
- [ ] Every execution yields a tenant-scoped trace record and a sanitized transient result or safe failure status.
- [ ] No normal-chat path can persist or expose full customer business data or connection secrets.

## Suggested Day (1–4)

Day 2.
