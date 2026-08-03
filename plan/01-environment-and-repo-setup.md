# 01. Environment & Repository Setup

## Goal

Prepare the future implementation repository so the required FastAPI platform, background processing, PostgreSQL application database, Qdrant retrieval service, MinIO object storage, Redis, and observability services have clear boundaries from day one. This phase plans and later creates only the project skeleton, dependency/configuration contracts, and local deployment layout; it does not implement business behavior or create an alternative to the Section 7 schema.

## Depends On

- 00 — use the authority order, selected baselines, fixed phase filenames, source-data-residency rules, and decision ledger.
- No implementation phase is required before this phase. The current workspace contains planning inputs only; retain that fact in the implementation handoff and do not overwrite an existing project tree without approval.

## Assignment References

- Section 3 — FastAPI gateway, LangGraph architecture, storage boundaries, and live customer-database boundary.
- Section 4 — recommended project tree and named modules.
- Section 11 — recommended technology stack.
- Section 12 — api, worker, postgres, redis, qdrant, minio, prometheus, and grafana services.
- Section 13 Day 1 — project setup checkpoint.
- Section 14 — required environment, container, README, OpenAPI, and modular-delivery artifacts.
- Sections 15–17 — reliable setup, independent-work disclosure, and data-residency principle.

## Detailed Tasks

- [x] Create the root application layout only when implementation begins: app/, api/, core/, models/, schemas/, repositories/, services/, agents/, storage/, vector_store/, workers/, migrations/, tests/, and scripts/.
- [x] Create app/main.py as the future FastAPI application entry point and keep app/main.py free of tenant/business implementation logic.
- [x] Create app/config.py as the typed configuration boundary for application, PostgreSQL, Redis, Celery, Qdrant, MinIO, encryption, JWT, LLM, embedding, parser, SQL-safety, and observability settings.
- [x] Create app/dependencies.py for future request dependencies, including authentication/tenant context and shared service providers.
- [x] Create app/exceptions.py for stable application error types and safe HTTP error translation.
- [x] Create app/logging_config.py for structured, redacted application logging and request correlation.
- [x] Create api/router.py as the future composition point for versioned route modules and OpenAPI tags.
- [x] Create api/routes/auth.py for the Section 8 authentication routes.
- [x] Create api/routes/tenants.py and api/routes/users.py for tenant/user administration surfaces required by the recommended structure; document any routes beyond Section 8 as baseline extensions.
- [x] Create api/routes/database_connections.py for the exact Section 8 database-connection routes.
- [x] Create api/routes/database_schema.py for the exact schema/table inspection routes.
- [x] Create api/routes/files.py for the exact file upload, list, get, delete, and reprocess routes.
- [x] Create api/routes/knowledge_bases.py for the exact knowledge-base routes.
- [x] Create api/routes/conversations.py for the exact conversation routes.
- [x] Create api/routes/chat.py for POST /api/chat and POST /api/chat/stream only; keep SSE framing work in Phase 18.
- [x] Create api/routes/permissions.py for the documented Baseline-assumption permission-grant routes; do not represent them as Section 8 routes.
- [x] Create api/routes/health.py for deployment health/readiness probes as a documented operational extension.
- [x] Create core/security.py for future JWT and Argon2id helpers, core/encryption.py for connection-secret encryption, core/permissions.py for authorization primitives, core/constants.py for shared safe limits/statuses, and core/tenant_context.py for trusted tenant resolution.
- [x] Create model modules tenant.py, user.py, role.py, database_connection.py, database_schema.py, table_permission.py, file.py, document_chunk.py, knowledge_base.py, conversation.py, message.py, query_execution.py, citation.py, and audit_log.py; include modules for user_roles, database_tables, database_columns, and column_permissions if they are represented separately rather than grouped into the supplied modules.
- [x] Create schemas/ for request/response DTOs, validation models, and OpenAPI shapes; preserve the Section 9 member names without deciding unspecified nullability prematurely.
- [x] Create repositories/ for tenant-scoped application-database access; require every repository interface to accept or derive trusted tenant context before resource-ID lookup.
- [x] Create services/database/connection_service.py, connection_tester.py, schema_discovery.py, metadata_cache.py, query_executor.py, query_validator.py, and dialect_resolver.py with contracts allocated to Phases 05–10.
- [x] Create services/database/adapters/base.py as a capability-oriented source-dialect interface with safe unsupported-operation errors.
- [x] Create services/database/adapters/postgresql.py as the fully implemented/tested source-adapter baseline.
- [x] Create services/database/adapters/sqlserver.py, mysql.py, and oracle.py as explicit extension-path modules only; do not advertise a dialect as supported until its discovery, AST validation, execution limits, and integration tests exist.
- [x] Create services/documents/upload_service.py, document_processor.py, chunking_service.py, embedding_service.py, retrieval_service.py, and services/documents/parsers/ for Phases 11–14.
- [x] Create services/chat/ for orchestration-facing use cases and services/llm/ for provider/client abstractions that cannot bypass permission or SQL-validation layers.
- [x] Create agents/graph.py, agents/state.py, agents/nodes/, and agents/prompts/ for the single reusable LangGraph database agent and document/hybrid nodes; prohibit a per-table, per-tenant, or permanent per-database agent layout.
- [x] Create storage/ for a tenant-qualified MinIO/S3-compatible abstraction and vector_store/ for a tenant-filtered Qdrant abstraction; keep raw source-database results out of both.
- [x] Create workers/ for Celery task definitions and worker-safe service composition; require job payloads to carry resource identifiers plus trusted tenant context, never credentials or copied business rows.
- [x] Create migrations/ for Alembic revisions and reserve the initial reference-schema migration for Phase 02.
- [x] Create tests/ with unit/, integration/, security/, and shared fixture/factory boundaries; preserve separate source-database, vector, object-storage, and application-database fixtures.
- [x] Create scripts/ only for safe developer/operational helpers; prohibit scripts that print or commit real credentials.
- [x] Create .env.example with placeholders only for application settings, PostgreSQL, Redis, Qdrant, MinIO, encryption/JWT keys, LLM/embedding provider configuration, SQL limits, parser limits, and observability endpoints.
- [x] Ensure .env.example contains no usable password, connection string, API key, encryption key, private key, tenant data, or source-database value.
- [x] Create alembic.ini and the Alembic environment configuration boundary; make it point to the Phase 02 model metadata without generating a migration in this phase.
- [x] Create requirements.txt (or a documented equivalent dependency manifest) with FastAPI, SQLAlchemy 2, Alembic, PostgreSQL driver, Celery, Redis client, Qdrant client, MinIO/S3 client, SQLGlot, Docling and format parsers, LangGraph, JWT/Argon2id libraries, Prometheus/OpenTelemetry libraries, and test tooling.
- [x] Record exact pinned-version policy and compatible Python/runtime version in the dependency/README plan; never pin secrets or provider account identifiers.
- [x] Create Dockerfile for the future API/worker image with non-root execution, reproducible dependency installation, and no secret material embedded in image layers.
- [x] Create docker-compose.yml with exactly the required service names api, worker, postgres, redis, qdrant, minio, prometheus, and grafana.
- [x] Configure the compose postgres service as the application database, not a customer business-data replica; expose only development-safe local ports and named persistent volumes as appropriate.
- [x] Configure redis only as cache/broker infrastructure, celert worker dependency, and optional rate/ephemeral state service; do not use it for durable source query results.
- [x] Configure qdrant only for document-chunk embeddings and tenant-filtered retrieval; document PostgreSQL document_chunks.embedding as the required synchronized schema/audit mirror rather than a second retrieval authority.
- [x] Configure minio only for original uploaded files and processed artifacts under tenant-qualified object keys.
- [x] Configure api and worker to receive configuration through environment variables/secrets at runtime and to depend on health/readiness conditions rather than hard-coded host assumptions.
- [x] Configure prometheus to scrape safe application/worker metrics and grafana to load only non-secret dashboard configuration.
- [x] Define local network boundaries so customer source databases are reached only from the controlled connection/executor layer, never directly by clients, Qdrant, MinIO, or arbitrary worker code.
- [x] Define health/readiness/liveness checks for api, worker, postgres, redis, qdrant, minio, prometheus, and grafana; health output must not reveal connection strings or stack traces.
- [x] Establish a configuration key convention for immutable safe defaults: source execution timeout, row limit, result-size limit, metadata sample cap, preview cap, retention duration, upload size, parser timeout, and allowed source-dialect flags.
- [x] Establish correlation/request IDs propagated through API, Celery jobs, audit logs, metrics, and traces without including user prompts, source rows, passwords, or unmasked sensitive values by default.
- [x] Set the implementation baseline to PostgreSQL as the only end-to-end source database supported on Day 1–4; preserve SQL Server, MySQL, and Oracle adapter paths as future extension points with explicit unsupported status until tested.
- [x] Set the implementation baseline to FastAPI, PostgreSQL with SQLAlchemy 2/Alembic, Celery with Redis, Qdrant, MinIO, SQLGlot, Docling, LangGraph, SSE, Prometheus, Grafana, and OpenTelemetry; label each as a baseline choice rather than an extra PDF requirement.
- [x] Create README.md with future setup, migration, run, test, API, architecture, service, source-data-residency, and individual-work disclosure sections; complete its substantive content in Phase 22.
- [x] Record that implementation setup must retain the exact Phase 00–22 roadmap and cannot replace the plan with source scaffolding during planning-only work.

## Data Model Touched

- No application tables are created in this phase; Phase 02 owns the complete Section 7 PostgreSQL migration and SQLAlchemy table mappings.
- This phase defines configuration and deployment boundaries for the later application database, Qdrant document index, MinIO objects, Redis broker/cache, and live source databases.
- Preserve the data-residency split: the application database will hold platform metadata; Qdrant will hold only document-chunk embeddings; MinIO will hold uploaded files/artifacts; live source databases retain business records.

## API Endpoints Touched

- No Section 8 endpoint behavior is implemented in this phase.
- Future route-module registration is planned for the exact Section 8 endpoints, while health, tenant/user, and permission administration surfaces are documented operational or baseline extensions until their owning phases specify them.

## Security & Permission Notes

- Resolve tenant identity only after authentication in Phase 03; do not place client-controlled tenant IDs in global configuration, cache namespaces, object-key prefixes, or worker trust decisions.
- Keep all local secrets outside version control and outside Docker image layers; .env.example uses non-functional placeholders only.
- Make logs, metrics, traces, health responses, compose diagnostics, and failed startup messages redact passwords, encrypted connection strings, JWTs, API keys, source rows, and internal stack traces.
- Isolate application PostgreSQL credentials from read-only customer-source credentials; the latter are later decrypted only inside authorized connection/execution flows.
- Treat Qdrant, MinIO, Redis, and Celery payloads as tenant-scoped data stores/transport paths subject to the same authorization and retention controls as repository access.
- Do not provide a generic tool/service path that lets an LLM invoke a database driver, mutate a row filter, query a source database, or access object/vector storage directly.

## Testing Requirements

- [x] Add a repository-layout test or review checklist that asserts every Section 4 path/module and every required root artifact has a home or a documented equivalent.
- [x] Add a compose-configuration validation that checks service names api, worker, postgres, redis, qdrant, minio, prometheus, and grafana and verifies configuration contains no literal production secrets.
- [x] Add startup/readiness tests that prove degraded dependencies yield safe statuses without connection strings, tokens, source records, or stack traces.
- [x] Add configuration validation tests for missing required settings, invalid numeric limits, disallowed source-dialect flags, unsafe embedding dimension, and accidental blank encryption/JWT secrets outside an explicitly local test mode.
- [x] Add container/image checks for non-root execution, reproducible dependency installation, and absence of copied .env/private-key material.
- [x] Add worker-payload tests proving tenant context/resource IDs are carried while passwords and business rows are rejected.
- [x] Add data-boundary tests showing Redis, Qdrant, MinIO, and application PostgreSQL are not configured as destinations for bulk source-database query results.

## Definition of Done

- [x] The future source tree contains every Section 4 path/module or a documented equivalent, with no per-table-agent structure.
- [x] The dependency and configuration manifests record all selected baseline technologies and override points.
- [x] docker-compose.yml defines the eight required service names with safe service boundaries and health checks.
- [x] .env.example, Dockerfile, compose configuration, logging configuration, and README skeleton contain no real secret or customer business data.
- [x] Alembic, testing, observability, object-storage, vector-store, worker, and source-adapter boundaries are ready for their owning phases.
- [x] The project setup documentation makes clear that PostgreSQL is the tested source-adapter baseline and other named adapters are not advertised as supported until completed.

## Suggested Day (1–4)

Day 1.
