# 06. Schema Discovery and Metadata Caching

## Goal

Discover an authorized live PostgreSQL source's schemas, tables, columns, keys, and relationships, then cache only safe metadata in the application database. Synchronization must preserve the required metadata schema, avoid copying customer business records, and give later permission and SQL phases a current tenant-scoped structural view.

## Depends On

- [x] Phase 02 preserves the Section 7.4 metadata DDL and its required defaults, foreign keys, constraints, and unique keys.
- [x] Phase 03 provides trusted tenant context and tenant-admin authorization.
- [x] Phase 05 provides a supported, healthy, active, read-only PostgreSQL connection and safe adapter lifecycle.
- [x] Phase 04 provides permission/governance rules that will later refer to discovered metadata.

## Assignment References

- [x] Sections 1, 2, 3, 4, 5 steps 2 and 4–5, 7.4, 8, 10 controls 1, 4, 7, 10, and 12, 11, 12, 13, 14, 15, and 17.

## Detailed Tasks

- [x] Implement PostgreSQL metadata introspection through the read-only adapter: enumerate approved non-system schemas, tables/views as supported table types, column names/types/ordinal/nullability, primary keys, foreign keys, and relationship targets without reading application business rows.
- [x] Exclude PostgreSQL system and administrative schemas from discovery by default, including `pg_catalog` and `information_schema`; use a documented connection-level allow-list for application schemas rather than treating all discoverable objects as promptable.
- [x] Define `POST /api/database-connections/{id}/sync-schema` as the required tenant-admin trigger. The **Baseline assumption** response is `202 Accepted` with connection ID and safe synchronization status; it does not invent a separate required job-status endpoint.
- [x] Validate active tenant ownership, tenant-admin authorization, supported PostgreSQL adapter, healthy test state, and active connection status before starting a sync. Reject untested, disabled, stale-configured, unsupported, or cross-tenant connections without exposing existence details.
- [x] Run discovery through the worker boundary when it may exceed request limits; pass only trusted tenant/connection identifiers and safe operation metadata in the job payload, then re-authorize/validate state in the worker before source access.
- [x] Gather a complete metadata snapshot before changing the application cache. On source read failure, preserve the last known cache, mark schema sync failed with a redacted reason, emit an audit event, and do not perform partial destructive reconciliation.
- [x] In one application-database transaction after a successful snapshot, upsert schemas by `(connection_id, schema_name)`, tables by `(connection_id, schema_id, table_name)`, and columns by `(table_id, column_name)` while setting redundant tenant IDs from the owned connection rather than request input.
- [x] Populate and refresh structural metadata only: descriptions/comments when safe, table type, estimated row count, primary-key column list, type/nullability/key flags, referenced schema/table/column, and timestamps. Never copy source-table contents as part of normal sync.
- [x] Preserve governance fields through refreshes: do not reset administrator-controlled table enablement/sensitivity, column sensitivity, permission grants, or mask policies merely because source discovery reruns.
- [x] Reconcile stale metadata only after a fully successful snapshot. Remove disappeared tables/columns/schemas according to the required cascade relationships, invalidate affected permission/schema-resolution caches, and write a safe audit event describing identifiers and counts rather than source values.
- [x] Preserve the core DDL default `database_tables.is_enabled = TRUE`; regardless of that default, no newly discovered object is usable by chat without an explicit effective permission from Phases 04 and 07.
- [x] Keep `database_columns.sample_values` as an empty array by default. If a future tenant explicitly enables samples, treat it as a **Baseline extension** requiring documented tenant approval, a small configured cap, sensitive-column exclusion/masking, retention/deletion rules, auditability, and no unrestricted business-record copying.
- [x] Classify source columns marked sensitive by governed policy before they can be exposed in prompts or results; do not infer that a column is safe merely because discovery succeeds. Phase 04/07 masking rules remain the authorization boundary.
- [x] Set `schema_sync_status` and `last_schema_sync_at` only from the synchronization outcome; do not equate a connection test with a successful schema cache.
- [x] Implement `GET /api/database-connections/{id}/schemas` and `GET /api/database-connections/{id}/tables` as required routes for safe cached metadata. Require tenant-admin authorization for the administrative discovery view, tenant-scope the connection, omit credentials/sample values, and bound/paginate output as a **Baseline assumption**.
- [x] Return safe stable metadata identifiers and structural fields from the listing routes; do not disclose disabled/hidden objects to non-administrative callers, raw source errors, row contents, or another tenant's cache.
- [x] Publish a metadata-cache service interface for Phase 07 that retrieves only current, enabled, tenant-owned objects and their safe relational metadata; no LLM or public client can mutate this cache directly.
- [x] Emit audit/observability data for sync requested, started, succeeded, failed, object counts, duration, adapter type, and cache version/change counts without logging source rows, sample values, connection credentials, or internal driver messages.

## Data Model Touched

- [x] Preserve `database_schemas`: UUID primary key default; tenant and connection FKs with `ON DELETE CASCADE`; non-null `schema_name`; nullable description; timestamps; and `uq_database_schema` on `(connection_id, schema_name)`.
- [x] Preserve `database_tables`: UUID primary key default; tenant/connection FKs with `ON DELETE CASCADE`; nullable schema FK with `ON DELETE CASCADE`; non-null `table_name`; non-null `table_type` default `table`; description, estimated row count, primary-key JSON default `[]`, `is_enabled` default `TRUE`, `is_sensitive` default `FALSE`, metadata JSON default `{}`, timestamps, and `uq_database_table`.
- [x] Preserve `database_columns`: UUID primary key default; tenant FK with `ON DELETE CASCADE`; table FK with `ON DELETE CASCADE`; non-null name/type; ordinal/nullability/key/sensitivity/reference fields; description; non-null `sample_values JSONB` default `[]`; timestamps; and `uq_database_column` on `(table_id, column_name)`.
- [x] Update `database_connections.schema_sync_status` and `last_schema_sync_at` only after safe lifecycle validation; retain its required tenant foreign key, encryption fields, status fields, and unique connection name.
- [x] Read and safely reconcile dependent `table_permissions` and `column_permissions` through their required cascades when metadata is truly removed; Phase 04 owns grant semantics and Phase 19 owns durable audit presentation.

## API Endpoints Touched

- [x] Implement the required `POST /api/database-connections/{id}/sync-schema` endpoint with the documented asynchronous baseline behavior and safe status response.
- [x] Implement the required `GET /api/database-connections/{id}/schemas` endpoint for tenant-admin cached-schema inspection.
- [x] Implement the required `GET /api/database-connections/{id}/tables` endpoint for tenant-admin cached table/column structural inspection.
- [x] Do not add unrequired raw-schema, sample-value, arbitrary SQL, or cross-tenant metadata endpoints; Phase 07 provides an internal permission-filtered schema contract for chat.

## Security & Permission Notes

- [x] Schema discovery uses the tenant-owned connection's read-only credentials and an allow-listed metadata query path; it never trusts a client-provided DSN, schema name, SQL fragment, tenant ID, or object ID.
- [x] Cache only source metadata needed for safe schema understanding. Customer business data, unbounded samples, query results, and result previews must not enter application tables, logs, vector storage, or audit payloads through sync.
- [x] Retain tenant predicates on every cache read/write and worker job, and invalidate resolution caches immediately after a successful metadata or connection lifecycle change.
- [x] Treat discovered metadata as sensitive: expose it only to the authorized administrative view or the internal Phase 07 resolver, mask/restrict sensitive columns, and do not make discovery alone a data-access grant.
- [x] Redact source server names, SQL diagnostics, driver stack traces, credentials, and any accidental data-bearing error content in API responses, job failures, logs, and audits.

## Testing Requirements

- [x] Unit-test PostgreSQL catalog mapping for schemas, tables, columns, primary keys, foreign keys, type/nullability fields, system-schema exclusion, and source allow-list behavior.
- [x] Integration-test a successful sync creates/upserts the required metadata records with exact tenant ownership, uniqueness behavior, status updates, and no source business rows stored.
- [x] Test repeat sync idempotency, source additions/renames/removals, full-snapshot reconciliation, cache invalidation, and failure rollback that leaves the prior cache intact.
- [x] Test that new/changed metadata does not automatically confer table/column access and that removed metadata safely invalidates dependent grants/resolved schemas.
- [x] Test default-empty sample values and future sample opt-in guards: approval required, cap enforced, sensitive values excluded/masked, and no audit/log/vector leakage.
- [x] Test all sync/list routes for tenant-admin authorization, cross-tenant ID denial, inactive/untested/unsupported connection rejection, bounded response behavior, and source-error redaction.

## Definition of Done

- [x] A healthy tenant-owned PostgreSQL source can be synchronized at runtime into a current structural metadata cache without copying customer business records.
- [x] All required schema routes preserve their Section 8 paths and return only safe, tenant-scoped cached metadata.
- [x] Sync failure is atomic from the application-cache perspective, auditable, and unable to erase valid prior metadata.
- [x] Later phases receive safe relationships and object metadata but no implicit permission grant, raw credentials, or unbounded source samples.

## Suggested Day (1–4)

Day 2
