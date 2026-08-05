"""PostgreSQL source catalog introspection service."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import create_engine, text

SYSTEM_SCHEMAS = frozenset(
    {"pg_catalog", "information_schema", "pg_toast", "pg_temp_1", "pg_toast_temp_1"}
)


@dataclass(slots=True)
class DiscoveredColumn:
    """Column structural metadata."""

    column_name: str
    data_type: str
    ordinal_position: int
    is_nullable: bool
    is_primary_key: bool = False
    is_foreign_key: bool = False
    referenced_schema: str | None = None
    referenced_table: str | None = None
    referenced_column: str | None = None
    description: str | None = None


@dataclass(slots=True)
class DiscoveredTable:
    """Table/view structural metadata."""

    schema_name: str
    table_name: str
    table_type: str  # 'table' or 'view'
    description: str | None = None
    estimated_row_count: int | None = None
    primary_key_columns: list[str] = field(default_factory=list)
    columns: dict[str, DiscoveredColumn] = field(default_factory=dict)


@dataclass(slots=True)
class DiscoveredSchema:
    """Schema structural metadata."""

    schema_name: str
    description: str | None = None
    tables: dict[str, DiscoveredTable] = field(default_factory=dict)


class PostgreSQLIntrospector:
    """Introspects PostgreSQL live catalog using read-only connection."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def introspect(self) -> dict[str, DiscoveredSchema]:
        """Query PostgreSQL catalogs and return discovered structural metadata."""
        engine = create_engine(self.connection_string, pool_pre_ping=True)
        schemas: dict[str, DiscoveredSchema] = {}

        with engine.connect() as conn:
            # 1. Discover non-system schemas
            schema_stmt = text(
                """
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
                AND schema_name NOT LIKE 'pg_temp%'
                ORDER BY schema_name;
                """
            )
            for row in conn.execute(schema_stmt):
                s_name = row.schema_name
                schemas[s_name] = DiscoveredSchema(schema_name=s_name)

            if not schemas:
                schemas["public"] = DiscoveredSchema(schema_name="public")

            # 2. Discover tables & views across discovered schemas with estimated row count from pg_class
            table_stmt = text(
                """
                SELECT
                    t.table_schema,
                    t.table_name,
                    t.table_type,
                    COALESCE(c.reltuples::bigint, 0) AS estimated_row_count
                FROM information_schema.tables t
                LEFT JOIN pg_namespace n ON n.nspname = t.table_schema
                LEFT JOIN pg_class c ON c.relname = t.table_name AND c.relnamespace = n.oid
                WHERE t.table_schema = ANY(:schemas)
                ORDER BY t.table_schema, t.table_name;
                """
            )
            for row in conn.execute(table_stmt, {"schemas": list(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                t_type = "view" if "VIEW" in str(row.table_type).upper() else "table"
                row_cnt = max(0, int(row.estimated_row_count or 0))

                dt = DiscoveredTable(
                    schema_name=s_name,
                    table_name=t_name,
                    table_type=t_type,
                    estimated_row_count=row_cnt,
                )
                schemas[s_name].tables[t_name] = dt

            # 3. Discover columns across tables
            col_stmt = text(
                """
                SELECT table_schema, table_name, column_name, data_type, ordinal_position, is_nullable
                FROM information_schema.columns
                WHERE table_schema = ANY(:schemas)
                ORDER BY table_schema, table_name, ordinal_position;
                """
            )
            for row in conn.execute(col_stmt, {"schemas": list(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                c_name = row.column_name

                if s_name in schemas and t_name in schemas[s_name].tables:
                    col = DiscoveredColumn(
                        column_name=c_name,
                        data_type=row.data_type,
                        ordinal_position=row.ordinal_position,
                        is_nullable=(str(row.is_nullable).upper() == "YES"),
                    )
                    schemas[s_name].tables[t_name].columns[c_name] = col

            # 4. Discover Primary Keys & Foreign Keys
            pk_fk_stmt = text(
                """
                SELECT
                    tc.table_schema,
                    tc.table_name,
                    kcu.column_name,
                    tc.constraint_type,
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                    AND tc.table_schema = kcu.table_schema
                LEFT JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                    AND ccu.table_schema = tc.table_schema
                WHERE tc.table_schema = ANY(:schemas)
                AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY');
                """
            )
            for row in conn.execute(pk_fk_stmt, {"schemas": list(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                c_name = row.column_name
                c_type = row.constraint_type

                if s_name in schemas and t_name in schemas[s_name].tables:
                    tbl = schemas[s_name].tables[t_name]
                    if c_name in tbl.columns:
                        col = tbl.columns[c_name]
                        if c_type == "PRIMARY KEY":
                            col.is_primary_key = True
                            if c_name not in tbl.primary_key_columns:
                                tbl.primary_key_columns.append(c_name)
                        elif c_type == "FOREIGN KEY":
                            col.is_foreign_key = True
                            col.referenced_schema = row.foreign_table_schema
                            col.referenced_table = row.foreign_table_name
                            col.referenced_column = row.foreign_column_name

        engine.dispose()
        return schemas


class MySQLIntrospector:
    """Introspects MySQL live catalog using information_schema."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def introspect(self) -> dict[str, DiscoveredSchema]:
        engine = create_engine(self.connection_string, pool_pre_ping=True)
        schemas: dict[str, DiscoveredSchema] = {}

        with engine.connect() as conn:
            # Discover schemas (databases)
            schema_stmt = text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT IN ('mysql', 'information_schema', 'performance_schema', 'sys') "
                "ORDER BY schema_name;"
            )
            for row in conn.execute(schema_stmt):
                s_name = row.schema_name
                schemas[s_name] = DiscoveredSchema(schema_name=s_name)

            if not schemas:
                # Default fallback
                db_name = engine.url.database or "default"
                schemas[db_name] = DiscoveredSchema(schema_name=db_name)

            table_stmt = text(
                "SELECT table_schema, table_name, table_type, table_rows "
                "FROM information_schema.tables WHERE table_schema IN :schemas;"
            )
            for row in conn.execute(table_stmt, {"schemas": tuple(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                t_type = "view" if "VIEW" in str(row.table_type).upper() else "table"
                row_cnt = int(row.table_rows or 0)
                schemas[s_name].tables[t_name] = DiscoveredTable(
                    schema_name=s_name, table_name=t_name, table_type=t_type, estimated_row_count=row_cnt
                )

            col_stmt = text(
                "SELECT table_schema, table_name, column_name, data_type, ordinal_position, is_nullable, column_key "
                "FROM information_schema.columns WHERE table_schema IN :schemas ORDER BY ordinal_position;"
            )
            for row in conn.execute(col_stmt, {"schemas": tuple(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                c_name = row.column_name
                if s_name in schemas and t_name in schemas[s_name].tables:
                    tbl = schemas[s_name].tables[t_name]
                    is_pk = (str(row.column_key).upper() == "PRI")
                    col = DiscoveredColumn(
                        column_name=c_name,
                        data_type=row.data_type,
                        ordinal_position=row.ordinal_position,
                        is_nullable=(str(row.is_nullable).upper() == "YES"),
                        is_primary_key=is_pk,
                    )
                    if is_pk and c_name not in tbl.primary_key_columns:
                        tbl.primary_key_columns.append(c_name)
                    tbl.columns[c_name] = col

            fk_stmt = text(
                "SELECT table_schema, table_name, column_name, referenced_table_schema, referenced_table_name, referenced_column_name "
                "FROM information_schema.key_column_usage "
                "WHERE table_schema IN :schemas AND referenced_table_name IS NOT NULL;"
            )
            for row in conn.execute(fk_stmt, {"schemas": tuple(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                c_name = row.column_name
                if s_name in schemas and t_name in schemas[s_name].tables:
                    tbl = schemas[s_name].tables[t_name]
                    if c_name in tbl.columns:
                        col = tbl.columns[c_name]
                        col.is_foreign_key = True
                        col.referenced_schema = row.referenced_table_schema
                        col.referenced_table = row.referenced_table_name
                        col.referenced_column = row.referenced_column_name

        engine.dispose()
        return schemas


class SQLServerIntrospector:
    """Introspects SQL Server catalog using sys & information_schema views."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def introspect(self) -> dict[str, DiscoveredSchema]:
        engine = create_engine(self.connection_string, pool_pre_ping=True)
        schemas: dict[str, DiscoveredSchema] = {}

        with engine.connect() as conn:
            schema_stmt = text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name NOT IN ('guest', 'INFORMATION_SCHEMA', 'sys', 'db_owner', 'db_accessadmin') "
                "ORDER BY schema_name;"
            )
            for row in conn.execute(schema_stmt):
                s_name = row.schema_name
                schemas[s_name] = DiscoveredSchema(schema_name=s_name)

            if not schemas:
                schemas["dbo"] = DiscoveredSchema(schema_name="dbo")

            table_stmt = text(
                "SELECT table_schema, table_name, table_type FROM information_schema.tables WHERE table_schema IN :schemas;"
            )
            for row in conn.execute(table_stmt, {"schemas": tuple(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                t_type = "view" if "VIEW" in str(row.table_type).upper() else "table"
                schemas[s_name].tables[t_name] = DiscoveredTable(
                    schema_name=s_name, table_name=t_name, table_type=t_type, estimated_row_count=0
                )

            col_stmt = text(
                "SELECT table_schema, table_name, column_name, data_type, ordinal_position, is_nullable "
                "FROM information_schema.columns WHERE table_schema IN :schemas ORDER BY ordinal_position;"
            )
            for row in conn.execute(col_stmt, {"schemas": tuple(schemas.keys())}):
                s_name = row.table_schema
                t_name = row.table_name
                c_name = row.column_name
                if s_name in schemas and t_name in schemas[s_name].tables:
                    col = DiscoveredColumn(
                        column_name=c_name,
                        data_type=row.data_type,
                        ordinal_position=row.ordinal_position,
                        is_nullable=(str(row.is_nullable).upper() == "YES"),
                    )
                    schemas[s_name].tables[t_name].columns[c_name] = col

        engine.dispose()
        return schemas


class OracleIntrospector:
    """Introspects Oracle catalog using ALL_* catalog views."""

    def __init__(self, connection_string: str) -> None:
        self.connection_string = connection_string

    def introspect(self) -> dict[str, DiscoveredSchema]:
        engine = create_engine(self.connection_string, pool_pre_ping=True)
        schemas: dict[str, DiscoveredSchema] = {"SYSTEM": DiscoveredSchema(schema_name="SYSTEM")}

        with engine.connect() as conn:
            table_stmt = text(
                "SELECT owner, table_name, num_rows FROM all_tables WHERE owner NOT IN ('SYS', 'SYSTEM', 'OUTLN', 'XDB') ORDER BY table_name"
            )
            for row in conn.execute(table_stmt):
                s_name = row.owner
                t_name = row.table_name
                if s_name not in schemas:
                    schemas[s_name] = DiscoveredSchema(schema_name=s_name)
                schemas[s_name].tables[t_name] = DiscoveredTable(
                    schema_name=s_name, table_name=t_name, table_type="table", estimated_row_count=int(row.num_rows or 0)
                )

            col_stmt = text(
                "SELECT owner, table_name, column_name, data_type, column_id, nullable FROM all_tab_columns WHERE owner IN :schemas ORDER BY column_id"
            )
            if schemas:
                for row in conn.execute(col_stmt, {"schemas": tuple(schemas.keys())}):
                    s_name = row.owner
                    t_name = row.table_name
                    c_name = row.column_name
                    if s_name in schemas and t_name in schemas[s_name].tables:
                        col = DiscoveredColumn(
                            column_name=c_name,
                            data_type=row.data_type,
                            ordinal_position=int(row.column_id or 1),
                            is_nullable=(str(row.nullable).upper() == "Y"),
                        )
                        schemas[s_name].tables[t_name].columns[c_name] = col

        engine.dispose()
        return schemas


def get_introspector(database_type: str, connection_string: str) -> Any:
    """Factory creating dialect-specific catalog introspector."""
    normalized = database_type.strip().lower()
    if normalized in {"postgresql", "postgres"}:
        return PostgreSQLIntrospector(connection_string)
    elif normalized in {"mysql", "mariadb"}:
        return MySQLIntrospector(connection_string)
    elif normalized in {"sqlserver", "mssql", "sql_server"}:
        return SQLServerIntrospector(connection_string)
    elif normalized == "oracle":
        return OracleIntrospector(connection_string)
    return PostgreSQLIntrospector(connection_string)

