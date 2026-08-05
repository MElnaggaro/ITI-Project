"""Seed initial platform tenant and tenant admin user for local development/testing."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path for direct script executions
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from core.security import hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository



def seed() -> None:
    settings = get_settings()
    engine = create_engine(settings.application_database_url)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        tenant_repo = TenantRepository(session)
        user_repo = UserRepository(session)

        # 1. Seed default tenant
        tenant = tenant_repo.get_by_code("demo-tenant")
        if not tenant:
            tenant = tenant_repo.create(
                name="Demo Tenant",
                code="demo-tenant",
                settings={"environment": "development"},
            )
            print(f"Created Tenant: {tenant.name} ({tenant.code}) -> ID: {tenant.id}")
        else:
            print(f"Tenant already exists: {tenant.name} ({tenant.code}) -> ID: {tenant.id}")

        # 2. Seed default tenant admin user
        user = user_repo.get_by_tenant_and_email(tenant.id, "admin@demo.com")
        if not user:
            pwd_hash = hash_password("Admin123456!")
            user = user_repo.create(
                tenant_id=tenant.id,
                email="admin@demo.com",
                password_hash=pwd_hash,
                full_name="Tenant Admin",
                is_tenant_admin=True,
            )
            session.commit()
            print(f"Created Admin User: {user.email} -> ID: {user.id}")
        # 3. Seed default database connections
        from models.database_connection import DatabaseConnection
        from repositories.connection_repository import ConnectionRepository
        from core.encryption import encrypt_secret
        from core.tenant_context import TenantContext

        conn_repo = ConnectionRepository(session)
        
        connections_to_seed = [
            {"name": "Platform PostgreSQL DB", "db_name": "platform_db"},
            {"name": "Sales PostgreSQL DB", "db_name": "platform_db"},
            {"name": "Analytics PostgreSQL DB", "db_name": "platform_db"}
        ]
        
        seeded_conns = []
        for c_data in connections_to_seed:
            conn = conn_repo.get_by_name(tenant.id, c_data["name"])
            if not conn:
                conn = DatabaseConnection(
                    tenant_id=tenant.id,
                    created_by=user.id,
                    name=c_data["name"],
                    database_type="postgresql",
                    host="postgres",
                    port=5432,
                    database_name=c_data["db_name"],
                    username="postgres",
                    encrypted_password=encrypt_secret("postgres", tenant.id),
                    ssl_enabled=False,
                    status="active",
                    schema_sync_status="completed",
                    is_active=True,
                )
                conn_repo.create(conn)
                session.commit()
                print(f"Created Database Connection: {conn.name} -> ID: {conn.id}")
            else:
                print(f"Database Connection already exists: {conn.name} -> ID: {conn.id}")
            seeded_conns.append(conn)

        # We will just use the first one for schema sync below, or we could sync all of them.
        conn = seeded_conns[0]

        # 4. Sync Schema for Connection
        try:
            from services.schema_sync_service import SchemaSyncService
            t_context = TenantContext(
                tenant_id=tenant.id,
                user_id=user.id,
                is_tenant_admin=True,
            )
            sync_service = SchemaSyncService(session)
            sync_res = sync_service.sync_schema(t_context, conn.id)
            session.commit()
            print(f"Synced Schema: {sync_res}")

        except Exception as sync_err:
            print(f"Schema sync notice: {sync_err}", file=sys.stderr)

        # 5. Seed default knowledge base
        from models.knowledge_base import KnowledgeBase
        from repositories.knowledge_base_repository import KnowledgeBaseRepository

        kb_repo = KnowledgeBaseRepository(session)
        kb = kb_repo.get_by_name(tenant.id, "Platform Specifications & Requirements")
        if not kb:
            kb = KnowledgeBase(
                tenant_id=tenant.id,
                created_by=user.id,
                name="Platform Specifications & Requirements",
                description="Knowledge base containing project requirements, architecture specifications, and assignment contracts.",
                embedding_model="bge-large-en-v1.5",
            )
            kb_repo.create(kb)
            session.commit()
            print(f"Created Knowledge Base: {kb.name} -> ID: {kb.id}")
        else:
            print(f"Knowledge Base already exists: {kb.name} -> ID: {kb.id}")

        # 6. Seed & Index Assignment PDF into Qdrant Vector Store
        pdf_path = project_root / "Text_to_SQL_and_Document_Chat_Assignment.pdf"
        if pdf_path.exists():
            from repositories.file_repository import FileRepository
            from services.file_service import FileService
            from services.document_pipeline_service import DocumentPipelineService

            file_repo = FileRepository(session)
            existing_files = file_repo.list_by_tenant(tenant.id)
            existing_file = next((f for f in existing_files if f.original_name == "Text_to_SQL_and_Document_Chat_Assignment.pdf"), None)

            if not existing_file:
                file_svc = FileService(session)
                pdf_bytes = pdf_path.read_bytes()
                uploaded_file = file_svc.upload_file(
                    context=t_context,
                    file_bytes=pdf_bytes,
                    filename="Text_to_SQL_and_Document_Chat_Assignment.pdf",
                    content_type="application/pdf",
                    knowledge_base_id=kb.id,
                )
                session.commit()
                print(f"Uploaded Assignment PDF: {uploaded_file.original_name} -> ID: {uploaded_file.id}")

                pipeline_svc = DocumentPipelineService(session)
                proc_res = pipeline_svc.process_file(t_context, uploaded_file.id)
                session.commit()
                print(f"Indexed PDF into Qdrant Vector Store: {proc_res}")
            else:
                print(f"Assignment PDF already indexed: {existing_file.original_name}")


    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        session.close()



if __name__ == "__main__":
    seed()
