"""Unit tests for SQLValidatorService AST validation, safety checks, and filter injection."""

from uuid import uuid4

import pytest
import sqlglot.expressions as exp

from schemas.resolved_schema import ResolvedColumn, ResolvedSchema, ResolvedTable
from services.sql_validator_service import SQLValidatorService


def build_test_schema(tenant_id=None, user_id=None):
    """Helper to build a valid ResolvedSchema fixture for testing."""
    t_id = tenant_id or uuid4()
    u_id = user_id or uuid4()
    conn_id = uuid4()

    col1 = ResolvedColumn(column_id=uuid4(), column_name="id", data_type="uuid", is_primary_key=True, is_foreign_key=False, can_read=True, can_filter=True, can_aggregate=True)
    col2 = ResolvedColumn(column_id=uuid4(), column_name="status", data_type="varchar", is_primary_key=False, is_foreign_key=False, can_read=True, can_filter=True, can_aggregate=True)

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


def test_sql_validator_valid_select_query():
    """Verify clean SELECT query is authorized, row-filter injected, and LIMIT clamped."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    candidate_sql = "SELECT id, status FROM orders"
    plan = validator.validate_and_rewrite(candidate_sql, schema)

    assert plan.validation_status == "valid"
    assert plan.query_type == "select"
    assert "orders" in plan.referenced_tables
    assert "status = 'active'" in plan.final_sql
    assert "LIMIT 1000" in plan.final_sql


def test_sql_validator_disallowed_dml_and_ddl():
    """Verify validator rejects INSERT, UPDATE, DELETE, DROP, ALTER, CREATE."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    disallowed_queries = [
        "DELETE FROM orders WHERE id = '123'",
        "UPDATE orders SET status = 'deleted'",
        "INSERT INTO orders (id, status) VALUES ('1', 'active')",
        "DROP TABLE orders",
        "ALTER TABLE orders ADD COLUMN extra text",
        "CREATE TABLE hack (id int)",
    ]

    for q in disallowed_queries:
        plan = validator.validate_and_rewrite(q, schema)
        assert plan.validation_status == "invalid", f"Failed to reject disallowed query: {q}"
        assert "strictly prohibited" in plan.validation_errors[0]


def test_sql_validator_unpermitted_table_rejection():
    """Verify validator rejects query referencing an unpermitted table."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    candidate_sql = "SELECT * FROM secret_passwords"
    plan = validator.validate_and_rewrite(candidate_sql, schema)

    assert plan.validation_status == "invalid"
    assert "not permitted or does not exist" in plan.validation_errors[0]


def test_sql_validator_limit_clamping():
    """Verify validator clamps high limit values to 1000."""
    schema = build_test_schema()
    validator = SQLValidatorService(dialect="postgres")

    candidate_sql = "SELECT id FROM orders LIMIT 50000"
    plan = validator.validate_and_rewrite(candidate_sql, schema)

    assert plan.validation_status == "valid"
    assert "LIMIT 1000" in plan.final_sql
