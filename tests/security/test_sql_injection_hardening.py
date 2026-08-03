"""Security regression tests verifying SQLGlot validator rejects DDL, DML, multi-statements, and injection attacks."""

from uuid import uuid4

from schemas.resolved_schema import ResolvedColumn, ResolvedSchema, ResolvedTable
from services.sql_validator_service import SQLValidatorService


def _get_test_schema() -> ResolvedSchema:
    schema = ResolvedSchema(tenant_id=uuid4(), user_id=uuid4(), connection_id=uuid4(), database_type="postgresql")
    tbl = ResolvedTable(
        table_id=uuid4(),
        schema_name="public",
        table_name="orders",
        table_type="BASE TABLE",
        description=None,
        can_read=True,
        can_insert=False,
        can_update=False,
        can_delete=False,
    )
    tbl.columns["id"] = ResolvedColumn(
        column_id=uuid4(),
        column_name="id",
        data_type="uuid",
        is_primary_key=True,
        is_foreign_key=False,
        can_read=True,
        can_filter=True,
        can_aggregate=True,
    )
    tbl.columns["total_amount"] = ResolvedColumn(
        column_id=uuid4(),
        column_name="total_amount",
        data_type="numeric",
        is_primary_key=False,
        is_foreign_key=False,
        can_read=True,
        can_filter=True,
        can_aggregate=True,
    )
    schema.tables["orders"] = tbl
    return schema


def test_sql_validator_rejects_destructive_dml():
    """Verify SQLValidatorService rejects INSERT, UPDATE, and DELETE queries."""
    validator = SQLValidatorService()
    schema = _get_test_schema()

    # 1. INSERT
    res_insert = validator.validate_and_rewrite("INSERT INTO orders (id) VALUES ('123')", schema)
    assert res_insert.validation_status == "invalid"

    # 2. UPDATE
    res_update = validator.validate_and_rewrite("UPDATE orders SET total_amount = 0", schema)
    assert res_update.validation_status == "invalid"

    # 3. DELETE
    res_delete = validator.validate_and_rewrite("DELETE FROM orders", schema)
    assert res_delete.validation_status == "invalid"


def test_sql_validator_rejects_ddl_and_stacked_queries():
    """Verify SQLValidatorService rejects DDL and stacked/multi-statement queries."""
    validator = SQLValidatorService()
    schema = _get_test_schema()

    # 1. DROP TABLE
    res_drop = validator.validate_and_rewrite("DROP TABLE orders;", schema)
    assert res_drop.validation_status == "invalid"

    # 2. CREATE TABLE
    res_create = validator.validate_and_rewrite("CREATE TABLE hack (id int);", schema)
    assert res_create.validation_status == "invalid"

    # 3. Stacked SQL query
    res_stacked = validator.validate_and_rewrite("SELECT * FROM orders; DROP TABLE orders;", schema)
    assert res_stacked.validation_status == "invalid"
