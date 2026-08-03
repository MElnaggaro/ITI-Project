# 08. Text-to-SQL Generation

## Goal

Turn a database-oriented natural-language request into a candidate SQL statement for one selected live connection, using one reusable database agent and only the request-specific schema that the authenticated user is permitted to see. This phase produces a candidate and execution parameters only; validation, row-filter injection, and execution remain separate safety boundaries.

## Depends On

- [ ] Phase 03 provides an authenticated user, active tenant context, and request identity.
- [ ] Phase 04 provides resolved roles and the policy primitives used to determine table, column, and masking permissions.
- [ ] Phase 05 provides active, tenant-owned database connections, their database_type values, and the adapter abstraction; PostgreSQL is the end-to-end baseline.
- [ ] Phase 06 provides tenant-scoped cached schemas, tables, columns, primary keys, foreign-key relationships, descriptions, and bounded approved metadata samples.
- [ ] Phase 07 provides a canonical permission-filtered schema and backend-owned row-filter references for the current user and selected connection.

## Assignment References

- [ ] Section 2: Text-to-SQL and Security capabilities.
- [ ] Section 3: Database Agent components.
- [ ] Section 5, steps 3 through 5: request classification, source selection, filtered-schema retrieval, SQL generation, validation, and execution.
- [ ] Section 6: one generic database agent rather than an agent per table, tenant, or industry.
- [ ] Sections 7.3 through 7.5: connection metadata, cached metadata, and permissions.
- [ ] Sections 10 and 15: permission exposure and safe-SQL requirements.

## Detailed Tasks

- [ ] Define an internal SQL-generation request object containing the authenticated tenant_id and user_id, one selected connection_id, the user message, the canonical permission-filtered schema, and trusted execution limits; do not accept raw schema text, permissions, or row filters from the client.
- [ ] Keep a single generic database-agent service that accepts the request object at runtime; do not create per-table, per-tenant, or industry-specific agents or prompts.
- [ ] Resolve the SQL dialect exclusively from the selected connection database_type through the adapter/dialect resolver; support PostgreSQL end to end first and keep SQL Server, MySQL, and Oracle behind explicit extension adapters.
- [ ] Reject generation when the selected connection is inactive, belongs to another tenant, has no usable schema cache, or resolves to no readable tables or columns.
- [ ] Build a bounded schema context containing only allowed schemas, enabled tables, readable columns, data types, primary keys, foreign-key relationships, approved descriptions, and strictly bounded non-sensitive metadata samples.
- [ ] Exclude disabled tables, unauthorized columns, masked raw values, connection secrets, source-database result rows, and backend row-filter expressions from the LLM context.
- [ ] Include each allowed object’s fully qualified source name and dialect-aware identifier rules so the model does not infer nonexistent tables, columns, or joins.
- [ ] Use a versioned prompt template that instructs the model to return a single candidate read-only SQL statement plus structured candidate metadata such as referenced-object candidates and bind-parameter values; keep this internal format separate from public API contracts.
- [ ] Require value placeholders and a separate bind-parameter map for user-supplied values whenever the target dialect supports them; never interpolate natural-language values into SQL text.
- [ ] Instruct the model that backend authorization owns tenant and row-level predicates; the model must not create, remove, name, or modify mandatory filters.
- [ ] Ensure the generated candidate targets exactly one connection. Defer cross-source comparison and document/database merging to the hybrid orchestrator in Phase 15.
- [ ] Capture a generation correlation ID, model/version metadata, and sanitized generation outcome for later audit linkage without logging credentials, protected samples, or unmasked sensitive values.
- [ ] Return typed, sanitized generation failures for ambiguous requests, unavailable schema, unsupported dialect features, and model failures; do not expose prompts, source connection strings, or provider stack traces.
- [ ] Define configuration for schema-context token/size limits, deterministic table and column ordering, model timeout, and retry policy so a large tenant schema cannot exhaust the request budget.

## Data Model Touched

- [ ] Read database_connections.id, tenant_id, database_type, status, is_active, and schema-sync fields without exposing encrypted credential fields.
- [ ] Read database_schemas, database_tables, and database_columns, including relationships, descriptions, sensitivity flags, and bounded sample_values.
- [ ] Read table_permissions and column_permissions only through the Phase 07 resolved-permission result.
- [ ] Prepare generated_sql, query_type, referenced_tables, and referenced_columns values for the query_executions record created by later validation and execution phases; do not add a migration in this phase.

## API Endpoints Touched

- [ ] No Section 8 endpoint is implemented directly in this phase; POST /api/chat and POST /api/chat/stream invoke this internal service later in Phase 15.
- [ ] Do not introduce a public SQL-generation endpoint. Any future administrative preview endpoint must be documented as an explicit implementation baseline rather than a Section 8 requirement.

## Security & Permission Notes

- [ ] Generate only from the server-built, tenant-scoped, permission-filtered schema and never from a client- or LLM-provided schema description.
- [ ] Treat generation output as untrusted until Phase 09 has parsed, authorized, rewritten, and revalidated it.
- [ ] Do not disclose masked columns, raw sensitive samples, source credentials, or internal authorization rules in prompts, traces, logs, or user-facing errors.
- [ ] Preserve the separation of duties: the LLM may propose SQL, while the backend owns table/column authorization, row filters, limits, and execution credentials.

## Testing Requirements

- [ ] Unit-test that a generic agent receives different permitted schemas for different users without any per-table agent configuration.
- [ ] Unit-test schema-context construction excludes unauthorized tables, columns, disabled tables, sensitive samples, row-filter definitions, credentials, and cross-tenant metadata.
- [ ] Unit-test dialect selection and deterministic failure for unsupported or inactive connections.
- [ ] Unit-test parameter extraction so user values remain bind parameters rather than interpolated SQL literals.
- [ ] Test candidate generation fixtures for joins based on cached foreign keys and for failure when an answer requires an unavailable table or column.
- [ ] Test that cross-connection requests are split for later orchestration rather than emitted as an unsafe cross-source SQL statement.

## Definition of Done

- [ ] A single internal service can create a bounded, tenant- and permission-scoped SQL candidate for a PostgreSQL connection.
- [ ] No candidate is executed, trusted, or able to carry backend row filters at this phase boundary.
- [ ] Generation logs and errors are sanitized and correlate to later query execution records.

## Suggested Day (1–4)

Day 2.
