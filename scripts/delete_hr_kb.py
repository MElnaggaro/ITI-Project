"""Delete the HR knowledge base."""

from __future__ import annotations

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models.knowledge_base import KnowledgeBase

def delete_hr_kb() -> None:
    engine = create_engine("postgresql+psycopg://postgres:postgres@postgres:5432/platform_db")
    
    with Session(engine) as session:
        kbs = session.scalars(select(KnowledgeBase).where(KnowledgeBase.name.ilike('%HR%'))).all()
        
        if not kbs:
            print("No Knowledge Base found matching 'HR'.")
            return
            
        for kb in kbs:
            print(f"Deleting Knowledge Base: {kb.name} ({kb.id})")
            session.delete(kb)
            
        session.commit()
        print("Deletion successful.")

if __name__ == "__main__":
    delete_hr_kb()
