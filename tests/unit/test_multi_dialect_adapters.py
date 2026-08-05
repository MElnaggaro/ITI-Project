"""Unit tests for multi-dialect database source adapters and introspectors."""

import pytest
from services.database.adapter import (
    PostgreSQLAdapter,
    MySQLAdapter,
    SQLServerAdapter,
    OracleAdapter,
    get_source_adapter,
    validate_host_ssrf,
)
from services.database.introspection import (
    PostgreSQLIntrospector,
    MySQLIntrospector,
    SQLServerIntrospector,
    OracleIntrospector,
    get_introspector,
)


def test_ssrf_host_validation():
    """Verify SSRF host validation blocks restricted hostnames and loopback IPs."""
    with pytest.raises(ValueError, match="SSRF security policy"):
        validate_host_ssrf("localhost")

    with pytest.raises(ValueError, match="SSRF security policy"):
        validate_host_ssrf("metadata.google.internal")


def test_get_source_adapter_factory():
    """Verify get_source_adapter returns appropriate dialect adapter instance."""
    pg = get_source_adapter("postgresql", "10.0.0.1", 5432, "db", "user", "pass")
    assert isinstance(pg, PostgreSQLAdapter)
    assert "postgresql+psycopg" in pg.build_connection_string()

    mysql = get_source_adapter("mysql", "10.0.0.1", 3306, "db", "user", "pass")
    assert isinstance(mysql, MySQLAdapter)
    assert "mysql+pymysql" in mysql.build_connection_string()

    mssql = get_source_adapter("sqlserver", "10.0.0.1", 1433, "db", "user", "pass")
    assert isinstance(mssql, SQLServerAdapter)
    assert "mssql+pymssql" in mssql.build_connection_string()

    oracle = get_source_adapter("oracle", "10.0.0.1", 1521, "db", "user", "pass")
    assert isinstance(oracle, OracleAdapter)
    assert "oracle+oracledb" in oracle.build_connection_string()


def test_get_introspector_factory():
    """Verify get_introspector returns appropriate introspector for dialect."""
    pg_intro = get_introspector("postgresql", "sqlite:///:memory:")
    assert isinstance(pg_intro, PostgreSQLIntrospector)

    mysql_intro = get_introspector("mysql", "sqlite:///:memory:")
    assert isinstance(mysql_intro, MySQLIntrospector)

    mssql_intro = get_introspector("sqlserver", "sqlite:///:memory:")
    assert isinstance(mssql_intro, SQLServerIntrospector)

    oracle_intro = get_introspector("oracle", "sqlite:///:memory:")
    assert isinstance(oracle_intro, OracleIntrospector)
