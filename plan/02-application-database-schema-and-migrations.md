# 02. Application Database Schema & Migrations

## Goal

Create the PostgreSQL application-database foundation exactly equivalent to the Section 7 reference design: tenant identities, roles and permissions, encrypted connection metadata, safe schema metadata cache, knowledge-base/file/chunk records, conversations, messages, query execution records, citations, and audits. The migration/model layer must preserve every listed extension, field, type, nullability rule, default, key, foreign-key delete action, check/unique constraint, and explicit index while maintaining the assignment’s rule that customer business records remain in live source databases.

## Depends On

- 00 — use the Section 7 Schema Fidelity Manifest, data-residency invariant, Qdrant/pgvector decision, and extension/override policy.
- 01 — use the planned PostgreSQL, SQLAlchemy 2, Alembic, configuration, testing, and secret-handling boundaries.

## Assignment References

- Section 3 — application database responsibility and separation from live customer databases.
- Section 4 — model, repository, migration, and test structure.
- Section 7.1–7.10 — PostgreSQL reference DDL.
- Section 10 — query audit fields, filter evidence, and sensitive-data masking requirements.
- Sections 11–12 — PostgreSQL/Alembic and Qdrant service choices.
- Sections 14–15 — migration/schema deliverable, traceability, isolation, and reliable test requirements.
- Section 17 — platform-data residency and prohibition on copying all customer data.

## Detailed Tasks

- [x] Initialize the application PostgreSQL database through Alembic and SQLAlchemy 2; create the initial migration as the semantic source of truth for the full Section 7 reference schema.
- [x] Execute CREATE EXTENSION IF NOT EXISTS "uuid-ossp" before any UUID default uses uuid_generate_v4().
- [x] Execute CREATE EXTENSION IF NOT EXISTS vector before creating document_chunks.embedding VECTOR(1024).
- [x] Create tenants with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), name VARCHAR(200) NOT NULL, code VARCHAR(100) NOT NULL UNIQUE, status VARCHAR(30) NOT NULL DEFAULT 'active', settings JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW().
- [x] Create users with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, email VARCHAR(255) NOT NULL, full_name VARCHAR(255), password_hash TEXT, status VARCHAR(30) NOT NULL DEFAULT 'active', is_tenant_admin BOOLEAN NOT NULL DEFAULT FALSE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email).
- [x] Create INDEX idx_users_tenant_id ON users(tenant_id) exactly in addition to the users primary/unique indexes implied by the reference DDL.
- [x] Create roles with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, name VARCHAR(100) NOT NULL, description TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_roles_tenant_name UNIQUE (tenant_id, name).
- [x] Create user_roles with user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and PRIMARY KEY (user_id, role_id).
- [x] Create database_connections with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, created_by UUID REFERENCES users(id) ON DELETE SET NULL, name VARCHAR(200) NOT NULL, database_type VARCHAR(50) NOT NULL, host VARCHAR(255), port INTEGER, database_name VARCHAR(255), username VARCHAR(255), encrypted_password TEXT, encrypted_connection_string TEXT, ssl_enabled BOOLEAN NOT NULL DEFAULT FALSE, ssl_settings JSONB NOT NULL DEFAULT '{}'::jsonb, connection_options JSONB NOT NULL DEFAULT '{}'::jsonb, status VARCHAR(30) NOT NULL DEFAULT 'pending', last_tested_at TIMESTAMPTZ, last_test_message TEXT, schema_sync_status VARCHAR(30) DEFAULT 'pending', last_schema_sync_at TIMESTAMPTZ, is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_database_connection_name UNIQUE (tenant_id, name).
- [x] Create INDEX idx_database_connections_tenant ON database_connections(tenant_id) exactly; do not silently substitute a partial or differently ordered index.
- [x] Create database_schemas with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, connection_id UUID NOT NULL REFERENCES database_connections(id) ON DELETE CASCADE, schema_name VARCHAR(255) NOT NULL, description TEXT, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_database_schema UNIQUE (connection_id, schema_name).
- [x] Create database_tables with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, connection_id UUID NOT NULL REFERENCES database_connections(id) ON DELETE CASCADE, schema_id UUID REFERENCES database_schemas(id) ON DELETE CASCADE, table_name VARCHAR(255) NOT NULL, table_type VARCHAR(50) NOT NULL DEFAULT 'table', description TEXT, estimated_row_count BIGINT, primary_key_columns JSONB NOT NULL DEFAULT '[]'::jsonb, is_enabled BOOLEAN NOT NULL DEFAULT TRUE, is_sensitive BOOLEAN NOT NULL DEFAULT FALSE, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_database_table UNIQUE (connection_id, schema_id, table_name).
- [x] Create database_columns with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, table_id UUID NOT NULL REFERENCES database_tables(id) ON DELETE CASCADE, column_name VARCHAR(255) NOT NULL, data_type VARCHAR(100) NOT NULL, ordinal_position INTEGER, is_nullable BOOLEAN, is_primary_key BOOLEAN NOT NULL DEFAULT FALSE, is_foreign_key BOOLEAN NOT NULL DEFAULT FALSE, is_sensitive BOOLEAN NOT NULL DEFAULT FALSE, referenced_schema VARCHAR(255), referenced_table VARCHAR(255), referenced_column VARCHAR(255), description TEXT, sample_values JSONB NOT NULL DEFAULT '[]'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_database_column UNIQUE (table_id, column_name).
- [x] Create table_permissions with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, role_id UUID REFERENCES roles(id) ON DELETE CASCADE, user_id UUID REFERENCES users(id) ON DELETE CASCADE, connection_id UUID NOT NULL REFERENCES database_connections(id) ON DELETE CASCADE, table_id UUID NOT NULL REFERENCES database_tables(id) ON DELETE CASCADE, can_read BOOLEAN NOT NULL DEFAULT TRUE, can_insert BOOLEAN NOT NULL DEFAULT FALSE, can_update BOOLEAN NOT NULL DEFAULT FALSE, can_delete BOOLEAN NOT NULL DEFAULT FALSE, row_filter JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT chk_permission_subject CHECK ((role_id IS NOT NULL AND user_id IS NULL) OR (role_id IS NULL AND user_id IS NOT NULL)).
- [x] Create column_permissions with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), table_permission_id UUID NOT NULL REFERENCES table_permissions(id) ON DELETE CASCADE, column_id UUID NOT NULL REFERENCES database_columns(id) ON DELETE CASCADE, can_read BOOLEAN NOT NULL DEFAULT TRUE, can_filter BOOLEAN NOT NULL DEFAULT TRUE, can_aggregate BOOLEAN NOT NULL DEFAULT TRUE, mask_type VARCHAR(50), and CONSTRAINT uq_column_permission UNIQUE (table_permission_id, column_id).
- [x] Create knowledge_bases with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, created_by UUID REFERENCES users(id) ON DELETE SET NULL, name VARCHAR(200) NOT NULL, description TEXT, embedding_model VARCHAR(255), chunking_config JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_knowledge_base_name UNIQUE (tenant_id, name).
- [x] Create files with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, knowledge_base_id UUID REFERENCES knowledge_bases(id) ON DELETE SET NULL, uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL, original_name VARCHAR(500) NOT NULL, stored_name VARCHAR(500) NOT NULL, storage_path TEXT NOT NULL, mime_type VARCHAR(255), extension VARCHAR(30), file_size_bytes BIGINT, checksum VARCHAR(128), processing_status VARCHAR(30) NOT NULL DEFAULT 'pending', processing_error TEXT, page_count INTEGER, extracted_text_length BIGINT, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and processed_at TIMESTAMPTZ.
- [x] Create document_chunks with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, knowledge_base_id UUID NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE, file_id UUID NOT NULL REFERENCES files(id) ON DELETE CASCADE, chunk_index INTEGER NOT NULL, content TEXT NOT NULL, content_hash VARCHAR(128), page_number INTEGER, section_title TEXT, token_count INTEGER, metadata JSONB NOT NULL DEFAULT '{}'::jsonb, embedding VECTOR(1024), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and CONSTRAINT uq_document_chunk UNIQUE (file_id, chunk_index).
- [x] Preserve document_chunks.embedding as the required PostgreSQL pgvector schema/audit mirror while Phase 13 uses Qdrant as the only runtime retrieval authority; require idempotent chunk-ID synchronization on create, reprocess, and delete.
- [x] Create conversations with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE, title VARCHAR(500), status VARCHAR(30) NOT NULL DEFAULT 'active', active_connection_ids JSONB NOT NULL DEFAULT '[]'::jsonb, active_knowledge_base_ids JSONB NOT NULL DEFAULT '[]'::jsonb, settings JSONB NOT NULL DEFAULT '{}'::jsonb, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(), and last_message_at TIMESTAMPTZ.
- [x] Create messages with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE, parent_message_id UUID REFERENCES messages(id) ON DELETE SET NULL, role VARCHAR(30) NOT NULL, message_type VARCHAR(30) NOT NULL DEFAULT 'text', content TEXT NOT NULL, structured_content JSONB, detected_intent VARCHAR(50), selected_sources JSONB NOT NULL DEFAULT '[]'::jsonb, model_name VARCHAR(255), prompt_tokens INTEGER, completion_tokens INTEGER, latency_ms INTEGER, status VARCHAR(30) NOT NULL DEFAULT 'completed', error_message TEXT, and created_at TIMESTAMPTZ NOT NULL DEFAULT NOW().
- [x] Create query_executions with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, conversation_id UUID REFERENCES conversations(id) ON DELETE SET NULL, message_id UUID REFERENCES messages(id) ON DELETE SET NULL, connection_id UUID NOT NULL REFERENCES database_connections(id) ON DELETE CASCADE, generated_sql TEXT NOT NULL, normalized_sql TEXT, query_type VARCHAR(30), validation_status VARCHAR(30) NOT NULL, validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb, applied_row_filters JSONB NOT NULL DEFAULT '{}'::jsonb, referenced_tables JSONB NOT NULL DEFAULT '[]'::jsonb, referenced_columns JSONB NOT NULL DEFAULT '[]'::jsonb, execution_status VARCHAR(30), execution_time_ms INTEGER, returned_row_count INTEGER, result_preview JSONB, error_code VARCHAR(100), error_message TEXT, and created_at TIMESTAMPTZ NOT NULL DEFAULT NOW().
- [x] Create message_citations with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE, message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE, citation_type VARCHAR(30) NOT NULL, file_id UUID REFERENCES files(id) ON DELETE SET NULL, chunk_id UUID REFERENCES document_chunks(id) ON DELETE SET NULL, query_execution_id UUID REFERENCES query_executions(id) ON DELETE SET NULL, title TEXT, source_reference TEXT, page_number INTEGER, relevance_score NUMERIC(8,6), metadata JSONB NOT NULL DEFAULT '{}'::jsonb, and created_at TIMESTAMPTZ NOT NULL DEFAULT NOW().
- [x] Create audit_logs with id UUID PRIMARY KEY DEFAULT uuid_generate_v4(), tenant_id UUID REFERENCES tenants(id) ON DELETE SET NULL, user_id UUID REFERENCES users(id) ON DELETE SET NULL, action VARCHAR(100) NOT NULL, resource_type VARCHAR(100), resource_id UUID, ip_address INET, user_agent TEXT, request_id VARCHAR(100), details JSONB NOT NULL DEFAULT '{}'::jsonb, and created_at TIMESTAMPTZ NOT NULL DEFAULT NOW().
- [x] Create the migration in foreign-key-safe order: extensions; tenants; users; roles; user_roles; database_connections; database_schemas; database_tables; database_columns; table_permissions; column_permissions; knowledge_bases; files; document_chunks; conversations; messages; query_executions; message_citations; audit_logs.
- [x] Define the downgrade/reversal order child-first and review it as a development/schema test operation only; do not treat a destructive downgrade on a populated production platform as a business-data management mechanism.
- [x] Map every listed table in SQLAlchemy 2 without replacing database-enforced primary keys, unique constraints, check constraints, nullable columns, server defaults, or ON DELETE behavior with weaker application-only validation.
- [x] Use server-side UUID and timestamp defaults exactly where Section 7 supplies them; do not add an undocumented updated_at trigger as if it were in the PDF. If automatic update maintenance is later added, record it as a compatible extension and test it.
- [x] Map JSONB defaults as database defaults, preserving '{}'::jsonb versus '[]'::jsonb exactly; avoid mutable process-level default objects that differ from the database contract.
- [x] Ensure nullable fields remain nullable where the reference DDL omits NOT NULL, including database_connections.schema_sync_status, database_tables.schema_id, database_columns.is_nullable, document_chunks.embedding, and audit_logs.tenant_id/user_id.
- [x] Retain only the two explicitly declared non-unique indexes, idx_users_tenant_id and idx_database_connections_tenant, in the base schema; any additional performance index must be a separately reviewed extension with migration and test.
- [x] Place connection credentials only in database_connections.encrypted_password or encrypted_connection_string after Phase 05 encryption; never add plaintext secret columns, sample business rows, or raw connection diagnostics to the schema.
- [x] Treat database_columns.sample_values as metadata-only: Phase 06 must apply an approved small cap, sensitive-value masking, tenant approval/policy, retention, and audit controls before storage.
- [x] Treat query_executions.result_preview as absent by default and, when explicitly enabled, as redacted, bounded, retention-controlled audit metadata rather than durable customer business data.
- [x] Keep source database keys/relationship metadata in database_schemas, database_tables, and database_columns; do not copy full source tables, records, or unbounded query results into application PostgreSQL.
- [x] Validate the selected embedding provider produces exactly 1024 dimensions before document_chunks.embedding or Qdrant points are written; fail processing safely on mismatch and do not permit divergent dual-index state.
- [x] Add repository/query conventions in later phases that always scope tenant-owned tables by trusted tenant_id, including tables whose PK is addressed directly; a foreign key alone is not authorization.
- [x] Record every non-Section 7 table/field/index/trigger introduced later as an extension with owner phase, migration revision, purpose, privacy impact, and rollback/retention decision.

## Data Model Touched

- tenants: platform tenant identity, code uniqueness, status/settings, and audit timestamps.
- users: tenant-scoped credentials and tenant-admin status; uq_users_tenant_email and idx_users_tenant_id are mandatory.
- roles and user_roles: tenant roles plus the required user/role composite primary key.
- database_connections: tenant-owned encrypted live-source metadata, SSL/options, lifecycle/test/sync status, uq_database_connection_name, and idx_database_connections_tenant.
- database_schemas, database_tables, and database_columns: tenant-owned source metadata including keys, relationships, sensitivity flags, and bounded sample_values only.
- table_permissions and column_permissions: role-or-user subject grant, read/write flags, JSONB row_filter, column read/filter/aggregate flags, masking type, and required check/unique constraints.
- knowledge_bases, files, and document_chunks: tenant knowledge metadata, object references, processing state, content/chunk metadata, required VECTOR(1024), and chunk uniqueness.
- conversations and messages: tenant/user conversation ownership, selected resource arrays, conversation hierarchy, intent, source selection, model/usage/latency/status/error metadata.
- query_executions: generated/normalized SQL, validation/filter/reference evidence, controlled execution outcome, bounded preview policy, and safe error metadata.
- message_citations and audit_logs: source traceability, request metadata, tenant/user provenance, and redacted audit details.
- The complete field-level specification, every default, key, delete action, constraint, and explicit index is repeated in Detailed Tasks and canonically enumerated in the Phase 00 Schema Fidelity Manifest.

## API Endpoints Touched

- No Section 8 endpoint is implemented in this phase; it establishes the persistence contracts consumed by later endpoint phases.
- The later owners are: authentication (03), database connections (05), schema inspection (06), permission administration baseline (04), file/knowledge base routes (11–14), conversations (16), chat (15/18), and message trace routes (10/17).

## Security & Permission Notes

- PostgreSQL platform tables must use tenant_id and tenant-scoped repository predicates together; do not infer cross-tenant authorization from a caller-provided UUID or from a foreign key alone.
- Enforce the Section 7 chk_permission_subject constraint at the database layer so every table permission names exactly one role or user subject.
- Store filters as JSONB data only; Phase 07 defines a restricted filter DSL and Phase 09 compiles it into parameterized SQL AST predicates. No row_filter is executable raw SQL.
- Preserve can_insert, can_update, and can_delete defaults even though normal chat is read-only; the future permission model must not reinterpret their presence as chat write authorization.
- Mark sensitive metadata through database_tables.is_sensitive and database_columns.is_sensitive; Phase 04 onward masks it in prompts, results, logs, previews, and final answers.
- Encrypt source credentials before persistence, redact database_connections.last_test_message and all errors, and never serialize plaintext credentials into audit_logs.details, query_executions, file metadata, worker jobs, or traces.
- Enforce the source-data boundary: metadata/sample_values and approved redacted previews are limited exceptions, while business records and bulk query results remain transient in source-query flows.
- Give the application database account only the privileges necessary for the schema/application; source customer-database accounts are separately read-only and are planned in Phase 05/10.

## Testing Requirements

- [x] Add a clean-database Alembic upgrade test that creates uuid-ossp and vector and reaches the exact latest schema revision.
- [x] Add a schema-introspection contract test for all 18 tables: column names, PostgreSQL types, nullable flags, server defaults, primary keys, unique constraints, check constraints, foreign keys, and every ON DELETE action.
- [x] Assert the exact explicit indexes idx_users_tenant_id on users(tenant_id) and idx_database_connections_tenant on database_connections(tenant_id), and assert no required index was replaced by a non-equivalent definition.
- [x] Assert tenants.code, uq_users_tenant_email, uq_roles_tenant_name, uq_database_connection_name, uq_database_schema, uq_database_table, uq_database_column, uq_column_permission, uq_knowledge_base_name, and uq_document_chunk all enforce the stated unique behavior.
- [x] Assert user_roles has its exact composite primary key and table_permissions rejects both-null and both-populated role_id/user_id subjects.
- [x] Add cascade/set-null lifecycle tests for every Section 7 relationship, including self-referential messages.parent_message_id and nullable audit_logs tenant/user references.
- [x] Add server-default tests for UUID generation, JSONB object/array defaults, booleans, statuses, timestamps, and VECTOR(1024) type dimension.
- [x] Add tenant-isolation repository tests for every tenant-owned table and direct-ID lookup tests for database_connections, files, conversations, messages, citations, query executions, and audits.
- [x] Add source-data-residency tests proving schema cache samples and result previews are bounded/masked/disabled by default and that bulk source rows cannot be persisted or vectorized.
- [x] Add Qdrant/pgvector mirror tests for idempotent create, reprocess, delete, 1024-dimension validation, and failed-sync reconciliation behavior.
- [x] Add migration upgrade/downgrade tests on disposable development databases and an extension-compatibility test that prevents silent destructive schema drift.

## Definition of Done

- [x] An Alembic migration and SQLAlchemy 2 metadata define all 18 Section 7 core tables plus uuid-ossp and vector without omissions or weakened semantics.
- [x] The base schema preserves every listed field, data type, nullability rule, default, key, FK ON DELETE action, check/unique constraint, and the two explicit indexes.
- [x] document_chunks.embedding remains VECTOR(1024), Qdrant is documented as the canonical retrieval index, and synchronization/mismatch behavior has a Phase 13 owner.
- [x] The schema contains no plaintext source-credential field, copied customer business table, unbounded business-row cache, or undocumented extension.
- [x] Schema-contract, migration, relationship, tenant-isolation, data-residency, and vector-mirror tests are specified and assigned to the automated suite.

## Suggested Day (1–4)

Day 1.
