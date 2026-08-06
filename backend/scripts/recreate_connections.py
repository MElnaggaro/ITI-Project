"""Re-create the real database connections properly."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models.database_connection import DatabaseConnection
from models.tenant import Tenant
from core.encryption import encrypt_secret

def create_connections() -> None:
    engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/platform_db")
    
    with Session(engine) as session:
        # Get the tenant ID
        tenant = session.scalars(select(Tenant).limit(1)).first()
        if not tenant:
            print("No tenant found.")
            return

        # Create Sales DB
        sales_conn = session.scalars(select(DatabaseConnection).where(DatabaseConnection.name == 'E-Commerce Sales DB')).first()
        if not sales_conn:
            sales_conn = DatabaseConnection(
                tenant_id=tenant.id,
                name='E-Commerce Sales DB',
                database_type='postgresql',
                host='postgres',
                port=5432,
                database_name='sales_db',
                username='postgres',
                encrypted_password=encrypt_secret('postgres', tenant.id),
                encrypted_connection_string=None, # IMPORTANT! Force adapter to use individual fields
                schema_sync_status='pending',
            )
            session.add(sales_conn)
            print("Created Sales DB connection.")
        
        # Update HR DB
        hr_conn = session.scalars(select(DatabaseConnection).where(DatabaseConnection.name == 'Corporate HR DB')).first()
        if hr_conn:
            hr_conn.database_name = 'hr_db'
            hr_conn.encrypted_connection_string = None # IMPORTANT!
            hr_conn.schema_sync_status = 'pending'
            print("Updated HR DB connection.")
        else:
            hr_conn = DatabaseConnection(
                tenant_id=tenant.id,
                name='Corporate HR DB',
                database_type='postgresql',
                host='postgres',
                port=5432,
                database_name='hr_db',
                username='postgres',
                encrypted_password=encrypt_secret('postgres', tenant.id),
                encrypted_connection_string=None,
                schema_sync_status='pending',
            )
            session.add(hr_conn)
            print("Created HR DB connection.")

        # Clean up any leftover schemas for HR DB (since it synced the wrong ones)
        from models.database_schema import DatabaseSchema
        schemas_to_delete = session.scalars(select(DatabaseSchema).where(DatabaseSchema.connection_id == hr_conn.id)).all()
        for s in schemas_to_delete:
            session.delete(s)
            
        session.commit()
        print("Done configuring connections.")

if __name__ == "__main__":
    create_connections()
