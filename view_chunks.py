from sqlalchemy import create_engine, text
from app.config import get_settings
engine = create_engine(get_settings().application_database_url)
with engine.connect() as conn:
    rows = conn.execute(text("SELECT chunk_index, content FROM document_chunks WHERE file_id='06d34858-8fb1-4148-b251-e55875c40731' ORDER BY chunk_index")).fetchall()
    for r in rows:
        print(f"=== Chunk {r[0]} ===")
        print(r[1][:300])
        print()
