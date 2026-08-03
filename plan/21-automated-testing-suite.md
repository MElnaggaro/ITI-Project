# 21. Automated Testing Suite (Unit + Integration)

## Goal

Assemble repeatable unit, integration, contract, and security test suites that demonstrate all required capabilities and acceptance criteria in isolated local infrastructure before packaging the assignment.

## Depends On

- [ ] Phases 01 and 02 provide test configuration, migrations, fixture factories, and isolated databases.
- [ ] Phases 03 through 20 provide the services, endpoints, jobs, graph paths, observability hooks, and security controls to validate.

## Assignment References

- [ ] Sections 2, 8, 9, 10, 11, 12, 13, 14, and 15.

## Detailed Tasks

- [ ] Establish pytest or an equivalent test runner, FastAPI test client, async test support, and deterministic dependency overrides under tests/.
- [ ] Provide disposable platform PostgreSQL, read-only source PostgreSQL, Redis, Qdrant, and MinIO fixtures through Docker Compose or an equivalent isolated test environment.
- [ ] Add migration tests that create a clean platform schema and verify the complete Section 7 DDL fidelity manifest.
- [ ] Add unit tests for password/token security, tenant context, encryption/redaction, permission combination, column masking, row-filter DSL compilation, and repository tenant scoping.
- [ ] Add unit tests for adapters, schema normalization, metadata sample bounds, SQL generation prompts, SQLGlot validation, AST filter injection, limit handling, result masking, citation serialization, and SSE event serialization.
- [ ] Add API contract tests for every Section 8 method/path and the Section 9 request/response fields, including source-specific citation shapes.
- [ ] Add integration tests for login/refresh/me, connection CRUD/test, schema discovery, schema sync, filtered-schema database chat, file upload/reprocess, knowledge-base attachment, document chat, hybrid chat, conversations, citations, SQL lookup, and streaming chat.
- [ ] Mock LLM/embedding providers in most tests; maintain a small clearly separated optional provider smoke-test layer that never requires production credentials in CI.
- [ ] Add Celery worker integration tests for upload processing, Qdrant/postgres embedding synchronization, retry/idempotency, delete/reprocess cleanup, and tenant context propagation.
- [ ] Add failure-mode tests for malformed files, unavailable storage/vector/source databases, parser errors, timeout, invalid SQL, invalid filters, cancelled streams, and safe user-facing errors.
- [ ] Add performance-safety tests for row/result limits, query timeout, bounded history, chunking bounds, and no unbounded result persistence.
- [ ] Add the Phase 20 security regression suite and map every test to its Section 10 control or Section 15 acceptance criterion.
- [ ] Configure a CI command sequence for lint/type checks if adopted, unit tests, integration tests, security tests, migration verification, and OpenAPI generation/contract checks.
- [ ] Produce test fixtures and factory data that contain synthetic business records only; never commit real credentials or customer data.

## Data Model Touched

- [ ] All Section 7 tables are covered by migrations, factories, repository tests, or integration fixtures as applicable.

## API Endpoints Touched

- [ ] All Section 8 endpoints.
- [ ] Baseline non-Section-8 health and permission-management interfaces are tested separately and labeled as assumptions.

## Security & Permission Notes

- [ ] Test data must model multi-tenant isolation, sensitive columns, row filters, read-only source credentials, and hostile SQL inputs.
- [ ] CI logs and test artifacts must redact secrets and synthetic sensitive values consistently.

## Testing Requirements

- [ ] Run unit, integration, contract, and security suites independently and together from a clean environment.
- [ ] Verify tests prove the required Section 14 deliverable coverage rather than only code-path coverage.

## Definition of Done

- [ ] The automated suite covers every required capability, API, SQL control, and acceptance criterion.
- [ ] Tests can run from documented local infrastructure with no real customer data or secrets.
- [ ] Failures identify the subsystem/control without disclosing protected data.

## Suggested Day (1–4)

Day 4
