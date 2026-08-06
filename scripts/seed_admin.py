"""Seed initial platform tenant and tenant admin user for local development/testing."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path for direct script executions
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from core.security import hash_password
from repositories.tenant_repository import TenantRepository
from repositories.user_repository import UserRepository
from models.database_connection import DatabaseConnection
from repositories.connection_repository import ConnectionRepository
from core.encryption import encrypt_secret
from core.tenant_context import TenantContext
from services.schema_sync_service import SchemaSyncService
from models.knowledge_base import KnowledgeBase
from repositories.knowledge_base_repository import KnowledgeBaseRepository
from repositories.file_repository import FileRepository
from services.file_service import FileService
from services.document_pipeline_service import DocumentPipelineService



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
        # 3. Seed database connections
        conn_repo = ConnectionRepository(session)

        connections_to_seed: list[dict[str, str | int]] = [
            {"name": "Platform PostgreSQL DB", "db_name": "platform_db", "type": "postgresql", "port": 5432},
        ]

        # Create some dummy tables to make the database look "full"
        session.execute(text("CREATE TABLE IF NOT EXISTS sales_orders (id SERIAL PRIMARY KEY, amount INT, order_date DATE);"))
        session.execute(text("CREATE TABLE IF NOT EXISTS analytics_events (id SERIAL PRIMARY KEY, event_type VARCHAR(50), user_id INT);"))
        session.execute(text("CREATE TABLE IF NOT EXISTS marketing_campaigns (id SERIAL PRIMARY KEY, name VARCHAR(100), budget INT);"))
        session.execute(text("CREATE TABLE IF NOT EXISTS customer_profiles (id SERIAL PRIMARY KEY, name VARCHAR(100), email VARCHAR(100), phone VARCHAR(20));"))
        session.execute(text("CREATE TABLE IF NOT EXISTS inventory_items (id SERIAL PRIMARY KEY, sku VARCHAR(50), quantity INT, price DECIMAL);"))
        session.commit()

        seeded_conns: list[DatabaseConnection] = []
        for c_data in connections_to_seed:
            conn_name = str(c_data["name"])
            db_type = str(c_data["type"])
            db_name = str(c_data["db_name"])
            db_port = int(c_data["port"])

            conn = conn_repo.get_by_name(tenant.id, conn_name)
            if not conn:
                conn = DatabaseConnection(
                    tenant_id=tenant.id,
                    created_by=user.id,
                    name=conn_name,
                    database_type=db_type,
                    host="postgres" if db_type == "postgresql" else "mysql-host",
                    port=db_port,
                    database_name=db_name,
                    username="postgres" if db_type == "postgresql" else "root",
                    encrypted_password=encrypt_secret("password", tenant.id),
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


        # 4. Sync Schema for All Connections
        t_context = TenantContext(
            tenant_id=tenant.id,
            user_id=user.id,
            is_tenant_admin=True,
        )
        sync_service = SchemaSyncService(session)
        for c in seeded_conns:
            if c.database_type == "mysql":
                print(f"Skipping schema sync for {c.name} (mock database).")
                continue
            try:
                sync_res = sync_service.sync_schema(t_context, c.id)
                session.commit()
                print(f"Synced Schema for {c.name}: {sync_res}")
            except Exception as sync_err:
                print(f"Schema sync notice for {c.name}: {sync_err}", file=sys.stderr)

        # 5. Seed default knowledge base
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

        # 6. Seed & Index Files into Qdrant Vector Store
        files_to_seed = [
            "large_knowledge_base_updated.txt",
            "test_kb_doc1.txt",
            "test_kb_data2.csv"
        ]

        
        file_repo = FileRepository(session)
        file_svc = FileService(session)
        pipeline_svc = DocumentPipelineService(session)
        existing_files = file_repo.list_by_tenant(tenant.id)
        
        for filename in files_to_seed:
            file_path = project_root / filename
            if file_path.exists():
                existing_file = next((f for f in existing_files if f.original_name == filename), None)
                if not existing_file:
                    file_bytes = file_path.read_bytes()
                    content_type = "text/plain" if filename.endswith(".txt") else "text/csv" if filename.endswith(".csv") else "application/pdf"
                    uploaded_file = file_svc.upload_file(
                        context=t_context,
                        file_bytes=file_bytes,
                        filename=filename,
                        content_type=content_type,
                        knowledge_base_id=kb.id,
                    )
                    session.commit()
                    print(f"Uploaded File: {uploaded_file.original_name} -> ID: {uploaded_file.id}")

                    proc_res = pipeline_svc.process_file(t_context, uploaded_file.id)
                    session.commit()
                    print(f"Indexed File into Qdrant Vector Store: {proc_res}")
                else:
                    print(f"File already indexed: {existing_file.original_name}")


    except Exception as e:
        session.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        session.close()



if __name__ == "__main__":
    seed()
