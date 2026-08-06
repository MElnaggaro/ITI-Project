"""Integration tests for file upload, listing, detail, reprocessing, and deletion endpoints."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from core.security import create_access_token, hash_password
from models.knowledge_base import KnowledgeBase
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository


def test_file_upload_and_lifecycle_routes(client: TestClient, db_session: Session):
    """Test file upload, metadata detail, listing, reprocessing, and deletion endpoints."""
    tenant_repo = TenantRepository(db_session)
    user_repo = UserRepository(db_session)

    tenant = tenant_repo.create("File Tenant", "file-tenant")
    user = user_repo.create(
        tenant_id=tenant.id,
        email="user@file.com",
        password_hash=hash_password("Pass123!"),
    )
    db_session.commit()

    token = create_access_token(tenant.id, user.id, is_tenant_admin=False)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload valid TXT file
    files = {"file": ("sample.txt", b"Hello text file content", "text/plain")}
    upload_resp = client.post("/api/files/upload", files=files, headers=headers)
    assert upload_resp.status_code == 201
    file_data = upload_resp.json()
    file_id = file_data["id"]
    assert file_data["original_name"] == "sample.txt"
    assert file_data["processing_status"] == "pending"

    # 2. Upload invalid extension (.exe)
    invalid_files = {"file": ("script.exe", b"binary content", "application/octet-stream")}
    bad_upload_resp = client.post("/api/files/upload", files=invalid_files, headers=headers)
    assert bad_upload_resp.status_code == 400

    # 3. List files
    list_resp = client.get("/api/files", headers=headers)
    assert list_resp.status_code == 200
    file_list = list_resp.json()
    assert len(file_list) == 1

    # 4. Get file detail
    detail_resp = client.get(f"/api/files/{file_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == file_id

    # 5. Reprocess file
    reprocess_resp = client.post(f"/api/files/{file_id}/reprocess", headers=headers)
    assert reprocess_resp.status_code == 200
    assert reprocess_resp.json()["processing_status"] == "pending"

    # 6. Associate with Knowledge Base
    kb = KnowledgeBase(tenant_id=tenant.id, name="KB One")
    db_session.add(kb)
    db_session.commit()

    assoc_resp = client.post(
        f"/api/knowledge-bases/{kb.id}/files",
        json={"file_id": file_id},
        headers=headers,
    )
    assert assoc_resp.status_code == 200
    assert assoc_resp.json()["knowledge_base_id"] == str(kb.id)

    # 7. Delete file
    del_resp = client.delete(f"/api/files/{file_id}", headers=headers)
    assert del_resp.status_code == 204
