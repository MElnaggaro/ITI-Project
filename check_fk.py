from sqlalchemy import create_engine, text
from app.config import get_settings

engine = create_engine(get_settings().application_database_url)
with engine.connect() as conn:
    rows = conn.execute(text("""
        SELECT
            tc.table_name, 
            kcu.column_name, 
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name, 
            rc.delete_rule
        FROM 
            information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
              ON rc.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = 'document_chunks';
    """)).fetchall()
    
    print("Foreign Keys on document_chunks:")
    for r in rows:
        print(f"  {r[1]} -> {r[2]}.{r[3]} ON DELETE {r[4]}")
