"""Integration tests for roles and permission administration routes."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from repositories.connection_repository import ConnectionRepository
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from models.database_table import DatabaseTable
from models.database_column import DatabaseColumn


def test_roles_and_permissions_admin_lifecycle(client: TestClient, db_session: Session):
    """Test role CRUD, user assignment, and table/column permission endpoints as tenant admin."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)
    conn_repo = ConnectionRepository(db_session)

    tenant = tenant_repo.create("Perm Tenant", "perm-tenant")
    admin_user = user_repo.create(
        tenant_id=tenant.id,
        email="admin@perm.com",
        password_hash=hash_password("Pass123!"),
        is_tenant_admin=True,
    )
    normal_user = user_repo.create(
        tenant_id=tenant.id,
        email="user@perm.com",
        password_hash=hash_password("Pass123!"),
        is_tenant_admin=False,
    )

    db_session.commit()

    admin_token = create_access_token(tenant.id, admin_user.id, is_tenant_admin=True)
    normal_token = create_access_token(tenant.id, normal_user.id, is_tenant_admin=False)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Non-admin is forbidden (403)
    forbidden_resp = client.get("/api/roles", headers={"Authorization": f"Bearer {normal_token}"})
    assert forbidden_resp.status_code == 403

    # 2. Create Role as Admin
    create_role_resp = client.post(
        "/api/roles",
        json={"name": "DataAnalyst", "description": "Analyst role"},
        headers=headers,
    )
    assert create_role_resp.status_code == 201
    role_data = create_role_resp.json()
    role_id = role_data["id"]
    assert role_data["name"] == "DataAnalyst"

    # 3. Assign role to normal user
    assign_resp = client.put(
        f"/api/users/{normal_user.id}/roles",
        json={"role_ids": [role_id]},
        headers=headers,
    )
    assert assign_resp.status_code == 200
    assigned_roles = assign_resp.json()
    assert len(assigned_roles) == 1
    assert assigned_roles[0]["id"] == role_id

    # 4. Create dummy connection, table, and column
    from models.database_connection import DatabaseConnection
    conn = DatabaseConnection(tenant_id=tenant.id, name="perm_conn", database_type="postgresql")
    db_session.add(conn)
    db_session.commit()

    tbl = DatabaseTable(tenant_id=tenant.id, connection_id=conn.id, table_name="customers")
    db_session.add(tbl)
    db_session.commit()

    col = DatabaseColumn(tenant_id=tenant.id, table_id=tbl.id, column_name="ssn", data_type="varchar", is_sensitive=True)
    db_session.add(col)
    db_session.commit()

    # 5. Create Table Permission
    perm_resp = client.post(
        "/api/permissions/table",
        json={
            "connection_id": str(conn.id),
            "table_id": str(tbl.id),
            "role_id": role_id,
            "can_read": True,
            "row_filter": {"status": {"eq": "active"}},
        },
        headers=headers,
    )
    assert perm_resp.status_code == 201
    perm_data = perm_resp.json()
    perm_id = perm_data["id"]
    assert perm_data["can_read"] is True

    # 6. Replace Column Permissions
    col_rule_resp = client.put(
        f"/api/permissions/table/{perm_id}/columns",
        json=[
            {
                "column_id": str(col.id),
                "can_read": True,
                "can_filter": True,
                "can_aggregate": False,
                "mask_type": "last4",
            }
        ],
        headers=headers,
    )
    assert col_rule_resp.status_code == 200
    col_rules = col_rule_resp.json()
    assert len(col_rules) == 1
    assert col_rules[0]["mask_type"] == "last4"
