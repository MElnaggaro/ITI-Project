# 00. Overview & Roadmap

## System Summary

This roadmap delivers a secure, multi-tenant backend through which authenticated users can add supported live business databases at runtime, upload documents into tenant knowledge bases, and ask database, document, or hybrid questions through one conversational interface. The application database owns identities, permissions, encrypted connection metadata, schema metadata, files, conversations, citations, query audits, and limited approved metadata samples; customer business records remain in the source database and are used only during authorized, time-bounded query execution. A single reusable database agent receives a permission-filtered schema per request, while the document path retrieves tenant-filtered evidence from uploaded files; the orchestrator combines only approved outputs into grounded, traceable answers.

## Planning Boundaries and Invariants

- The assignment PDF is the product authority; this roadmap controls planning format; selections not imposed by the PDF are marked as Baseline assumption.
- This planning pass creates roadmap Markdown only. Future Phase 01 may scaffold the project, but this pass must not create source code, migrations, configuration, infrastructure, or tests outside plan/.
- Preserve every Section 7 core entity and control semantically. A migration or ORM representation may differ syntactically, but it must not remove or rename a core entity, omit a field/default/constraint/index/delete action, or weaken its behavior. Necessary additions are documented as extensions.
- Build one generic database agent, never a table-, tenant-, database-, or industry-specific permanent agent. It receives only the schema, tables, columns, and row predicates the current user is allowed to use.
- Customer business records never enter the application database, vector store, durable cache, or logs. Only bounded, masked, tenant-approved metadata samples and redacted audit previews may be retained; live query results are transient.
- Treat tenant context as trusted server-side authentication state, never a client-supplied tenant selector. Scope every repository lookup, object key, cache key, background job, vector search filter, citation, audit record, and resource-ID lookup to that context.
- SQL is parsed and safety-checked as an AST with SQLGlot plus dialect rules, then executed through read-only source credentials with limits and timeouts. The LLM cannot author, replace, remove, or weaken backend-owned predicates.

## Ordered Table of Contents

| Phase | Roadmap file | Focus |
|---|---|---|
| 00 | plan/00-overview-and-roadmap.md | Cross-requirement map, contracts, defaults, and implementation order. |
| 01 | plan/01-environment-and-repo-setup.md | Future repository structure, local configuration boundary, and deployment-service plan. |
| 02 | plan/02-application-database-schema-and-migrations.md | PostgreSQL reference schema, SQLAlchemy mappings, Alembic migration contract, and schema tests. |
| 03 | plan/03-authentication-and-tenant-context.md | Authentication, trusted tenant context, and user identity. |
| 04 | plan/04-roles-and-permission-model-foundations.md | Role/user grants, permission-administration baseline, and fail-closed authorization. |
| 05 | plan/05-live-database-connections.md | Encrypted runtime connection CRUD, testing, dialect resolution, and adapter boundary. |
| 06 | plan/06-schema-discovery-and-metadata-caching.md | Safe source-schema discovery and bounded metadata caching. |
| 07 | plan/07-permission-filtered-schema-resolution.md | Request-specific allowed schemas, columns, masks, and compiled row-filter policy. |
| 08 | plan/08-text-to-sql-generation.md | Generic database-agent prompting and constrained SQL generation. |
| 09 | plan/09-sql-validation-and-safety-layer.md | AST validation, immutable predicate injection, and unsafe-SQL rejection. |
| 10 | plan/10-query-execution-engine.md | Controlled source execution, results handling, and query-execution records. |
| 11 | plan/11-file-upload-and-object-storage.md | Tenant-scoped supported-file upload and original/artifact storage. |
| 12 | plan/12-document-parsing-and-chunking.md | Parsing, status handling, chunk creation, and background processing. |
| 13 | plan/13-embeddings-and-vector-store.md | 1024-dimensional embeddings, Qdrant indexing, and pgvector mirror integrity. |
| 14 | plan/14-knowledge-base-management-and-retrieval.md | Knowledge-base management, tenant-filtered retrieval, and reranking. |
| 15 | plan/15-chat-orchestrator-langgraph-agent-graph.md | LangGraph flow for general, database, document, hybrid, and clarification turns. |
| 16 | plan/16-conversation-and-messaging-persistence.md | Conversation/history handling and durable message persistence. |
| 17 | plan/17-citations-and-traceability.md | Source-specific citations and answer-to-evidence/query traceability. |
| 18 | plan/18-streaming-chat-api-sse.md | SSE streaming contract and non-streaming/streaming chat surfaces. |
| 19 | plan/19-audit-logging-and-observability.md | Audit events, metrics, tracing, safe diagnostics, and latency capture. |
| 20 | plan/20-security-hardening-and-multi-tenant-isolation-tests.md | Cross-cutting isolation, secrets, SQL-hardening, and adversarial tests. |
| 21 | plan/21-automated-testing-suite.md | Unit, integration, schema-contract, and acceptance test suites. |
| 22 | plan/22-documentation-and-submission-packaging.md | Submission artifacts, deployment documentation, architecture explanation, and disclosure. |

## Four-Day Delivery Map

| Day | Phases | Required checkpoint and pacing rationale |
|---|---|---|
| Day 1 | 01, 02, 03, 05 | The repository and required services are planned; PostgreSQL schema and tenant authentication exist; a tenant administrator can create, encrypt, test, and securely store a supported connection. |
| Day 2 | 04, 06, 07, 08, 09, 10 | Permission APIs/foundations, safe metadata discovery, filtered schema resolution, generic SQL generation, parser validation, and controlled execution produce validated results for a permitted database question. |
| Day 3 | 11, 12, 13, 14, 17 | A supported file is stored, parsed, chunked, embedded, retrieved, and cited within a tenant knowledge base. |
| Day 4 | 15, 16, 18, 19, 20, 21, 22 | Hybrid orchestration, conversations, SSE, audits, security/integration tests, container packaging, documentation, and submission artifacts are complete. |

## Requirement Traceability Matrix

### Sections 1–2: objective and required capabilities

| PDF requirement | Owner phase(s) | Verification artifact |
|---|---|---|
| Secure, scalable backend for authenticated chat over live databases and uploaded documents | 01, 03, 15, 20, 21 | Architecture test plan and end-to-end authenticated chat scenario. |
| Add a supported database connection at runtime without source-code changes | 05, 21 | Runtime PostgreSQL connection CRUD/test integration test with no application redeploy. |
| Discover schemas while keeping business data in the source database | 06, 20, 21 | Discovery integration test plus storage/log inspection showing metadata-only persistence. |
| Upload and process PDF, Word, Excel, CSV, and text files | 11, 12, 21 | One processing test per supported file family and safe failure test. |
| Generate safe SQL from a natural-language question | 07, 08, 09, 10, 21 | Permitted-question integration test and parser/authorization test evidence. |
| Retrieve relevant document chunks through vector search | 12, 13, 14, 21 | Tenant-filtered retrieval and citation integration test. |
| Combine structured results and document evidence into one grounded answer | 15, 17, 18, 21 | Hybrid answer test with database and document citations. |
| Apply tenant, role, table, column, and row-level permissions | 03, 04, 07, 09, 20, 21 | Cross-tenant, hidden-table/column, masked-field, and row-filter adversarial tests. |
| Store conversations, citations, query executions, and audit records | 02, 16, 17, 19, 21 | Persistence/schema-contract test and traceability lookup test. |
| Live connection capability: encrypted, validated, available only to authorized chats | 03, 05, 07, 20, 21 | Credential-redaction, connection-test, authorization, and chat-selection tests. |
| Schema discovery capability: read schemas/tables/columns/keys/relationships and cache approved metadata | 05, 06, 20, 21 | Adapter discovery fixture with keys/relationships and approved-sample bounds. |
| File-ingestion capability: parse, chunk, embed, and index uploaded knowledge-base files | 11, 12, 13, 14, 21 | Background-processing lifecycle and searchable-index tests. |
| Text-to-SQL capability: select an allowed schema, generate SQL, execute validated SQL through controlled credentials/limits | 07, 08, 09, 10, 21 | Allowed-schema prompt snapshot and controlled execution test. |
| Document-chat capability: retrieve selected-file evidence with document citations | 14, 15, 17, 21 | Document-only answer with file/page citation test. |
| Hybrid-chat capability: orchestrate source retrieval and combine outputs | 15, 17, 18, 21 | Parallel-capable hybrid workflow test. |
| Security capability: apply permissions and backend filters before execution; LLM cannot bypass them | 04, 07, 09, 20, 21 | Tampered SQL/filter test proving fail-closed rejection. |

### Sections 3–6: architecture, project structure, orchestration, and agent rule

| PDF requirement | Owner phase(s) | Verification artifact |
|---|---|---|
| FastAPI gateway with authentication/tenant context, connection/schema management, file processing, and conversation/streaming API | 01, 03, 05, 06, 11, 16, 18 | Router/application inventory and endpoint integration suite. |
| LangGraph orchestrator with classifier, selector, database path, document-RAG path, hybrid merger, and final-answer generator | 15, 21 | Graph-state/unit tests and workflow trace. |
| Database agent components: schema retriever, SQL generator, validator, and executor | 07, 08, 09, 10, 21 | Database-turn integration trace showing each safety boundary. |
| Document RAG components: query rewriter, vector retriever, and evidence reranker | 12, 13, 14, 21 | Retrieval/reranking tests with tenant filters. |
| Application DB, vector DB, file store, and live source databases have distinct data responsibilities | 01, 02, 05, 11, 13, 20 | Architecture diagram and data-residency tests. |
| Recommended Section 4 source-tree modules and root artifacts are represented or have a documented equivalent | 01, 22 | Repository-tree manifest checked during packaging. |
| Authenticate and resolve active tenant/user at the start of every chat request | 03, 15, 20 | Authentication dependency and impersonation-rejection test. |
| Load conversation, selected connections/knowledge bases, and recent history | 05, 14, 16, 15 | Selected-resource authorization and history-window test. |
| Classify each request as general, database, document, hybrid, or clarification | 15, 21 | Intent-contract tests covering all five values. |
| Resolve user-permitted tables and columns before database generation | 04, 07, 08, 20 | Hidden schema/column prompt and execution tests. |
| Database flow retrieves filtered schema, generates SQL, validates it, injects backend filters, and executes it | 07, 08, 09, 10, 21 | Ordered workflow trace and immutable-filter test. |
| Document flow retrieves and reranks chunks from selected knowledge bases | 14, 15, 21 | Selected-knowledge-base retrieval test. |
| Hybrid flow runs database and document work in parallel where safe | 15, 21 | Trace showing concurrent independent branches and safe join. |
| Final answer uses approved outputs only; persist question, answer, SQL details, citations, latency, and audit event | 15, 16, 17, 19, 21 | Persisted answer trace and rejected-unapproved-output test. |
| Stream using SSE when requested | 18, 21 | Content-type/event-order test and safe stream-error test. |
| One generic database agent receives a request-specific permission-filtered schema | 07, 08, 15, 20 | Architecture review plus two-tenant/multi-schema test proving no per-table agent. |

### Section 7: application-database reference design

Every detailed Section 7 item is owned by Phase 02 and verified by the schema-contract suite in Phase 21; the Section 7 Schema Fidelity Manifest below is the item-level traceability record. Downstream phases listed there own behavioral use of the same table. No Section 7 entity may be silently represented as an untracked extension or omitted because it is not immediately used by an endpoint.

### Sections 8–9: endpoint and chat-contract requirements

The API and Chat-Contract Manifest below maps each exact route, request/response member, intent value, and citation shape to its owner and verification.

### Section 10: mandatory SQL safety controls

| PDF requirement | Owner phase(s) | Verification artifact |
|---|---|---|
| Expose only permitted tables and columns | 04, 07, 08, 20, 21 | Prompt/context and execution tests for forbidden tables/columns. |
| Use SQLGlot/parser plus database-specific rules, never keywords alone | 09, 21 | AST test matrix including dialect fixtures. |
| Block multi-statements and comments | 09, 20, 21 | Semicolon/comment injection tests. |
| Block system schemas and administrative functions | 09, 20, 21 | System-schema/admin-function rejection tests. |
| Allow read-only queries by default | 09, 10, 21 | Valid SELECT test through read-only source credentials. |
| Block DDL and destructive DML without a separate approved workflow | 09, 20, 21 | Rejection tests for DROP, TRUNCATE, ALTER, CREATE, GRANT, REVOKE, EXEC, CALL, COPY, ATTACH, and DETACH. |
| Apply row limits, execution timeouts, and result-size limits | 05, 09, 10, 20, 21 | Timeout, row cap, and result payload cap tests. |
| Inject tenant/row predicates from backend authorization rules | 04, 07, 09, 20, 21 | Parameterized AST-injection and precedence tests. |
| Never let the LLM create, remove, or modify a mandatory security filter | 07, 08, 09, 20, 21 | Predicate-removal, alias, subquery, and prompt-injection tests. |
| Use read-only source credentials for normal chat | 05, 10, 20, 21 | Source-credential privilege inspection and attempted-write test. |
| Log generated/normalized SQL, validation decisions, status, and referenced objects | 02, 09, 10, 19, 21 | Query-execution/audit record assertions. |
| Mask sensitive columns in prompts, results, logs, and final answers | 04, 07, 08, 10, 15, 19, 20, 21 | End-to-end masking test across every output channel. |

### Sections 11–17: stack, deployment, pacing, deliverables, acceptance, and residency

| PDF requirement | Owner phase(s) | Verification artifact |
|---|---|---|
| Recommended stack: FastAPI, PostgreSQL, SQLAlchemy 2/Alembic, LangGraph, queue, Redis, vector store, object storage, SQLGlot, Docling, SSE, Prometheus/Grafana/OpenTelemetry | 01 and applicable 02–19 phases | Decision ledger, dependency/configuration manifest, and service smoke suite. |
| Suggested deployment services: api, worker, postgres, redis, qdrant, minio, prometheus, grafana | 01, 12, 13, 19, 22 | Compose/service-health manifest and packaging verification. |
| Four-day sequence and checkpoints | 00–22 | This delivery map plus phase definition-of-done checks. |
| Complete modular backend source code | 01, 22 | Repository-tree and submission checklist. |
| Migration files or complete schema.sql | 02, 22 | Alembic upgrade/schema-contract verification. |
| Secret-free .env.example | 01, 22 | Secret-scanning and placeholder review. |
| Dockerfile and docker-compose.yml | 01, 22 | Build/compose validation. |
| README setup, migration, run, test, and API instructions | 22 | Fresh-environment documentation run-through. |
| OpenAPI documentation and example requests | 03, 05, 06, 11, 14, 16, 18, 22 | Generated OpenAPI and example-request contract checks. |
| Validator and permission unit tests | 04, 07, 09, 21 | Unit-test suite. |
| Connection, discovery, file, database-chat, document-chat, and hybrid-chat integration tests | 05, 06, 11–15, 21 | Integration-test suite. |
| Security tests proving unauthorized tables, columns, rows, and destructive SQL are blocked | 04, 07, 09, 20, 21 | Security-test suite. |
| Architecture explanation and diagram | 00, 22 | README architecture section/diagram review. |
| Acceptance: tenant isolation | 03, 04, 05–19, 20, 21 | Cross-tenant resource, job, cache, vector, and audit tests. |
| Acceptance: runtime supported connections require no source-code change | 05, 21 | Runtime PostgreSQL connection test. |
| Acceptance: prompt/execution reveal only approved schemas, tables, columns, and rows | 04, 07–10, 20, 21 | Authorization boundary tests. |
| Acceptance: unsafe/unauthorized SQL is rejected before source access | 09, 10, 20, 21 | Pre-execution rejection and no-source-call assertion. |
| Acceptance: supported files are parsed, indexed, searchable, and cited | 11–14, 17, 21 | Per-format processing/retrieval/citation test. |
| Acceptance: hybrid answer combines database calculation and uploaded-file evidence | 15, 17, 18, 21 | Hybrid response contract test. |
| Acceptance: every answer traces to SQL records and/or chunks | 02, 16, 17, 19, 21 | Citation/query-execution back-reference test. |
| Acceptance: failures expose clear status but no secrets/internal stack traces | 03, 05, 09–12, 18–20, 21 | Error-redaction and failure-state tests. |
| Acceptance: another developer can run from README | 01, 22 | Clean setup rehearsal. |
| Individual work: independent work and acknowledgement of documentation, external code, references, and AI tools | 22 | README disclosure review. |
| Architecture principle: application DB stores platform data only; live customer DB holds business data; vector DB holds document embeddings; object store holds files/artifacts | 01, 02, 05, 11, 13, 20, 22 | Architecture diagram and residency test/audit. |

## Section 7 Schema Fidelity Manifest

### Preservation rule and migration boundary

The PDF calls this a reference design that may be extended, but its core entities and controls must remain. Phase 02 will create an initial PostgreSQL migration in dependency order, use SQLAlchemy 2 mappings that preserve the listed database semantics, and add schema-contract tests that introspect the resulting database. Any later extra table, field, index, or trigger must be named as an extension in its owning phase. No implicit update trigger is assumed for updated_at columns because the reference DDL supplies insert defaults only; a later update-maintenance mechanism, if selected, is an explicit compatible extension.

### Required extensions

| Extension | Required behavior | Owner and verification |
|---|---|---|
| uuid-ossp | Create if absent before UUID defaults use uuid_generate_v4(). | 02; migration upgrade and default-introspection test. |
| vector | Create if absent before document_chunks.embedding VECTOR(1024). | 02, 13; extension/type and 1024-dimension contract test. |

### Core tables, exact fields, keys, delete actions, constraints, and indexes

| Table | Exact columns, types, nullability, and defaults | Keys, relationships, constraints, indexes, downstream owner, and verification |
|---|---|---|
| tenants | id UUID NOT NULL DEFAULT uuid_generate_v4(); name VARCHAR(200) NOT NULL; code VARCHAR(100) NOT NULL; status VARCHAR(30) NOT NULL DEFAULT 'active'; settings JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; UNIQUE code. Used by 03–20. Verify exact columns/defaults/unique constraint in 21. |
| users | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; email VARCHAR(255) NOT NULL; full_name VARCHAR(255) NULL; password_hash TEXT NULL; status VARCHAR(30) NOT NULL DEFAULT 'active'; is_tenant_admin BOOLEAN NOT NULL DEFAULT FALSE; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email); INDEX idx_users_tenant_id ON users(tenant_id). Used by 03–05, 16, 19. Verify FK action, constraint, and index in 21. |
| roles | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; name VARCHAR(100) NOT NULL; description TEXT NULL; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; CONSTRAINT uq_roles_tenant_name UNIQUE (tenant_id, name). Used by 04, 07. Verify in 21. |
| user_roles | user_id UUID NOT NULL; role_id UUID NOT NULL; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | Composite PK (user_id, role_id); user_id → users.id ON DELETE CASCADE; role_id → roles.id ON DELETE CASCADE. Used by 04, 07. Verify composite key and both delete actions in 21. |
| database_connections | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; created_by UUID NULL; name VARCHAR(200) NOT NULL; database_type VARCHAR(50) NOT NULL; host VARCHAR(255) NULL; port INTEGER NULL; database_name VARCHAR(255) NULL; username VARCHAR(255) NULL; encrypted_password TEXT NULL; encrypted_connection_string TEXT NULL; ssl_enabled BOOLEAN NOT NULL DEFAULT FALSE; ssl_settings JSONB NOT NULL DEFAULT '{}'::jsonb; connection_options JSONB NOT NULL DEFAULT '{}'::jsonb; status VARCHAR(30) NOT NULL DEFAULT 'pending'; last_tested_at TIMESTAMPTZ NULL; last_test_message TEXT NULL; schema_sync_status VARCHAR(30) NULL DEFAULT 'pending'; last_schema_sync_at TIMESTAMPTZ NULL; is_active BOOLEAN NOT NULL DEFAULT TRUE; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; created_by → users.id ON DELETE SET NULL; CONSTRAINT uq_database_connection_name UNIQUE (tenant_id, name); INDEX idx_database_connections_tenant ON database_connections(tenant_id). Used by 05–10, 15–17, 19. Verify all nullable fields, defaults, constraint, index, and FK actions in 21. |
| database_schemas | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; connection_id UUID NOT NULL; schema_name VARCHAR(255) NOT NULL; description TEXT NULL; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; connection_id → database_connections.id ON DELETE CASCADE; CONSTRAINT uq_database_schema UNIQUE (connection_id, schema_name). Used by 06–08. Verify in 21. |
| database_tables | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; connection_id UUID NOT NULL; schema_id UUID NULL; table_name VARCHAR(255) NOT NULL; table_type VARCHAR(50) NOT NULL DEFAULT 'table'; description TEXT NULL; estimated_row_count BIGINT NULL; primary_key_columns JSONB NOT NULL DEFAULT '[]'::jsonb; is_enabled BOOLEAN NOT NULL DEFAULT TRUE; is_sensitive BOOLEAN NOT NULL DEFAULT FALSE; metadata JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; connection_id → database_connections.id ON DELETE CASCADE; schema_id → database_schemas.id ON DELETE CASCADE; CONSTRAINT uq_database_table UNIQUE (connection_id, schema_id, table_name). Used by 06–10. Verify in 21. |
| database_columns | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; table_id UUID NOT NULL; column_name VARCHAR(255) NOT NULL; data_type VARCHAR(100) NOT NULL; ordinal_position INTEGER NULL; is_nullable BOOLEAN NULL; is_primary_key BOOLEAN NOT NULL DEFAULT FALSE; is_foreign_key BOOLEAN NOT NULL DEFAULT FALSE; is_sensitive BOOLEAN NOT NULL DEFAULT FALSE; referenced_schema VARCHAR(255) NULL; referenced_table VARCHAR(255) NULL; referenced_column VARCHAR(255) NULL; description TEXT NULL; sample_values JSONB NOT NULL DEFAULT '[]'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; table_id → database_tables.id ON DELETE CASCADE; CONSTRAINT uq_database_column UNIQUE (table_id, column_name). Used by 06–10. Verify restricted-sample policy separately in 06/20 and DDL in 21. |
| table_permissions | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; role_id UUID NULL; user_id UUID NULL; connection_id UUID NOT NULL; table_id UUID NOT NULL; can_read BOOLEAN NOT NULL DEFAULT TRUE; can_insert BOOLEAN NOT NULL DEFAULT FALSE; can_update BOOLEAN NOT NULL DEFAULT FALSE; can_delete BOOLEAN NOT NULL DEFAULT FALSE; row_filter JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; role_id → roles.id ON DELETE CASCADE; user_id → users.id ON DELETE CASCADE; connection_id → database_connections.id ON DELETE CASCADE; table_id → database_tables.id ON DELETE CASCADE; CONSTRAINT chk_permission_subject CHECK ((role_id IS NOT NULL AND user_id IS NULL) OR (role_id IS NULL AND user_id IS NOT NULL)). Used by 04, 07, 09. Verify check/FK actions in 21. |
| column_permissions | id UUID NOT NULL DEFAULT uuid_generate_v4(); table_permission_id UUID NOT NULL; column_id UUID NOT NULL; can_read BOOLEAN NOT NULL DEFAULT TRUE; can_filter BOOLEAN NOT NULL DEFAULT TRUE; can_aggregate BOOLEAN NOT NULL DEFAULT TRUE; mask_type VARCHAR(50) NULL. | PK id; table_permission_id → table_permissions.id ON DELETE CASCADE; column_id → database_columns.id ON DELETE CASCADE; CONSTRAINT uq_column_permission UNIQUE (table_permission_id, column_id). Used by 04, 07–10. Verify in 21. |
| knowledge_bases | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; created_by UUID NULL; name VARCHAR(200) NOT NULL; description TEXT NULL; embedding_model VARCHAR(255) NULL; chunking_config JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; created_by → users.id ON DELETE SET NULL; CONSTRAINT uq_knowledge_base_name UNIQUE (tenant_id, name). Used by 11–15. Verify in 21. |
| files | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; knowledge_base_id UUID NULL; uploaded_by UUID NULL; original_name VARCHAR(500) NOT NULL; stored_name VARCHAR(500) NOT NULL; storage_path TEXT NOT NULL; mime_type VARCHAR(255) NULL; extension VARCHAR(30) NULL; file_size_bytes BIGINT NULL; checksum VARCHAR(128) NULL; processing_status VARCHAR(30) NOT NULL DEFAULT 'pending'; processing_error TEXT NULL; page_count INTEGER NULL; extracted_text_length BIGINT NULL; metadata JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); processed_at TIMESTAMPTZ NULL. | PK id; tenant_id → tenants.id ON DELETE CASCADE; knowledge_base_id → knowledge_bases.id ON DELETE SET NULL; uploaded_by → users.id ON DELETE SET NULL. Used by 11–14, 17. Verify in 21. |
| document_chunks | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; knowledge_base_id UUID NOT NULL; file_id UUID NOT NULL; chunk_index INTEGER NOT NULL; content TEXT NOT NULL; content_hash VARCHAR(128) NULL; page_number INTEGER NULL; section_title TEXT NULL; token_count INTEGER NULL; metadata JSONB NOT NULL DEFAULT '{}'::jsonb; embedding VECTOR(1024) NULL; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; knowledge_base_id → knowledge_bases.id ON DELETE CASCADE; file_id → files.id ON DELETE CASCADE; CONSTRAINT uq_document_chunk UNIQUE (file_id, chunk_index). Used by 12–15, 17. Verify vector dimension, unique constraint, and cascade paths in 13/21. |
| conversations | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; user_id UUID NOT NULL; title VARCHAR(500) NULL; status VARCHAR(30) NOT NULL DEFAULT 'active'; active_connection_ids JSONB NOT NULL DEFAULT '[]'::jsonb; active_knowledge_base_ids JSONB NOT NULL DEFAULT '[]'::jsonb; settings JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(); last_message_at TIMESTAMPTZ NULL. | PK id; tenant_id → tenants.id ON DELETE CASCADE; user_id → users.id ON DELETE CASCADE. Used by 15–19. Verify in 21. |
| messages | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; conversation_id UUID NOT NULL; parent_message_id UUID NULL; role VARCHAR(30) NOT NULL; message_type VARCHAR(30) NOT NULL DEFAULT 'text'; content TEXT NOT NULL; structured_content JSONB NULL; detected_intent VARCHAR(50) NULL; selected_sources JSONB NOT NULL DEFAULT '[]'::jsonb; model_name VARCHAR(255) NULL; prompt_tokens INTEGER NULL; completion_tokens INTEGER NULL; latency_ms INTEGER NULL; status VARCHAR(30) NOT NULL DEFAULT 'completed'; error_message TEXT NULL; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; conversation_id → conversations.id ON DELETE CASCADE; parent_message_id → messages.id ON DELETE SET NULL. Used by 15–19. Verify self-reference and all defaults in 21. |
| query_executions | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; conversation_id UUID NULL; message_id UUID NULL; connection_id UUID NOT NULL; generated_sql TEXT NOT NULL; normalized_sql TEXT NULL; query_type VARCHAR(30) NULL; validation_status VARCHAR(30) NOT NULL; validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb; applied_row_filters JSONB NOT NULL DEFAULT '{}'::jsonb; referenced_tables JSONB NOT NULL DEFAULT '[]'::jsonb; referenced_columns JSONB NOT NULL DEFAULT '[]'::jsonb; execution_status VARCHAR(30) NULL; execution_time_ms INTEGER NULL; returned_row_count INTEGER NULL; result_preview JSONB NULL; error_code VARCHAR(100) NULL; error_message TEXT NULL; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; conversation_id → conversations.id ON DELETE SET NULL; message_id → messages.id ON DELETE SET NULL; connection_id → database_connections.id ON DELETE CASCADE. Used by 09, 10, 17, 19. Verify redacted/retention-controlled preview behavior in 10/20 and DDL in 21. |
| message_citations | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NOT NULL; message_id UUID NOT NULL; citation_type VARCHAR(30) NOT NULL; file_id UUID NULL; chunk_id UUID NULL; query_execution_id UUID NULL; title TEXT NULL; source_reference TEXT NULL; page_number INTEGER NULL; relevance_score NUMERIC(8,6) NULL; metadata JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE CASCADE; message_id → messages.id ON DELETE CASCADE; file_id → files.id ON DELETE SET NULL; chunk_id → document_chunks.id ON DELETE SET NULL; query_execution_id → query_executions.id ON DELETE SET NULL. Used by 17–19. Verify citations remain tenant-scoped and source-specific in 21. |
| audit_logs | id UUID NOT NULL DEFAULT uuid_generate_v4(); tenant_id UUID NULL; user_id UUID NULL; action VARCHAR(100) NOT NULL; resource_type VARCHAR(100) NULL; resource_id UUID NULL; ip_address INET NULL; user_agent TEXT NULL; request_id VARCHAR(100) NULL; details JSONB NOT NULL DEFAULT '{}'::jsonb; created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(). | PK id; tenant_id → tenants.id ON DELETE SET NULL; user_id → users.id ON DELETE SET NULL. Used by 19, 20. Verify redaction and nullable SET NULL behavior in 21. |

The only explicitly declared non-unique indexes in the reference DDL are idx_users_tenant_id and idx_database_connections_tenant. PostgreSQL indexes implied by primary keys and unique constraints must remain as consequences of those constraints; any additional performance index is an explicitly documented extension with a migration and regression test.

## API and Chat-Contract Manifest

### Section 8 required endpoints

| Exact method and path | Owner phase(s) | Contract verification |
|---|---|---|
| POST /api/auth/login | 03 | Authentication response/error integration tests. |
| POST /api/auth/refresh | 03 | Refresh-token rotation/validation tests. |
| GET /api/auth/me | 03 | Trusted user/tenant/role resolution test. |
| POST /api/database-connections | 05 | Tenant-admin encrypted-connection create test. |
| GET /api/database-connections | 05 | Tenant-scoped list test. |
| GET /api/database-connections/{id} | 05 | Authorized resource lookup test. |
| PUT /api/database-connections/{id} | 05 | Tenant-admin update/redaction test. |
| DELETE /api/database-connections/{id} | 05 | Tenant-scoped deletion/status test. |
| POST /api/database-connections/{id}/test | 05 | Timeout-safe connection-test integration test. |
| POST /api/database-connections/{id}/sync-schema | 06 | Metadata-only sync test. |
| GET /api/database-connections/{id}/schemas | 06 | Tenant/connection-scoped schema-list test. |
| GET /api/database-connections/{id}/tables | 06 | Tenant/connection-scoped table-list test. |
| POST /api/files/upload | 11 | Supported-format upload/ownership test. |
| GET /api/files | 11 | Tenant-scoped file-list test. |
| GET /api/files/{id} | 11 | Authorized file metadata/download access test. |
| DELETE /api/files/{id} | 11, 13 | Storage/index cleanup and tenant-isolation test. |
| POST /api/files/{id}/reprocess | 12, 13 | Idempotent parser/embed reprocess test. |
| POST /api/knowledge-bases | 14 | Tenant-admin/member create policy test. |
| GET /api/knowledge-bases | 14 | Tenant-scoped list test. |
| POST /api/knowledge-bases/{id}/files | 11, 14 | Knowledge-base association authorization test. |
| POST /api/conversations | 16 | Tenant/user-owned conversation creation test. |
| GET /api/conversations | 16 | Tenant/user-visible conversation list test. |
| GET /api/conversations/{id} | 16 | Conversation ownership/history test. |
| DELETE /api/conversations/{id} | 16 | Tenant-scoped cleanup/retention test. |
| POST /api/chat | 15, 17 | Non-streaming Section 9 response-contract test. |
| POST /api/chat/stream | 18 | SSE event-order/final-contract test. |
| GET /api/messages/{id}/citations | 17 | Source-specific citation authorization test. |
| GET /api/messages/{id}/sql | 10, 17 | Authorized query-execution trace lookup test. |

### Baseline permission-management interface, not a Section 8 requirement

Section 4 contains a permissions route and Section 13 calls for table/column permission APIs, but Section 8 does not prescribe paths or payloads. Phase 04 therefore owns the following Baseline assumption and must expose it as extra documented OpenAPI surface rather than claim it is assignment-mandated:

| Baseline method and path | Baseline payload/behavior | Verification |
|---|---|---|
| POST /api/permissions/table-grants | Tenant-admin creates one grant with exactly one subject (role_id or user_id), connection_id, table_id, can_read/can_insert/can_update/can_delete, row_filter, and zero or more column grants. | Subject check constraint, tenant ownership, and invalid-filter rejection tests. |
| GET /api/permissions/table-grants | Tenant-admin lists grants scoped to the current tenant, with optional connection/table/subject filters. | Cross-tenant list denial test. |
| PUT /api/permissions/table-grants/{id} | Tenant-admin replaces the mutable authorization values and column-grant collection atomically after validation. | Precedence/versioning and invalid update tests. |
| DELETE /api/permissions/table-grants/{id} | Tenant-admin revokes the specified current-tenant grant. | Subsequent access is denied test. |

### Section 9 request and response contract

| Contract member | Required shape/meaning | Owner and verification |
|---|---|---|
| conversation_id | UUID selecting a conversation the current tenant/user may access. | 15, 16; unauthorized/unknown conversation test. |
| message | User natural-language prompt. | 15; validation and persistence test. |
| database_connection_ids | Array of selected, current-tenant connection UUIDs. | 05, 15; selected-connection authorization test. |
| knowledge_base_ids | Array of selected, current-tenant knowledge-base UUIDs. | 14, 15; selected-knowledge-base authorization test. |
| stream | Boolean selecting non-streaming POST /api/chat or streaming POST /api/chat/stream behavior. | 18; route/mode contract test. |
| message_id | UUID of the persisted response message. | 16, 18; response-to-message back-reference test. |
| answer | Grounded final answer derived only from approved execution/retrieval outputs. | 15, 17, 20; evidence-bound answer test. |
| intent | One of general, database, document, hybrid, or clarification. | 15; all-intent contract test. |
| sources_used | Array describing sources used, such as database and documents for the supplied hybrid example. | 15, 17; source-accounting test. |
| sql.query_execution_id | UUID identifying the persisted query_executions record when SQL is used. | 10, 17; trace lookup test. |
| sql.query | The validated/authorized SQL query exposed according to authorization/masking policy. | 09, 10, 20; safe-SQL disclosure test. |
| sql.row_count | Row count of the controlled execution. | 10; result-limit/row-count test. |
| citations document shape | type: document, file_name, and page; omit database-only fields. | 17; document citation serialization test. |
| citations database shape | type: database and table; omit document-only fields. | 17; database citation serialization test. |

### SSE event baseline, not a PDF wire-format requirement

The PDF requires SSE when requested but does not define event names, payloads, retry, or reconnection. Phase 18 will use this Baseline assumption: POST /api/chat/stream responds with text/event-stream and emits meta once with safe request metadata, token zero or more times with an answer delta, final once with the complete Section 9 response object, or error once with only a stable safe code and user-safe message. No replay/resume contract is claimed until explicitly added; internal exception details, credentials, raw stack traces, and unapproved results never appear in any event.

## Decision Ledger

| Decision | Selected baseline | Rationale | Source classification | Affected phases | Override impact |
|---|---|---|---|---|---|
| Requirement authority | PDF for product behavior; roadmap prompt for planning/output rules. | Prevents an implementation choice from being presented as a PDF mandate. | Planning constraint | 00–22 | An override requires reconciling every traceability row. |
| Planning-only boundary | Create only plan/ files in this pass; future Phase 01 describes, but does not perform, scaffolding. | Avoids conflict between planning and implementation. | Planning constraint | 00–02, 22 | None without an explicit implementation request. |
| API/application database | FastAPI; PostgreSQL; SQLAlchemy 2; Alembic. | Matches Section 11 recommendations and supports the required PostgreSQL schema. | Baseline assumption | 01–22 | Changing framework/ORM changes project structure, migration, testing, and documentation plans. |
| Authentication | JWT access/refresh tokens and Argon2id password hashing. | Provides a concrete tenant-context mechanism; the PDF requires authentication but not token/hash choices. | Baseline assumption | 03, 20, 21 | Replace token flows/security tests and document the migration. |
| Queue/cache | Celery with Redis. | Matches one permitted Section 11 queue option and supports file-processing workers. | Baseline assumption | 01, 11–14, 19 | Rework worker contracts and service manifests if Dramatiq/another cache is selected. |
| Runtime vector retrieval | Qdrant is the canonical retrieval index. | The Section 12 service list includes qdrant and it supports tenant-filtered retrieval. | Baseline assumption | 01, 13, 14, 20 | Rework retrieval adapter/indexing and deployment if pgvector becomes canonical. |
| Required pgvector field | Keep vector extension and document_chunks.embedding VECTOR(1024) as an audited, synchronized mirror; do not use it as the retrieval source. | Retains exact Section 7 DDL while avoiding two independent retrieval authorities. | Baseline assumption plus PDF schema requirement | 02, 13, 21 | Selecting a different canonical store requires a documented synchronization/reindex plan. |
| Embedding dimension | Configurable model/provider must validate to exactly 1024 dimensions before indexing. | The schema fixes VECTOR(1024); mismatch must fail safely rather than create divergent data. | Baseline assumption constrained by PDF | 13, 21 | A different dimension needs an intentional compatible schema migration and reindex. |
| Object storage | MinIO. | Matches Section 12 and gives a local S3-compatible implementation. | Baseline assumption | 01, 11, 12, 22 | Change storage client/configuration/deployment documentation. |
| SQL validation | SQLGlot plus per-dialect AST rules. | Meets Section 10 parser requirement and handles dialect-sensitive safety. | Baseline assumption constrained by PDF | 05, 08–10, 20, 21 | Any replacement needs equivalent AST/read-only guarantees and tests. |
| Document processing | Docling plus format-specific parsers. | Matches Section 11 and covers the five required upload families. | Baseline assumption | 11–14, 21 | Replace parser adapters, worker tests, and output metadata policy. |
| Agent orchestration | LangGraph. | Matches Section 11 and makes the Section 5 graph explicit. | Baseline assumption | 15, 21 | Retain the same state/approval boundaries if another orchestrator is selected. |
| Streaming | SSE with meta, token, final, and safe error events. | PDF mandates SSE but not a wire contract. | Baseline assumption | 18, 21, 22 | Version/document any different event framing or resume behavior. |
| Observability | Prometheus, Grafana, and OpenTelemetry. | Matches Section 11/12 recommendations. | Baseline assumption | 01, 19, 22 | Update service/configuration and monitoring acceptance tests. |
| Source adapters | PostgreSQL is the only fully implemented/tested end-to-end source baseline; SQL Server, MySQL, and Oracle adapter paths are extension points until implemented/tested. | Section 4 names all adapters but does not require claiming complete multi-dialect support immediately. | Baseline assumption | 01, 05, 06, 09, 10, 21 | Add dialect discovery, validation, limits, and integration coverage before advertising support. |
| Permission API | Tenant-admin table-grant CRUD at the baseline routes listed above, including nested column grants. | Section 4/13 require permission APIs while Section 8 leaves paths unspecified. | Baseline assumption | 04, 07, 20, 21, 22 | Route/payload changes must preserve grants, auditability, and OpenAPI documentation. |
| Permission precedence and row-filter DSL | Deny by default; require explicit column grant; direct user grants are authoritative when present, otherwise applicable role grants apply; a direct can_read false denies; allowlisted filters within the winning class are ORed and injected with AND into generated query; unknown/invalid filters fail closed. Only backend parameter values and trusted tenant_id/user_id placeholders are allowed. | The PDF stores row_filter JSONB and mandates backend injection but does not define grammar or precedence. | Baseline assumption constrained by PDF | 04, 07, 09, 20, 21 | Changes require migration/data validation, security review, and adversarial regression tests. |
| Source data previews | No persisted source-row preview by default; approved metadata samples/result previews are masked, small, retention-controlled, auditable, and never vectorized. | Reconciles Section 7 cache/audit fields with Section 17 data-residency limits. | Baseline assumption constrained by PDF | 06, 10, 19, 20, 21 | Any enablement needs explicit tenant approval and privacy/security review. |

## Individual Work and Submission Reminder

The README produced in Phase 22 must state that the work was completed independently, list any AI tools used, and acknowledge every external code sample, public documentation source, library-specific reference, and other reference material that materially informed the work. The submission must contain the required source, migration/schema, environment example, containers, API documentation/examples, tests, architecture explanation, and diagram without exposing credentials.

## Roadmap Acceptance Gate

- [ ] Exactly 23 contiguous roadmap files, numbered 00 through 22 with the prescribed filenames, exist under plan/.
- [ ] No file outside plan/ is created during this planning pass.
- [ ] Every Phase 01–22 file uses the required heading order and granular actionable checkboxes.
- [ ] Every Section 2–17 requirement has an owner and a verification artifact in this overview or its referenced manifest.
- [ ] Every Section 7 extension, field, type, nullability rule, default, key, FK delete action, constraint, and explicit index is represented in Phase 02 and a schema-contract test.
- [ ] Every Section 8 endpoint, Section 9 field, Section 5 intent, Section 10 control, Section 14 deliverable, and Section 15 acceptance criterion has a phase owner and a test/verification owner.
- [ ] Non-PDF API routes, wire formats, precedence rules, and technology choices are visibly labeled Baseline assumption.
- [ ] No phase permits durable copying of customer business data, a per-table database agent, or LLM-controlled security predicates.
