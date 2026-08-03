"""Permission repository for TablePermission and ColumnPermission operations."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from models.column_permission import ColumnPermission
from models.database_column import DatabaseColumn
from models.database_connection import DatabaseConnection
from models.database_table import DatabaseTable
from models.table_permission import TablePermission
from repositories.base import BaseTenantRepository, to_uuid
from schemas.permissions import ColumnPermissionRule, TablePermissionCreate, TablePermissionUpdate


class PermissionRepository(BaseTenantRepository[TablePermission]):
    """Repository operations for TablePermission and ColumnPermission entities."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, TablePermission)

    def get_permission_with_columns(
        self,
        tenant_id: UUID | str,
        permission_id: UUID | str,
    ) -> TablePermission | None:
        """Fetch TablePermission with its ColumnPermissions eager loaded."""
        perm = self.get_by_id(tenant_id, permission_id)
        return perm

    def get_direct_user_grant(
        self,
        tenant_id: UUID | str,
        user_id: UUID | str,
        connection_id: UUID | str,
        table_id: UUID | str,
    ) -> TablePermission | None:
        """Fetch direct user table permission grant if present."""
        t_id = to_uuid(tenant_id)
        u_id = to_uuid(user_id)
        conn_id = to_uuid(connection_id)
        tbl_id = to_uuid(table_id)

        stmt = (
            select(TablePermission)
            .where(TablePermission.tenant_id == t_id)
            .where(TablePermission.user_id == u_id)
            .where(TablePermission.connection_id == conn_id)
            .where(TablePermission.table_id == tbl_id)
        )
        return self.session.scalar(stmt)

    def get_role_grants_for_user(
        self,
        tenant_id: UUID | str,
        role_ids: list[UUID],
        connection_id: UUID | str,
        table_id: UUID | str,
    ) -> list[TablePermission]:
        """Fetch table permissions matching any of the user's role_ids."""
        if not role_ids:
            return []
        t_id = to_uuid(tenant_id)
        conn_id = to_uuid(connection_id)
        tbl_id = to_uuid(table_id)

        stmt = (
            select(TablePermission)
            .where(TablePermission.tenant_id == t_id)
            .where(TablePermission.role_id.in_(role_ids))
            .where(TablePermission.connection_id == conn_id)
            .where(TablePermission.table_id == tbl_id)
        )
        return list(self.session.scalars(stmt).all())

    def get_column_permissions(self, table_permission_id: UUID | str) -> list[ColumnPermission]:
        """Fetch all ColumnPermission records for a TablePermission."""
        p_id = to_uuid(table_permission_id)
        stmt = select(ColumnPermission).where(ColumnPermission.table_permission_id == p_id)
        return list(self.session.scalars(stmt).all())

    def create_table_permission(
        self,
        tenant_id: UUID | str,
        data: TablePermissionCreate,
    ) -> TablePermission:
        """Create a new TablePermission record after validating target connection & table."""
        t_id = to_uuid(tenant_id)
        conn_id = to_uuid(data.connection_id)
        tbl_id = to_uuid(data.table_id)

        # Validate connection belongs to tenant
        conn = self.session.scalar(
            select(DatabaseConnection)
            .where(DatabaseConnection.tenant_id == t_id)
            .where(DatabaseConnection.id == conn_id)
        )
        if not conn:
            raise ValueError("Connection not found or belongs to another tenant.")

        # Validate table belongs to connection & tenant
        tbl = self.session.scalar(
            select(DatabaseTable)
            .where(DatabaseTable.tenant_id == t_id)
            .where(DatabaseTable.connection_id == conn_id)
            .where(DatabaseTable.id == tbl_id)
        )
        if not tbl:
            raise ValueError("Table not found or does not belong to specified connection.")

        perm = TablePermission(
            tenant_id=t_id,
            connection_id=conn_id,
            table_id=tbl_id,
            role_id=to_uuid(data.role_id) if data.role_id else None,
            user_id=to_uuid(data.user_id) if data.user_id else None,
            can_read=data.can_read,
            can_insert=data.can_insert,
            can_update=data.can_update,
            can_delete=data.can_delete,
            row_filter=data.row_filter,
        )
        self.session.add(perm)
        self.session.flush()
        return perm

    def update_table_permission(
        self,
        tenant_id: UUID | str,
        permission_id: UUID | str,
        data: TablePermissionUpdate,
    ) -> TablePermission | None:
        """Update an existing TablePermission."""
        perm = self.get_by_id(tenant_id, permission_id)
        if not perm:
            return None
        perm.can_read = data.can_read
        perm.can_insert = data.can_insert
        perm.can_update = data.can_update
        perm.can_delete = data.can_delete
        perm.row_filter = data.row_filter
        self.session.flush()
        return perm

    def delete_table_permission(self, tenant_id: UUID | str, permission_id: UUID | str) -> bool:
        """Delete a TablePermission by ID."""
        perm = self.get_by_id(tenant_id, permission_id)
        if not perm:
            return False
        self.session.delete(perm)
        self.session.flush()
        return True

    def replace_column_permissions(
        self,
        tenant_id: UUID | str,
        permission_id: UUID | str,
        rules: list[ColumnPermissionRule],
    ) -> list[ColumnPermission]:
        """Atomically replace column rules for a TablePermission."""
        perm = self.get_by_id(tenant_id, permission_id)
        if not perm:
            raise ValueError("Table permission not found.")

        col_ids = [r.column_id for r in rules]
        # Validate columns belong to table & tenant
        valid_cols = list(
            self.session.scalars(
                select(DatabaseColumn)
                .where(DatabaseColumn.tenant_id == to_uuid(tenant_id))
                .where(DatabaseColumn.table_id == perm.table_id)
                .where(DatabaseColumn.id.in_([to_uuid(c) for c in col_ids]))
            ).all()
        )
        if len(valid_cols) != len(set(col_ids)):
            raise ValueError("One or more column IDs are invalid or do not belong to the target table.")

        # Delete existing column_permissions
        self.session.execute(
            delete(ColumnPermission).where(ColumnPermission.table_permission_id == perm.id)
        )

        # Add new column_permissions
        created_rules: list[ColumnPermission] = []
        for r in rules:
            cp = ColumnPermission(
                table_permission_id=perm.id,
                column_id=to_uuid(r.column_id),
                can_read=r.can_read,
                can_filter=r.can_filter,
                can_aggregate=r.can_aggregate,
                mask_type=r.mask_type,
            )
            self.session.add(cp)
            created_rules.append(cp)

        self.session.flush()
        return created_rules
