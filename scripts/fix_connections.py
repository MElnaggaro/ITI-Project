"""Update failing database connections to point to the newly created sales_db and hr_db."""

from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.config import get_settings
from models.database_connection import DatabaseConnection
from core.encryption import encrypt_secret

def update_connections() -> None:
    settings = get_settings()
    engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/platform_db")
    
    with Session(engine) as session:
        connections = session.scalars(select(DatabaseConnection)).all()
        
        print(f"Found {len(connections)} connections.")
        
        # We need 2 connections to update to sales_db and hr_db.
        # Leave the first one (which is likely the working one) alone if it works.
        # But we'll just find any failing or non-postgres connections and replace them.
        
        updates = [
            {
                "name": "E-Commerce Sales DB",
                "database_name": "sales_db"
            },
            {
                "name": "Corporate HR DB",
                "database_name": "hr_db"
            }
        ]
        
        update_idx = 0
        for conn in connections:
            print(f"Checking connection: {conn.name} (Host: {conn.host}, DB: {conn.database_name})")
            if 'marketing' in conn.name.lower() or 'mysql' in conn.name.lower():
                pass # Already updated
            elif 'sales' in conn.name.lower() and 'postgresql' in conn.name.lower():
                print(f"Updating '{conn.name}' to 'Corporate HR DB'")
                conn.name = 'Corporate HR DB'
                conn.database_type = 'postgresql'
                conn.host = 'postgres'
                conn.port = 5432
                conn.database_name = 'hr_db'
                conn.username = 'postgres'
                conn.encrypted_password = encrypt_secret('postgres', conn.tenant_id)
                conn.schema_sync_status = 'pending'
            elif 'analytics' in conn.name.lower():
                print(f"Deleting leftover failing connection '{conn.name}'")
                session.delete(conn)
        
        session.commit()
        print("Done updating connections.")

if __name__ == "__main__":
    update_connections()
