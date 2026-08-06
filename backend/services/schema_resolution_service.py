"""Schema resolution service building request-specific ResolvedSchema contracts."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.tenant_context import TenantContext
from models.database_column import DatabaseColumn
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseSchema
from models.database_table import DatabaseTable
from repositories.connection_repository import ConnectionRepository
from schemas.resolved_schema import (
    ResolvedColumn,
    ResolvedRelationship,
    ResolvedSchema,
    ResolvedTable,
)
from services.permission_service import PermissionService
from services.row_filter_compiler import RowFilterCompiler


class SchemaResolutionService:
    """Resolves short-lived, request-specific ResolvedSchema for Text-to-SQL generation."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.conn_repo = ConnectionRepository(session)
        self.perm_service = PermissionService(session)

    def resolve_schema(self, context: TenantContext, connection_id: UUID) -> ResolvedSchema:
        """Build request-specific ResolvedSchema enforcing deterministic permissions."""
        conn = self.conn_repo.get_by_id(context.tenant_id, connection_id)
        if not conn or not conn.is_active:
            raise ValueError("Database connection not found or inactive.")

        if conn.status != "healthy":
            raise ValueError("Database connection is not in healthy state.")

        if conn.schema_sync_status != "healthy":
            raise ValueError("Database connection schema is not synchronized.")

        # Fetch cached tables
        tables = list(
            self.session.scalars(
                select(DatabaseTable)
                .where(DatabaseTable.connection_id == conn.id)
                .where(DatabaseTable.is_enabled == True)
            ).all()
        )

        resolved_schema = ResolvedSchema(
            tenant_id=context.tenant_id,
            user_id=context.user_id,
            connection_id=conn.id,
            database_type=conn.database_type,
        )

        compiler = RowFilterCompiler(context)

        for tbl in tables:
            # 1. Resolve table permission
            eff_table = self.perm_service.resolve_effective_table_permission(
                tenant_id=context.tenant_id,
                user_id=context.user_id,
                connection_id=conn.id,
                table_id=tbl.id,
            )

            # Omit unreadable table completely
            if not eff_table.can_read:
                continue

            # Get schema_name
            schema_obj = self.session.scalar(
                select(DatabaseSchema).where(DatabaseSchema.id == tbl.schema_id)
            )
            s_name = schema_obj.schema_name if schema_obj else "public"

            # 2. Build resolved columns
            resolved_cols: dict[str, ResolvedColumn] = {}
            for col_name, eff_col in eff_table.column_rules.items():
                if not eff_col.can_read:
                    continue

                db_col = self.session.scalar(
                    select(DatabaseColumn)
                    .where(DatabaseColumn.table_id == tbl.id)
                    .where(DatabaseColumn.column_name == col_name)
                )

                resolved_cols[col_name] = ResolvedColumn(
                    column_id=eff_col.column_id,
                    column_name=col_name,
                    data_type=db_col.data_type if db_col else "varchar",
                    is_primary_key=db_col.is_primary_key if db_col else False,
                    is_foreign_key=db_col.is_foreign_key if db_col else False,
                    can_read=eff_col.can_read,
                    can_filter=eff_col.can_filter,
                    can_aggregate=eff_col.can_aggregate,
                    mask_type=eff_col.mask_type,
                )

            # 3. Compile row filters
            compiled_filters = []
            for rf in eff_table.effective_row_filters:
                c_ast = compiler.compile(rf)
                if c_ast is not None:
                    compiled_filters.append(c_ast)

            resolved_tbl = ResolvedTable(
                table_id=tbl.id,
                schema_name=s_name,
                table_name=tbl.table_name,
                table_type=tbl.table_type,
                description=tbl.description,
                can_read=True,
                can_insert=eff_table.can_insert,
                can_update=eff_table.can_update,
                can_delete=eff_table.can_delete,
                columns=resolved_cols,
                primary_key_columns=tbl.primary_key_columns,
                compiled_row_filters=compiled_filters,
                raw_row_filters=eff_table.effective_row_filters,
            )

            resolved_schema.tables[tbl.table_name] = resolved_tbl

        # 4. Resolve relationships between readable tables
        self._resolve_relationships(resolved_schema)

        return resolved_schema

    def _resolve_relationships(self, resolved_schema: ResolvedSchema) -> None:
        """Add relationship metadata connecting readable tables & readable join columns."""
        table_ids = [t.table_id for t in resolved_schema.tables.values()]
        if not table_ids:
            return

        cols_with_fk = list(
            self.session.scalars(
                select(DatabaseColumn)
                .where(DatabaseColumn.table_id.in_(table_ids))
                .where(DatabaseColumn.is_foreign_key == True)
            ).all()
        )

        for col in cols_with_fk:
            if not col.referenced_table or not col.referenced_column:
                continue

            target_tbl_name = col.referenced_table
            if target_tbl_name in resolved_schema.tables:
                src_tbl = self.session.scalar(
                    select(DatabaseTable).where(DatabaseTable.id == col.table_id)
                )
                if not src_tbl or src_tbl.table_name not in resolved_schema.tables:
                    continue

                tgt_tbl = resolved_schema.tables[target_tbl_name]
                src_tbl_obj = resolved_schema.tables[src_tbl.table_name]

                # Both join columns must be readable
                if (
                    col.column_name in src_tbl_obj.columns
                    and col.referenced_column in tgt_tbl.columns
                ):
                    rel = ResolvedRelationship(
                        source_table_id=src_tbl_obj.table_id,
                        source_table_name=src_tbl.table_name,
                        source_column_name=col.column_name,
                        target_table_id=tgt_tbl.table_id,
                        target_table_name=target_tbl_name,
                        target_column_name=col.referenced_column,
                    )
                    resolved_schema.relationships.append(rel)
