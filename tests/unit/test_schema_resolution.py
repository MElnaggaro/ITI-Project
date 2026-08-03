"""Unit tests for SchemaResolutionService and request-specific ResolvedSchema generation."""

from uuid import uuid4

import pytest

from core.security import hash_password
from core.tenant_context import TenantContext
from models.database_column import DatabaseColumn
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseSchema
from models.database_table import DatabaseTable
from repositories.permission_repository import PermissionRepository
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from schemas.permissions import TablePermissionCreate
from services.schema_resolution_service import SchemaResolutionService


def test_schema_resolution_with_permissions(db_session):
    """Verify ResolvedSchema includes only permitted tables/columns and applies row-filter ASTs."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)
    perm_repo = PermissionRepository(db_session)

    tenant = tenant_repo.create("Res Tenant", "res-tenant")
    user = user_repo.create(tenant.id, "res@user.com", hash_password("pass"))

    # Create dummy connection, schema, tables
    conn = DatabaseConnection(
        id=uuid4(),
        tenant_id=tenant.id,
        name="res_conn",
        database_type="postgresql",
        status="healthy",
        schema_sync_status="healthy",
        is_active=True,
    )
    s_obj = DatabaseSchema(id=uuid4(), tenant_id=tenant.id, connection_id=conn.id, schema_name="sales")
    t1 = DatabaseTable(id=uuid4(), tenant_id=tenant.id, connection_id=conn.id, schema_id=s_obj.id, table_name="orders", is_enabled=True)
    t2 = DatabaseTable(id=uuid4(), tenant_id=tenant.id, connection_id=conn.id, schema_id=s_obj.id, table_name="secret_table", is_enabled=True)

    c1 = DatabaseColumn(id=uuid4(), tenant_id=tenant.id, table_id=t1.id, column_name="id", data_type="uuid", is_primary_key=True)
    c2 = DatabaseColumn(id=uuid4(), tenant_id=tenant.id, table_id=t1.id, column_name="amount", data_type="numeric")
    c3 = DatabaseColumn(id=uuid4(), tenant_id=tenant.id, table_id=t2.id, column_name="secret_key", data_type="text")

    db_session.add_all([conn, s_obj, t1, t2, c1, c2, c3])
    db_session.commit()

    # Grant read access only for 'orders' table
    perm_repo.create_table_permission(
        tenant.id,
        TablePermissionCreate(
            connection_id=conn.id,
            table_id=t1.id,
            user_id=user.id,
            can_read=True,
            row_filter={"amount": {"gte": 100}},
        ),
    )

    context = TenantContext(tenant_id=tenant.id, user_id=user.id)
    service = SchemaResolutionService(db_session)

    resolved = service.resolve_schema(context, conn.id)

    assert not resolved.is_empty()
    assert "orders" in resolved.tables
    assert "secret_table" not in resolved.tables, "Unpermitted table must be omitted completely."

    orders_tbl = resolved.tables["orders"]
    assert "id" in orders_tbl.columns
    assert "amount" in orders_tbl.columns
    assert len(orders_tbl.compiled_row_filters) == 1
    assert "amount >= 100" in orders_tbl.compiled_row_filters[0].sql()
