"""Trigger schema sync for pending database connections."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models.database_connection import DatabaseConnection
from services.schema_sync_service import SchemaSyncService
from core.tenant_context import TenantContext


def sync_pending_connections() -> None:
    # Use direct connection string
    try:
        import psycopg
    except ImportError:
        print("❌ Error: This script must be run INSIDE the Docker container.")
        print("Run it using: docker exec fusionisexist-api-1 python scripts/sync_schemas_now.py")
        sys.exit(1)
        
    engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/platform_db")
    
    with Session(engine) as session:
        connections = session.scalars(select(DatabaseConnection).where(DatabaseConnection.schema_sync_status == 'pending')).all()
        
        print(f"Found {len(connections)} connections pending sync.")
        
        if not connections:
            print("No connections need syncing.")
            return

        sync_service = SchemaSyncService(session)
        
        for conn in connections:
            print(f"Syncing connection: {conn.name} ({conn.id})")
            import uuid
            context = TenantContext(
                tenant_id=conn.tenant_id,
                user_id=conn.created_by or uuid.uuid4(),
                is_tenant_admin=True
            )
            try:
                result = sync_service.sync_schema(context, conn.id)
                print(f"Success! Synced {result.get('schemas_count', 0)} schemas, {result.get('tables_count', 0)} tables, {result.get('columns_count', 0)} columns.")
            except Exception as e:
                print(f"Failed to sync {conn.name}: {e}")
                
        session.commit()
        print("Schema sync committed successfully.")

if __name__ == "__main__":
    sync_pending_connections()
