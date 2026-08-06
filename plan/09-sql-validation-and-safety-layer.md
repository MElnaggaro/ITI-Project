# 09. SQL Validation & Safety Layer

## Goal

Convert an untrusted generated SQL candidate into an immutable, dialect-aware, read-only execution plan or reject it before it can reach a live customer database. The layer must use parsed SQL ASTs, server-owned authorization data, parameterized row filters, and enforced limits rather than keyword matching or LLM assertions.

## Depends On

- [x] Phase 05 provides connection-specific adapter and dialect capabilities.
- [x] Phase 07 provides the canonical allowed tables, columns, masks, and resolved backend-owned row-filter AST/parameter values.
- [x] Phase 08 provides an untrusted candidate SQL statement, candidate bind parameters, selected connection, and sanitized correlation metadata.

## Assignment References

- [x] Section 2: validated SQL execution using controlled credentials and limits.
- [x] Section 3: SQL Validator component.
- [x] Section 5, step 5: validate SQL and inject backend row filters before execution.
- [x] Section 7.5: table_permissions.row_filter and column permissions.
- [x] Section 10: all mandatory SQL security controls.
- [x] Section 15: permissions and unsafe/unauthorized SQL acceptance criteria.

## Detailed Tasks

- [x] Define a typed validated-query plan containing generated SQL, normalized SQL, dialect, AST-derived query type, referenced tables and columns, backend bind parameters, applied row-filter metadata, enforced row limit, and validation decision.
- [x] Parse the complete candidate with SQLGlot plus database-specific validation rules; never use keyword matching as the authorization decision.
- [x] Reject empty input, parser errors, more than one statement, SQL comments, unsupported dialect constructs, and any generated statement whose parsed form differs from the single accepted statement.
- [x] Implement a recursive AST read-only allowlist: SELECT is allowed only when every descendant is read-only; WITH is allowed only when every CTE and final query is read-only; EXPLAIN is allowed only for an underlying read-only query and must reject execution options that can run or analyze writes.
- [x] Reject INSERT, UPDATE, DELETE, MERGE, UPSERT, SELECT INTO, DDL, privilege changes, procedural execution, file import/export, attachment operations, and all other write-capable statements even when nested in CTEs, views, EXPLAIN, or dialect-specific syntax.
- [x] Reject the explicitly blocked forms from Section 10: DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE, EXEC, CALL, COPY, ATTACH, and DETACH.
- [x] Reject system schemas, information/administrative schemas unless explicitly approved by a future backend policy, and administrative or unsafe database functions.
- [x] Resolve every referenced base table, view, and column from the parsed AST, including aliases, CTEs, joins, subqueries, wildcard expansion, ordering, grouping, filtering, and aggregate expressions.
- [x] Verify every resolved base object against the Phase 07 permission-filtered schema; reject unknown, unauthorized, ambiguous, disabled, sensitive-unmasked, or cross-connection objects.
- [x] Resolve a wildcard only after expanding it to permitted columns; reject it when expansion would expose a non-readable or masked-incompatible column.
- [x] Accept only backend-provided bind parameters with approved scalar types and names; reject user- or LLM-provided identifiers, SQL fragments, and parameter values that do not match the parsed placeholder set.
- [x] Consume the canonical backend row-filter AST from Phase 07, compile it to parameterized dialect SQL, inject it into every protected base-table access, and bind its values separately from LLM output.
- [x] Reparse and revalidate the rewritten SQL after row-filter and limit injection; no executable query may bypass the final AST authorization pass.
- [x] Apply a backend-owned maximum row limit through AST rewriting, preserving a smaller user-requested LIMIT but clamping or rejecting a larger one; do not allow the LLM to remove or increase it.
- [x] Record normalized SQL, validation status, structured validation errors, applied-row-filter metadata, and AST-derived referenced objects in the validated-query plan for query_executions and audit logging.
- [x] Return stable, non-sensitive validation error codes to the orchestrator; keep parser internals, policies, filter values, and source-object details out of public error bodies.

## Data Model Touched

- [x] Read tenant-scoped database_connections, database_tables, database_columns, table_permissions, and column_permissions through the resolved Phase 07 authorization context.
- [x] Populate query_executions.generated_sql, normalized_sql, query_type, validation_status, validation_errors, applied_row_filters, referenced_tables, and referenced_columns.
- [x] Do not persist raw row-filter parameter values, credentials, or unmasked result data in query_executions or audit_logs.

## API Endpoints Touched

- [x] No Section 8 endpoint is implemented directly in this phase; validation is an internal dependency of the chat flow.
- [x] Do not expose a public validate-SQL API unless a later approved scope adds it and labels it as an implementation baseline outside Section 8.

## Security & Permission Notes

- [x] Fail closed on parser, dialect, authorization, filter-compilation, or rewrite failures.
- [x] Backend-owned authorization is authoritative: neither client input nor LLM output can add, remove, weaken, reorder, or parameterize mandatory row filters.
- [x] Enforce table, column, row, system-schema, function, statement, and result-limit controls before a query reaches the source database.
- [x] Preserve a complete but sanitized validation audit trail without leaking sensitive columns, filter values, connection details, or stack traces.

## Testing Requirements

- [x] Unit-test accepted read-only SELECT, nested read-only WITH, and EXPLAIN over a read-only query for each supported baseline dialect rule.
- [x] Unit-test rejection of data-modifying CTEs, EXPLAIN over DML, SELECT INTO, multi-statements, comments, DDL, DML, procedural calls, COPY, system schemas, and administrative functions.
- [x] Unit-test AST table/column authorization across aliases, joins, subqueries, CTEs, aggregates, and wildcard expansion.
- [x] Unit-test that unauthorized columns, unauthorized filter columns, and masked raw columns are rejected before execution.
- [x] Unit-test parameter binding and row-filter compilation with adversarial LLM SQL proving mandatory filters cannot be removed, bypassed, or broadened.
- [x] Unit-test limit injection and final-AST revalidation after every rewrite.

## Definition of Done

- [x] Every executable plan originates from a single parsed, recursively read-only AST and has passed final authorization after server-side rewrites (see [docs/ACCEPTANCE_CRITERIA_SAFE_SQL.md](file:///d:/PROJECTS/ITI%20Project/docs/ACCEPTANCE_CRITERIA_SAFE_SQL.md)).
- [x] Mandatory row filters and maximum result limits are backend-owned, parameterized, and immutable to the LLM.
- [x] Rejected SQL receives a stable sanitized status and is never sent to a source connection.

## Suggested Day (1–4)

Day 2.
