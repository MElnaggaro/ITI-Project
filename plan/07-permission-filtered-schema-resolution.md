# 07. Permission-Filtered Schema Resolution

## Goal

Resolve one request-specific, tenant-scoped schema for the reusable database agent from current metadata and deterministic permissions. The resolver must expose only approved tables, columns, relationships, permitted operations, and safe masking instructions while retaining backend-owned row filters for later AST injection.

## Depends On

- [x] Phase 03 provides immutable authenticated `TenantContext`.
- [x] Phase 04 provides tenant-consistent roles, grants, precedence, column policy, masks, and validated row-filter definitions.
- [x] Phase 05 provides healthy, active, supported tenant-owned source connections.
- [x] Phase 06 provides current cached schemas, tables, columns, key relationships, and metadata lifecycle state.

## Assignment References

- [x] Sections 1, 2, 3, 4, 5 steps 2 and 4–5, 6, 7.4–7.5, 8, 10 controls 1, 2, 7–10, and 12, 13, 14, 15, and 17.

## Detailed Tasks

- [x] Define an internal `ResolvedSchema` contract consumed by the single generic database agent: tenant-scoped connection identity/dialect, approved schema/table identifiers, enabled relationships, safe descriptions, column IDs/names/types, permitted projection/filter/aggregate flags, and masking instruction references.
- [x] Keep the `ResolvedSchema` contract request-specific and short-lived; it must never be a permanent agent, prompt, or permission cache per table, tenant, database, or industry.
- [x] Resolve requested connection IDs only through `TenantContext`, require each connection to be active, healthy, synchronized, supported, and owned by the tenant, and reject missing/duplicate/cross-tenant selections with a safe authorization result.
- [x] Load user roles through tenant-scoped membership joins and load only current enabled metadata for those connections. Do not allow client-provided schema/table/column names to expand the resolved object set.
- [x] Apply the direct-user precedence rule from Phase 04: one direct grant for a table is authoritative; a direct `can_read = false` denies the table even when a role allows it; otherwise use matching role grants only.
- [x] Apply the additive-role rule from Phase 04 when no direct grant exists: any readable role grant exposes the table, and its row filters are combined as a fully parenthesized OR policy expression. No readable grant means no table in the resolved schema.
- [x] Apply column rules independently after table resolution: project only explicitly readable columns; allow a filter-only column only in approved predicates; allow aggregation only for readable columns with `can_aggregate`; omit all other columns from the agent contract and reject their later SQL use.
- [x] Include primary/foreign-key relationship metadata only when both participating tables and the necessary join columns are permitted. Do not reveal hidden table names, column names, sample values, descriptions, or joins through an authorized neighbor.
- [x] Decorate sensitive columns with the effective backend mask policy and prevent sample values for them from entering the agent prompt. A sensitive column with no explicit policy uses `redact`; the final masking service, validator, executor, logs, previews, and answer generator must honor the same policy.
- [x] Define row filters as a restricted JSON DSL: a group is `{"all": [filters...]}`, `{"any": [filters...]}`, or `{"not": filter}`; a leaf is `{"column_id": "<cached-column-uuid>", "operator": "eq|ne|lt|lte|gt|gte|in|not_in|is_null|is_not_null", "value": <typed literal | typed literal array | {"context": "tenant.id" | "user.id"}>}`.
- [x] Enforce a **Baseline assumption** maximum filter depth of 8 and 50 leaf clauses, require non-empty arrays, match every leaf to its table and permitted filter column, type-check values against cached source types, and limit `in`/`not_in` arrays to a configured safe bound.
- [x] Reject all filter representations outside the DSL: raw SQL, column-name strings, qualified identifiers, functions, casts, arithmetic, wildcards, joins, subqueries, comments, client/LLM parameters, free-form context keys, and arbitrary JSON properties.
- [x] Resolve `tenant.id` and `user.id` placeholders only from verified `TenantContext` at execution preparation time. No client value, request body value, LLM output, chat history, or source result may substitute a policy placeholder.
- [x] Define the connection source-scope setting as a **Baseline assumption** stored in existing `connection_options`: `tenant_isolated` is the default and requires documented administrator confirmation; `shared` requires every readable table to have a non-empty valid row filter containing a trusted contextual predicate. Missing/ambiguous scope or a shared table without that filter fails closed.
- [x] Compile the effective filters to SQLGlot AST predicate objects plus bound parameters using cached identifier mappings; do not render them to raw SQL strings or include them in the LLM prompt.
- [x] Publish a handoff contract to Phases 08–10: the LLM receives only `ResolvedSchema`; SQL validation resolves every referenced object against it; the backend injects the compiled filter into every referenced table scope/alias, preserves Boolean and outer-join semantics, then revalidates the final AST before execution.
- [x] Require mandatory predicates for nested queries, CTE bodies, derived tables, aliases, and joins that reference protected tables. Do not rely on a textual predicate search or an LLM promise that it applied a filter.
- [x] Prevent stale authorization from widening access: initially resolve effective permissions from current tenant-scoped application data for every chat request. Add a cache only after it has a tenant/user/connection-specific invalidation strategy for role, grant, metadata, connection, and tenant-status changes.
- [x] Return no row-filter JSON, encryption material, raw sample values, source results, hidden metadata, or other users' grants from the resolver. Record only safe policy IDs/versions for audit and later query-execution traceability.
- [x] Define a safe no-access outcome for an empty permitted schema so the orchestrator can request clarification or explain lack of access without generating speculative SQL.

## Data Model Touched

- [x] Read `tenants` and `users` through trusted context and active-status checks; do not receive tenant ownership from API payloads.
- [x] Read `roles`, `user_roles`, `table_permissions`, and `column_permissions` to compute effective access using the documented direct-user and additive-role rules.
- [x] Read `database_connections`, `database_schemas`, `database_tables`, and `database_columns` only when they belong to the active tenant and are current/enabled for the selected connection.
- [x] Preserve all Section 7 permission defaults, unique constraints, foreign-key actions, and row-filter JSON storage; compile policy from them without changing their required core schema.
- [x] Use existing `database_connections.connection_options` only for the documented baseline source-scope configuration; do not introduce raw row-filter SQL or a new unscoped per-tenant setting.
- [x] Provide safe policy/execution identifiers to the future `query_executions.applied_row_filters`, `referenced_tables`, and `referenced_columns` records without persisting source business data or literal sensitive values.

## API Endpoints Touched

- [x] This phase adds no new Section 8 endpoint; it supplies an internal authorization contract used by required `POST /api/chat` and `POST /api/chat/stream` in later phases.
- [x] Consume only the explicit **Baseline assumption** permission-management interfaces from Phase 04 for grant mutation; do not expose an endpoint that returns raw effective filters, hidden schema, or another user's resolved schema.
- [x] Preserve `GET /api/database-connections/{id}/schemas` and `GET /api/database-connections/{id}/tables` as administrative cache views from Phase 06, not a substitute for request-specific chat authorization.

## Security & Permission Notes

- [x] The resolver is the authorization boundary before SQL generation: no table, column, relationship, row filter, or mask decision may be delegated to an LLM or inferred from a source database response.
- [x] Backend-owned filter ASTs and parameters remain opaque to the LLM. The database agent cannot create, remove, relax, reorder, or replace mandatory filters, even if it generates an otherwise valid read-only query.
- [x] Application tenant ownership limits connection selection; `shared` source data additionally requires immutable contextual row filtering. A source connection never becomes cross-tenant merely because a caller knows its ID.
- [x] Keep sensitive schema annotations and values out of prompts where possible, and enforce masking consistently in subsequent validator, executor, audit, preview, citation, and final-answer stages.
- [x] Fail closed for malformed policy, unsupported filter type, missing metadata, ambiguous grant subject, stale/inactive connection, invalid alias mapping, or any inability to attach a required predicate safely.

## Testing Requirements

- [x] Unit-test empty-schema denial, tenant-scoped connection selection, disabled/inactive/unsynchronized connection denial, direct-user allow/deny precedence, additive role grants, and no-grant default denial.
- [x] Unit-test column projection/filter/aggregate combinations, hidden relationship suppression, sensitive-column redaction defaults, and exclusion of samples/hidden identifiers from the agent contract.
- [x] Unit-test every row-filter DSL operator, typed literal/context binding, nesting, maximum depth/count, empty groups, unknown keys, invalid column IDs, cross-table columns, unfilterable columns, raw SQL, and incompatible values.
- [x] Test `tenant_isolated` and `shared` source-scope behavior, including failure for a shared readable table that lacks a valid trusted contextual predicate.
- [x] Test AST compilation and mandatory-filter injection against simple queries, aliases, joins, outer joins, nested subqueries, derived tables, and read-only CTEs; verify Boolean grouping is preserved and parameters remain backend-owned.
- [x] Test adversarial LLM SQL that omits, weakens, aliases around, or attempts to neutralize a required predicate; final validation must reject or reapply policy before any source execution.
- [x] Integration-test two tenants and multiple roles so no resolved schema, policy identifier, cached result, query record, or error reveals another tenant's tables, columns, filters, or source data.

## Definition of Done

- [x] The one generic database agent can receive a deterministic, request-specific allowed schema without a per-table or per-tenant agent design.
- [x] Every exposed table, column, relationship, operation, mask, and row predicate has an explicit tenant-scoped authorization basis (see [docs/ACCEPTANCE_CRITERIA_PERMISSIONS.md](file:///d:/PROJECTS/ITI%20Project/docs/ACCEPTANCE_CRITERIA_PERMISSIONS.md)).
- [x] Row filters have a documented constrained grammar, direct/role precedence, trusted-context binding, parameterized AST compilation, and fail-closed behavior.
- [x] Later SQL phases can validate and execute only against the resolved schema while keeping mandatory filters outside LLM control.

## Suggested Day (1–4)

Day 2
