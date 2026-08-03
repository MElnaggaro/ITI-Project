"""Unit tests for source adapters and SSRF host policy validation."""

import pytest

from services.database.adapter import PostgreSQLAdapter, ExtensionSourceAdapter, validate_host_ssrf


def test_ssrf_host_validation():
    """Verify host validation rejects localhost, loopback, link-local, and metadata endpoints."""
    # Valid external hostnames
    validate_host_ssrf("db.example.com")
    validate_host_ssrf("192.0.2.1")  # Documentation TEST-NET-1 IP

    # Disallowed hostnames
    with pytest.raises(ValueError, match="disallowed due to SSRF"):
        validate_host_ssrf("localhost")

    with pytest.raises(ValueError, match="disallowed due to SSRF"):
        validate_host_ssrf("metadata.google.internal")

    # Disallowed IP ranges
    with pytest.raises(ValueError, match="disallowed due to network isolation policy"):
        validate_host_ssrf("127.0.0.1")

    with pytest.raises(ValueError, match="disallowed due to network isolation policy"):
        validate_host_ssrf("169.254.169.254")


def test_postgresql_adapter_build_connection_string():
    """Verify connection string construction for PostgreSQL adapter."""
    adapter = PostgreSQLAdapter(
        host="db.example.com",
        port=5432,
        database_name="prod_db",
        username="db_user",
        password="secret_password",
        ssl_enabled=True,
    )

    conn_str = adapter.build_connection_string()
    assert "postgresql+psycopg://db_user:secret_password@db.example.com:5432/prod_db?sslmode=require" in conn_str


def test_unsupported_extension_adapter():
    """Verify extension adapters return safe unsupported test status."""
    adapter = ExtensionSourceAdapter(dialect="oracle")
    success, msg = adapter.test_connection()
    assert success is False
    assert "unsupported extension adapter" in msg
