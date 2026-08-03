"""Schema Synchronization Service executing catalog introspection and atomic metadata upsert."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from core.encryption import decrypt_secret
from core.tenant_context import TenantContext
from models.database_column import DatabaseColumn
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseSchema
from models.database_table import DatabaseTable
from repositories.connection_repository import ConnectionRepository
from services.database.adapter import get_source_adapter
from services.database.introspection import PostgreSQLIntrospector


class SchemaSyncService:
    """Service synchronizing live database source metadata into application cache."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.conn_repo = ConnectionRepository(session)

    def sync_schema(self, context: TenantContext, connection_id: UUID) -> dict[str, Any]:
        """Perform catalog introspection and atomic metadata cache upsert."""
        conn = self.conn_repo.get_by_id(context.tenant_id, connection_id)
        if not conn:
            raise ValueError("Database connection not found.")

        if not conn.is_active:
            raise ValueError("Cannot sync inactive database connection.")

        if conn.database_type.lower() != "postgresql":
            raise ValueError(f"Dialect '{conn.database_type}' is not supported for schema sync.")

        # Decrypt secrets to construct connection string
        plain_pass = decrypt_secret(conn.encrypted_password, context.tenant_id)
        plain_conn_str = decrypt_secret(conn.encrypted_connection_string, context.tenant_id)

        adapter = get_source_adapter(
            database_type=conn.database_type,
            host=conn.host,
            port=conn.port,
            database_name=conn.database_name,
            username=conn.username,
            password=plain_pass,
            connection_string=plain_conn_str,
            ssl_enabled=conn.ssl_enabled,
            ssl_settings=conn.ssl_settings,
            connection_options=conn.connection_options,
        )

        conn_string = adapter.build_connection_string()
        introspector = PostgreSQLIntrospector(conn_string)

        try:
            discovered_schemas = introspector.introspect()
        except Exception as e:
            conn.schema_sync_status = "failed"
            self.session.flush()
            raise ValueError(f"Schema sync introspection failed: {str(e)[:150]}")

        # Atomic transaction on application database
        synced_schemas_count = 0
        synced_tables_count = 0
        synced_columns_count = 0

        for s_name, d_schema in discovered_schemas.items():
            # 1. Upsert DatabaseSchema
            db_schema = self.session.scalar(
                select(DatabaseSchema)
                .where(DatabaseSchema.connection_id == conn.id)
                .where(DatabaseSchema.schema_name == s_name)
            )
            if not db_schema:
                db_schema = DatabaseSchema(
                    tenant_id=conn.tenant_id,
                    connection_id=conn.id,
                    schema_name=s_name,
                    description=d_schema.description,
                )
                self.session.add(db_schema)
                self.session.flush()

            synced_schemas_count += 1

            for t_name, d_table in d_schema.tables.items():
                # 2. Upsert DatabaseTable
                db_table = self.session.scalar(
                    select(DatabaseTable)
                    .where(DatabaseTable.connection_id == conn.id)
                    .where(DatabaseTable.schema_id == db_schema.id)
                    .where(DatabaseTable.table_name == t_name)
                )
                if not db_table:
                    db_table = DatabaseTable(
                        tenant_id=conn.tenant_id,
                        connection_id=conn.id,
                        schema_id=db_schema.id,
                        table_name=t_name,
                        table_type=d_table.table_type,
                        primary_key_columns=d_table.primary_key_columns,
                        is_enabled=True,
                        is_sensitive=False,
                    )
                    self.session.add(db_table)
                    self.session.flush()
                else:
                    db_table.table_type = d_table.table_type
                    db_table.primary_key_columns = d_table.primary_key_columns
                    self.session.flush()

                synced_tables_count += 1

                for c_name, d_col in d_table.columns.items():
                    # 3. Upsert DatabaseColumn
                    db_col = self.session.scalar(
                        select(DatabaseColumn)
                        .where(DatabaseColumn.table_id == db_table.id)
                        .where(DatabaseColumn.column_name == c_name)
                    )
                    if not db_col:
                        db_col = DatabaseColumn(
                            tenant_id=conn.tenant_id,
                            table_id=db_table.id,
                            column_name=c_name,
                            data_type=d_col.data_type,
                            ordinal_position=d_col.ordinal_position,
                            is_nullable=d_col.is_nullable,
                            is_primary_key=d_col.is_primary_key,
                            is_foreign_key=d_col.is_foreign_key,
                            referenced_schema=d_col.referenced_schema,
                            referenced_table=d_col.referenced_table,
                            referenced_column=d_col.referenced_column,
                            is_sensitive=False,
                            sample_values=[],
                        )
                        self.session.add(db_col)
                    else:
                        db_col.data_type = d_col.data_type
                        db_col.ordinal_position = d_col.ordinal_position
                        db_col.is_nullable = d_col.is_nullable
                        db_col.is_primary_key = d_col.is_primary_key
                        db_col.is_foreign_key = d_col.is_foreign_key
                        db_col.referenced_schema = d_col.referenced_schema
                        db_col.referenced_table = d_col.referenced_table
                        db_col.referenced_column = d_col.referenced_column

                    synced_columns_count += 1

        # Mark schema sync healthy
        now = datetime.now(timezone.utc)
        conn.schema_sync_status = "healthy"
        conn.last_schema_sync_at = now
        conn.status = "healthy"
        self.session.flush()

        return {
            "connection_id": str(conn.id),
            "status": "healthy",
            "schemas_count": synced_schemas_count,
            "tables_count": synced_tables_count,
            "columns_count": synced_columns_count,
            "synced_at": now.isoformat(),
        }
