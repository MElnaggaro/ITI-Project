from sqlalchemy import create_engine, text
from app.config import get_settings

engine = create_engine(get_settings().application_database_url)
with engine.connect() as conn:
    f = conn.execute(text("SELECT id FROM files WHERE original_name='large_knowledge_base.txt'")).fetchone()
    if f:
        fid = str(f[0])
        conn.execute(text("DELETE FROM document_chunks WHERE file_id='" + fid + "'"))
        conn.execute(text("DELETE FROM files WHERE id='" + fid + "'"))
        conn.commit()
        print('Deleted file from PostgreSQL:', fid)
    else:
        print('File not found in DB')
