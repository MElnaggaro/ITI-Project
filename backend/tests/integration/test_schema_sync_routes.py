"""Integration tests for cached schema inspection and sync routes."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from models.database_column import DatabaseColumn
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseSchema
from models.database_table import DatabaseTable
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_cached_schema_and_table_endpoints(client: TestClient, db_session: Session):
    """Test GET /api/database-connections/{id}/schemas and /tables endpoints."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Sync Tenant", "sync-tenant")
    admin_user = user_repo.create(
        tenant_id=tenant.id,
        email="admin@sync.com",
        password_hash=hash_password("Pass123!"),
        is_tenant_admin=True,
    )

    conn = DatabaseConnection(
        id=uuid4(),
        tenant_id=tenant.id,
        name="sync_conn",
        database_type="postgresql",
        status="healthy",
        schema_sync_status="healthy",
        is_active=True,
    )
    s_obj = DatabaseSchema(id=uuid4(), tenant_id=tenant.id, connection_id=conn.id, schema_name="public")
    tbl = DatabaseTable(id=uuid4(), tenant_id=tenant.id, connection_id=conn.id, schema_id=s_obj.id, table_name="users")
    col = DatabaseColumn(id=uuid4(), tenant_id=tenant.id, table_id=tbl.id, column_name="email", data_type="varchar")

    db_session.add_all([conn, s_obj, tbl, col])
    db_session.commit()

    admin_token = create_access_token(tenant.id, admin_user.id, is_tenant_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Test GET /schemas
    schemas_resp = client.get(f"/api/database-connections/{conn.id}/schemas", headers=headers)
    assert schemas_resp.status_code == 200
    schemas_data = schemas_resp.json()
    assert len(schemas_data) == 1
    assert schemas_data[0]["schema_name"] == "public"

    # 2. Test GET /tables
    tables_resp = client.get(f"/api/database-connections/{conn.id}/tables", headers=headers)
    assert tables_resp.status_code == 200
    tables_data = tables_resp.json()
    assert len(tables_data) == 1
    assert tables_data[0]["table_name"] == "users"
    assert len(tables_data[0]["columns"]) == 1
    assert tables_data[0]["columns"][0]["column_name"] == "email"
