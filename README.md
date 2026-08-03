# Multi-Tenant Text-to-SQL and Document Chat Platform

This repository follows the implementation roadmap in plan/00-overview-and-roadmap.md.

## Current status

Phases 00 and 01 are implemented: repository scaffolding, safe typed
configuration, basic health probes, dependency manifests, Compose services, and
future module boundaries are present. Database schema, authentication, live
database access, document processing, SQL execution, chat, and tenant behavior
remain intentionally deferred to their owning roadmap phases.

## Runtime baseline

- Python 3.11
- FastAPI, SQLAlchemy 2, Alembic, PostgreSQL with pgvector
- Celery with Redis, Qdrant, MinIO, Docling, SQLGlot, and LangGraph
- Prometheus, Grafana, and OpenTelemetry boundaries

PostgreSQL is the planned initial customer-source adapter. SQL Server, MySQL,
and Oracle paths are extension points, not supported adapters.

## Local setup

1. Copy .env.example to .env.
2. Replace every REPLACE_* value with a locally generated secret.
3. Create a Python 3.11 virtual environment and install requirements-dev.txt.
4. Run docker compose config to validate the deployment manifest.
5. Start the foundation stack with docker compose up --build.
6. Check http://127.0.0.1:8000/api/health/live.

The Compose PostgreSQL service is the future application database, never a
customer business-data replica. Redis has Celery result persistence disabled;
Qdrant and MinIO are reserved for documents, never bulk source-query results.

## Dependency locking policy

requirements.txt contains reviewed compatible ranges. Before a release image is
treated as reproducible, generate and commit a hash-pinned lock file using
pip-compile --generate-hashes requirements.txt, then test it.

## Security baseline

- Tenant identity will be server-derived in Phase 03; no client tenant selector exists.
- Runtime secrets stay outside source control and image layers.
- Source credentials and business rows must never appear in workers, Redis,
  Qdrant, MinIO, logs, or repository fixtures.
- The future platform uses one generic database agent with permission-filtered
  schema context; per-table or per-tenant agents are prohibited.

## Disclosure

Phase 22 will record all AI tools, external code, documentation, and reference
material used, as required by the assignment.
