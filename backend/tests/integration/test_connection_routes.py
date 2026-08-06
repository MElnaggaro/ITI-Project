"""Integration tests for DatabaseConnection management endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_connection_lifecycle_and_secret_redaction(client: TestClient, db_session: Session):
    """Test connection CRUD, secret redaction, and connectivity test probe as tenant admin."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("Conn Tenant", "conn-tenant")
    admin_user = user_repo.create(
        tenant_id=tenant.id,
        email="admin@conn.com",
        password_hash=hash_password("Pass123!"),
        is_tenant_admin=True,
    )
    db_session.commit()

    admin_token = create_access_token(tenant.id, admin_user.id, is_tenant_admin=True)
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Create connection
    create_resp = client.post(
        "/api/database-connections",
        json={
            "name": "Production Postgres",
            "database_type": "postgresql",
            "host": "db.example.com",
            "port": 5432,
            "database_name": "app_db",
            "username": "admin_user",
            "password": "SuperSecretPassword123!",
            "ssl_enabled": True,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    conn_data = create_resp.json()
    conn_id = conn_data["id"]

    # Assert secrets are NEVER returned in response
    assert "password" not in conn_data
    assert "encrypted_password" not in conn_data
    assert conn_data["name"] == "Production Postgres"
    assert conn_data["status"] == "pending"

    # 2. Get connection detail
    get_resp = client.get(f"/api/database-connections/{conn_id}", headers=headers)
    assert get_resp.status_code == 200
    detail = get_resp.json()
    assert "password" not in detail
    assert "encrypted_password" not in detail

    # 3. Test connection (mock test with unreachable host returns failed status safely)
    test_resp = client.post(f"/api/database-connections/{conn_id}/test", headers=headers)
    assert test_resp.status_code == 200
    test_data = test_resp.json()
    assert test_data["status"] in {"healthy", "failed"}
    assert "tested_at" in test_data

    # 4. Update connection
    update_resp = client.put(
        f"/api/database-connections/{conn_id}",
        json={
            "name": "Updated Postgres Name",
            "host": "db.example.com",
            "port": 5432,
            "database_name": "app_db",
            "username": "admin_user",
            "ssl_enabled": True,
            "is_active": True,
        },
        headers=headers,
    )
    assert update_resp.status_code == 200
    updated_data = update_resp.json()
    assert updated_data["name"] == "Updated Postgres Name"
    # Status reset to pending on update
    assert updated_data["status"] == "pending"

    # 5. Delete connection
    del_resp = client.delete(f"/api/database-connections/{conn_id}", headers=headers)
    assert del_resp.status_code == 204
