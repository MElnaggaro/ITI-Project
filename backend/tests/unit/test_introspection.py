"""Unit tests for PostgreSQL catalog introspector data structures."""

from services.database.introspection import DiscoveredColumn, DiscoveredSchema, DiscoveredTable, SYSTEM_SCHEMAS


def test_system_schema_filtering():
    """Verify system schemas list contains pg_catalog and information_schema."""
    assert "pg_catalog" in SYSTEM_SCHEMAS
    assert "information_schema" in SYSTEM_SCHEMAS


def test_discovered_schema_data_structures():
    """Verify DiscoveredSchema, DiscoveredTable, and DiscoveredColumn objects."""
    schema = DiscoveredSchema(schema_name="sales")
    table = DiscoveredTable(schema_name="sales", table_name="orders", table_type="table")
    col1 = DiscoveredColumn(column_name="id", data_type="uuid", ordinal_position=1, is_nullable=False, is_primary_key=True)
    col2 = DiscoveredColumn(column_name="total", data_type="numeric", ordinal_position=2, is_nullable=True)

    table.columns["id"] = col1
    table.columns["total"] = col2
    table.primary_key_columns.append("id")
    schema.tables["orders"] = table

    assert schema.schema_name == "sales"
    assert "orders" in schema.tables
    assert schema.tables["orders"].columns["id"].is_primary_key is True
    assert schema.tables["orders"].columns["total"].is_nullable is True
