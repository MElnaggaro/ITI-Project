"""Section 4 layout and root-artifact coverage tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_required_phase01_paths_exist() -> None:
    expected_paths = {
        "app/main.py",
        "app/config.py",
        "app/dependencies.py",
        "app/exceptions.py",
        "app/logging_config.py",
        "api/router.py",
        "api/routes/auth.py",
        "api/routes/tenants.py",
        "api/routes/users.py",
        "api/routes/database_connections.py",
        "api/routes/database_schema.py",
        "api/routes/files.py",
        "api/routes/knowledge_bases.py",
        "api/routes/conversations.py",
        "api/routes/chat.py",
        "api/routes/permissions.py",
        "api/routes/health.py",
        "core/security.py",
        "core/encryption.py",
        "core/permissions.py",
        "core/constants.py",
        "core/tenant_context.py",
        "services/database/connection_service.py",
        "services/database/connection_tester.py",
        "services/database/schema_discovery.py",
        "services/database/metadata_cache.py",
        "services/database/query_executor.py",
        "services/database/query_validator.py",
        "services/database/dialect_resolver.py",
        "services/database/adapters/base.py",
        "services/database/adapters/postgresql.py",
        "services/database/adapters/sqlserver.py",
        "services/database/adapters/mysql.py",
        "services/database/adapters/oracle.py",
        "services/documents/upload_service.py",
        "services/documents/document_processor.py",
        "services/documents/chunking_service.py",
        "services/documents/embedding_service.py",
        "services/documents/retrieval_service.py",
        "agents/graph.py",
        "agents/state.py",
        "workers/celery_app.py",
        "migrations/env.py",
        ".env.example",
        "alembic.ini",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "README.md",
    }

    missing = sorted(path for path in expected_paths if not ((ROOT / path).exists() or (ROOT.parent / path).exists()))
    assert not missing, f"Missing required Phase 01 paths: {missing}"

