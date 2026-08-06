"""Unit tests for SQLValidatorService AST validation, safety checks, and filter injection."""

from uuid import UUID, uuid4

import sqlglot.expressions as exp

from schemas.resolved_schema import ResolvedColumn, ResolvedSchema, ResolvedTable
from services.sql_validator_service import SQLValidatorService


def build_test_schema(tenant_id: UUID | None = None, user_id: UUID | None = None) -> ResolvedSchema:
    """Helper to build a valid ResolvedSchema fixture for testing."""
    t_id = tenant_id or uuid4()
    u_id = user_id or uuid4()
    conn_id = uuid4()

    col1 = ResolvedColumn(
        column_id=uuid4(), column_name="id", data_type="uuid", is_primary_key=True,
        is_foreign_key=False, can_read=True, can_filter=True, can_aggregate=True
    )
    col2 = ResolvedColumn(
        column_id=uuid4(), column_name="status", data_type="varchar", is_primary_key=False,
        is_foreign_key=False, can_read=True, can_filter=True, can_aggregate=True
    )

    filter_ast = exp.EQ(
        this=exp.Column(this=exp.Identifier(this="status")),
        expression=exp.Literal.string("active"),
    )

    tbl = ResolvedTable(
        table_id=uuid4(),
        schema_name="public",
        table_name="orders",
        table_type="table",
        description="Orders table",
        can_read=True,
        can_insert=False,
        can_update=False,
        can_delete=False,
        columns={"id": col1, "status": col2},
        compiled_row_filters=[filter_ast],
        raw_row_filters=[{"status": {"eq": "active"}}],
    )

    return ResolvedSchema(
        tenant_id=t_id,
        user_id=u_id,
        connection_id=conn_id,
        database_type="postgres",
        tables={"orders": tbl},
    )


def test_sql_validator_valid_select_query() -> None:
    """Verify clean SELECT query is authorized, row-filter injected, and LIMIT clamped."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    candidate_sql = "SELECT id, status FROM orders"
    plan = validator.validate_and_rewrite(candidate_sql, schema)

    assert plan.validation_status == "valid"
    assert plan.query_type == "select"
    assert "orders" in plan.referenced_tables
    assert plan.final_sql is not None
    assert "status = 'active'" in plan.final_sql
    assert "LIMIT 1000" in plan.final_sql


def test_sql_validator_disallowed_dml_and_ddl() -> None:
    """Verify validator rejects INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, GRANT, REVOKE, EXEC, CALL, COPY, ATTACH, DETACH, TRUNCATE."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    disallowed_queries = [
        "DELETE FROM orders WHERE id = '123'",
        "UPDATE orders SET status = 'deleted'",
        "INSERT INTO orders (id, status) VALUES ('1', 'active')",
        "DROP TABLE orders",
        "ALTER TABLE orders ADD COLUMN extra text",
        "CREATE TABLE hack (id int)",
        "GRANT ALL PRIVILEGES ON orders TO public",
        "REVOKE SELECT ON orders FROM public",
        "EXEC sp_executesql N'SELECT 1'",
        "CALL my_procedure()",
        "COPY orders FROM '/tmp/data.csv'",
        "ATTACH DATABASE 'db.sqlite' AS aux",
        "DETACH DATABASE aux",
        "TRUNCATE TABLE orders",
    ]

    for q in disallowed_queries:
        plan = validator.validate_and_rewrite(q, schema)
        assert plan.validation_status == "invalid", f"Failed to reject disallowed query: {q}"
        assert len(plan.validation_errors) > 0


def test_sql_validator_allowed_queries() -> None:
    """Verify validator permits SELECT, WITH, and EXPLAIN read-only queries."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    explain_query = "EXPLAIN SELECT id FROM orders"
    plan_explain = validator.validate_and_rewrite(explain_query, schema)
    assert plan_explain.validation_status == "valid"
    assert plan_explain.query_type == "explain"

    with_query = "WITH sub AS (SELECT id FROM orders) SELECT id FROM sub"
    plan_with = validator.validate_and_rewrite(with_query, schema)
    assert plan_with.validation_status == "valid"
    assert plan_with.query_type in ("with", "select")


def test_sql_validator_blocks_system_schemas_and_admin_functions() -> None:
    """Verify validator blocks access to system schemas and administrative functions."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    sys_queries = [
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM pg_catalog.pg_user",
        "SELECT * FROM sys.tables",
        "SELECT pg_read_file('/etc/passwd') FROM orders",
        "SELECT version() FROM orders",
        "SELECT pg_sleep(5) FROM orders",
    ]

    for q in sys_queries:
        plan = validator.validate_and_rewrite(q, schema)
        assert plan.validation_status == "invalid", f"Failed to block system access/admin func: {q}"
        assert len(plan.validation_errors) > 0
        assert ("strictly prohibited" in plan.validation_errors[0] or "not permitted" in plan.validation_errors[0])


def test_sql_validator_unpermitted_table_rejection() -> None:
    """Verify validator rejects query referencing an unpermitted table."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    candidate_sql = "SELECT * FROM secret_passwords"
    plan = validator.validate_and_rewrite(candidate_sql, schema)

    assert plan.validation_status == "invalid"
    assert "not permitted or does not exist" in plan.validation_errors[0]


def test_sql_validator_limit_clamping() -> None:
    """Verify validator clamps high limit values to 1000."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    candidate_sql = "SELECT id FROM orders LIMIT 50000"
    plan = validator.validate_and_rewrite(candidate_sql, schema)

    assert plan.validation_status == "valid"
    assert plan.final_sql is not None
    assert "LIMIT 1000" in plan.final_sql

