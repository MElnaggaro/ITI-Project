# 05. Live Database Connections

## Goal

Implement tenant-administrator management of encrypted, runtime live-source connections while keeping credentials, connection tests, and source access tightly controlled. PostgreSQL is the fully supported end-to-end source adapter baseline; the other adapter paths are explicit future extension points, not claimed support.

## Depends On

- [x] Phase 01 provides configuration, encrypted-secret/key-management seams, Redis/Celery boundaries, and structured logging.
- [x] Phase 02 preserves the Section 7.3 `database_connections` DDL.
- [x] Phase 03 provides trusted tenant context and tenant-admin authorization.
- [x] Phase 04 provides the policy foundation that later constrains how a connected source may be used.

## Assignment References

- [x] Sections 1, 2, 3, 4, 5 steps 1–2, 7.3, 8, 10 controls 7 and 11, 11, 12, 13, 14, 15, and 17.

## Detailed Tasks

- [x] Define a `BaseSourceAdapter` contract for validating a connection configuration, producing a safe source client, testing connectivity, discovering metadata, resolving dialect details, and disposing resources; Phase 06 owns discovery and later phases own SQL execution.
- [x] Implement and test `PostgreSQLAdapter` as the only end-to-end supported source-database adapter baseline. Keep SQL Server, MySQL, and Oracle adapter modules/interfaces as explicit extension paths that return a safe unsupported status until independently implemented and tested.
- [x] Define the required `POST /api/database-connections` create flow for tenant administrators: validate a typed PostgreSQL configuration, enforce network policy before storage, encrypt supplied credentials/connection string, set required ownership fields from `TenantContext`, and store a pending, inactive-to-chat connection until test and schema sync succeed.
- [x] Define the required `GET /api/database-connections` and `GET /api/database-connections/{id}` flows with tenant-scoped list/detail queries, safe pagination/filtering as a **Baseline assumption**, and responses that never return `encrypted_password`, `encrypted_connection_string`, raw passwords, or SSL secret material.
- [x] Define the required `PUT /api/database-connections/{id}` flow so credential or network changes are re-encrypted, invalidate the prior test/schema state, set `status` and `schema_sync_status` back to pending, and require a new successful test and sync before chat can use the connection.
- [x] Define the required `DELETE /api/database-connections/{id}` flow as tenant-admin-only removal of platform metadata and encrypted credentials; it must never issue a destructive command to the live source database. Audit the deletion and rely on the required application-DB cascades only after ownership verification.
- [x] Define the required `POST /api/database-connections/{id}/test` flow: decrypt credentials only in memory, establish a time-limited TLS-capable connection using read-only source credentials, perform a minimal non-business-data health probe such as `SELECT 1`, safely dispose resources, and update `last_tested_at`, `last_test_message`, and status with a redacted result.
- [x] Treat supported source credentials as read-only for normal chat and metadata access. Reject a configuration that declares elevated source credentials unless an explicitly approved future workflow exists; do not use stored permission flags as a reason to grant write-capable source access.
- [x] Define status vocabulary as a **Baseline assumption**: `pending`, `testing`, `healthy`, `failed`, and `disabled`; retain `is_active` as the additional explicit operator switch and require both active/healthy state plus a successful schema sync before chat selection.
- [x] Encrypt secrets with envelope encryption or an equivalent managed-key boundary, bind ciphertext additional authenticated data to tenant and connection identity, rotate/re-encrypt safely, and keep plaintext lifetime limited to the in-memory operation that needs it.
- [x] Validate and normalize host, port, database name, SSL options, and typed PostgreSQL connection options. Block connection strings or hostnames targeting loopback, link-local, metadata-service, Unix-socket, and other disallowed destinations; enforce deployment egress allow-lists and DNS/IP revalidation to reduce SSRF and DNS-rebinding risk.
- [x] Require TLS according to a deployment policy, validate `ssl_enabled` and `ssl_settings` as structured input, and redact host/driver diagnostics to the amount safe for the tenant administrator.
- [x] Apply connect, authentication, socket, statement, and overall request timeouts; bound retries; close every source connection/pool deterministically; and translate driver failures into stable safe API codes without stack traces or credential fragments.
- [x] Store only application connection metadata and encrypted credentials. Do not copy business tables, rows, query results, or live-source schema samples during creation or testing.
- [x] Reserve the required schema synchronization route for Phase 06; connection CRUD/test must not pretend a test establishes an authorized, current schema cache.
- [x] Publish a tenant-scoped connection lookup that later phases can use only after confirming connection ownership, supported adapter status, `is_active`, successful test state, and current schema-sync state.
- [x] Emit safe audit events for create, update, test, disable, and delete with actor, connection ID, adapter type, status transition, and request ID, omitting credentials, raw connection strings, and verbose driver failures.

## Data Model Touched

- [x] Preserve `database_connections` exactly as Section 7.3 specifies: UUID primary key default; tenant FK with `ON DELETE CASCADE`; nullable `created_by` FK with `ON DELETE SET NULL`; name/type/host/port/database/username fields; encrypted password and connection-string fields; non-null SSL/configuration JSON defaults; status and test/sync timestamps/messages; non-null `is_active` default; timestamps; and `uq_database_connection_name`.
- [x] Preserve `idx_database_connections_tenant` and use it with the tenant predicate for administration and later source selection.
- [x] Set `tenant_id` and `created_by` server-side from `TenantContext`; never accept either as trusted API input and never serialize encrypted fields back to a client.
- [x] Update only required lifecycle fields on test/update/sync handoffs; Phase 06 owns cached metadata writes and the final schema-sync completion timestamp/status.
- [x] Read related `database_schemas`, `database_tables`, `table_permissions`, `query_executions`, and audit records only through tenant-scoped paths before destructive lifecycle actions.

## API Endpoints Touched

- [x] Implement the required `POST /api/database-connections` endpoint for tenant-admin creation with a safe PostgreSQL baseline request and redacted response.
- [x] Implement the required `GET /api/database-connections` and `GET /api/database-connections/{id}` endpoints with tenant-scoped safe metadata only.
- [x] Implement the required `PUT /api/database-connections/{id}` and `DELETE /api/database-connections/{id}` endpoints with tenant-admin checks, lifecycle invalidation, safe cleanup, and audit events.
- [x] Implement the required `POST /api/database-connections/{id}/test` endpoint with controlled read-only connectivity testing and redacted status reporting.
- [x] Leave `POST /api/database-connections/{id}/sync-schema`, `GET /api/database-connections/{id}/schemas`, and `GET /api/database-connections/{id}/tables` to Phase 06 without changing their Section 8 method/path contract.

## Security & Permission Notes

- [x] Only a tenant administrator may create, view administrative detail for, edit, test, disable, delete, or synchronize a tenant connection; a tenant administrator cannot target another tenant's connection by guessed UUID.
- [x] Do not log, audit, return, cache, vectorize, or persist plaintext credentials, raw connection strings, source rows, or source result previews during connection management.
- [x] Defend outbound connection testing as a privileged SSRF-sensitive operation with host/IP controls, TLS validation, timeouts, limited concurrency, and audited status transitions.
- [x] Keep source credentials read-only and separate from the application PostgreSQL credentials. An application tenant boundary does not make an arbitrary source host safe to contact.
- [x] Do not expose detailed network, authentication, TLS, driver, or source-server diagnostics to clients; preserve a redacted diagnostic for authorized administrators and a safe code for all others.

## Testing Requirements

- [x] Unit-test typed PostgreSQL configuration validation, adapter selection, unsupported-adapter rejection, encryption/decryption boundaries, AAD tenant binding, and redaction utilities.
- [x] Integration-test create/list/get/update/delete/test with two tenants and verify every ID lookup remains tenant-scoped.
- [x] Test that test requests use read-only credentials, a minimal probe, configured timeouts, resource cleanup, and no business-data retrieval.
- [x] Test host/port policy rejection for loopback, link-local, metadata-service, malformed, and DNS-rebinding scenarios, plus safe TLS and driver failures.
- [x] Test that credential changes invalidate test/schema state and that inactive, failed, unsupported, or unsynchronized connections cannot be selected for chat.
- [x] Test logs, audits, OpenAPI examples, exceptions, list responses, and detail responses for absence of plaintext or encrypted secret fields and raw source errors.

## Definition of Done

- [x] A tenant administrator can securely store, list, inspect, update, test, and delete a PostgreSQL source connection at runtime without source-code changes.
- [x] Connection lifecycle state prevents untested, stale, inactive, cross-tenant, or unsupported sources from reaching chat workflows.
- [x] Connection management protects source credentials and never copies customer business data into platform storage.
- [x] Non-PostgreSQL adapter paths are visibly extension points, not falsely advertised as supported functionality.

## Suggested Day (1–4)

Day 1
