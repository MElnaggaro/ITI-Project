# 21. Automated Testing Suite (Unit + Integration)

## Goal

Assemble repeatable unit, integration, contract, and security test suites that demonstrate all required capabilities and acceptance criteria in isolated local infrastructure before packaging the assignment.

## Depends On

- [x] Phases 01 and 02 provide test configuration, migrations, fixture factories, and isolated databases.
- [x] Phases 03 through 20 provide the services, endpoints, jobs, graph paths, observability hooks, and security controls to validate.

## Assignment References

- [x] Sections 2, 8, 9, 10, 11, 12, 13, 14, and 15.

## Detailed Tasks

- [x] Establish pytest or an equivalent test runner, FastAPI test client, async test support, and deterministic dependency overrides under tests/.
- [x] Provide disposable platform PostgreSQL, read-only source PostgreSQL, Redis, Qdrant, and MinIO fixtures through Docker Compose or an equivalent isolated test environment.
- [x] Add migration tests that create a clean platform schema and verify the complete Section 7 DDL fidelity manifest.
- [x] Add unit tests for password/token security, tenant context, encryption/redaction, permission combination, column masking, row-filter DSL compilation, and repository tenant scoping.
- [x] Add unit tests for adapters, schema normalization, metadata sample bounds, SQL generation prompts, SQLGlot validation, AST filter injection, limit handling, result masking, citation serialization, and SSE event serialization.
- [x] Add API contract tests for every Section 8 method/path and the Section 9 request/response fields, including source-specific citation shapes.
- [x] Add integration tests for login/refresh/me, connection CRUD/test, schema discovery, schema sync, filtered-schema database chat, file upload/reprocess, knowledge-base attachment, document chat, hybrid chat, conversations, citations, SQL lookup, and streaming chat.
- [x] Mock LLM/embedding providers in most tests; maintain a small clearly separated optional provider smoke-test layer that never requires production credentials in CI.
- [x] Add Celery worker integration tests for upload processing, Qdrant/postgres embedding synchronization, retry/idempotency, delete/reprocess cleanup, and tenant context propagation.
- [x] Add failure-mode tests for malformed files, unavailable storage/vector/source databases, parser errors, timeout, invalid SQL, invalid filters, cancelled streams, and safe user-facing errors.
- [x] Add performance-safety tests for row/result limits, query timeout, bounded history, chunking bounds, and no unbounded result persistence.
- [x] Add the Phase 20 security regression suite and map every test to its Section 10 control or Section 15 acceptance criterion.
- [x] Configure a CI command sequence for lint/type checks if adopted, unit tests, integration tests, security tests, migration verification, and OpenAPI generation/contract checks.
- [x] Produce test fixtures and factory data that contain synthetic business records only; never commit real credentials or customer data.

## Data Model Touched

- [x] All Section 7 tables are covered by migrations, factories, repository tests, or integration fixtures as applicable.

## API Endpoints Touched

- [x] All Section 8 endpoints.
- [x] Baseline non-Section-8 health and permission-management interfaces are tested separately and labeled as assumptions.

## Security & Permission Notes

- [x] Test data must model multi-tenant isolation, sensitive columns, row filters, read-only source credentials, and hostile SQL inputs.
- [x] CI logs and test artifacts must redact secrets and synthetic sensitive values consistently.

## Testing Requirements

- [x] Run unit, integration, contract, and security suites independently and together from a clean environment.
- [x] Verify tests prove the required Section 14 deliverable coverage rather than only code-path coverage.

## Definition of Done

- [x] The automated suite covers every required capability, API, SQL control, and acceptance criterion.
- [x] Tests can run from documented local infrastructure with no real customer data or secrets.
- [x] Failures identify the subsystem/control without disclosing protected data.

## Suggested Day (1–4)

Day 4
