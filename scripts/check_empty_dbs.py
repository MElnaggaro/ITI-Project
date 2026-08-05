"""List all database connections and their schema counts."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from models.database_connection import DatabaseConnection
from models.database_schema import DatabaseSchema
from models.database_table import DatabaseTable

def list_connections() -> None:
    engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/platform_db")
    
    with Session(engine) as session:
        connections = session.scalars(select(DatabaseConnection)).all()
        
        print(f"Total connections: {len(connections)}")
        
        for conn in connections:
            schema_count = session.scalar(
                select(func.count(DatabaseSchema.id))
                .where(DatabaseSchema.connection_id == conn.id)
            )
            table_count = session.scalar(
                select(func.count(DatabaseTable.id))
                .join(DatabaseSchema)
                .where(DatabaseSchema.connection_id == conn.id)
            )
            print(f"- {conn.name} ({conn.database_name}): {schema_count} schemas, {table_count} tables")
            
            # Delete if it's one of the dummy ones or truly empty
            if 'mysql' in conn.name.lower() or ('sales' in conn.name.lower() and 'postgresql' in conn.name.lower()) or 'analytics' in conn.name.lower():
                print(f"  -> Deleting dummy connection: {conn.name}")
                session.delete(conn)
            elif schema_count == 0 and table_count == 0 and conn.name != "Platform PostgreSQL DB":
                print(f"  -> Deleting empty connection: {conn.name}")
                session.delete(conn)
        
        session.commit()
        print("Done cleaning up connections.")

if __name__ == "__main__":
    list_connections()
