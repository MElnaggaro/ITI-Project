"""Re-process large_knowledge_base_updated.txt with new 200-word chunking."""
import uuid
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from services.chunking_service import ChunkingService
from services.embedding_service import EmbeddingService
from services.vector_store_service import VectorStoreService

settings = get_settings()
engine = create_engine(settings.application_database_url)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

FILE_ID = '06d34858-8fb1-4148-b251-e55875c40731'
KB_ID = '64720854-afa1-48b4-b14d-f3f71f6da003'

# 1. Get tenant_id
tenant_row = db.execute(text("SELECT tenant_id FROM files WHERE id=:fid"), {"fid": FILE_ID}).fetchone()
TENANT_ID = str(tenant_row[0])
print(f"Tenant: {TENANT_ID}, KB: {KB_ID}, File: {FILE_ID}")

# 2. Get old chunks content to reconstruct original text
old_chunks = db.execute(
    text("SELECT content FROM document_chunks WHERE file_id=:fid ORDER BY chunk_index"),
    {"fid": FILE_ID}
).fetchall()

if not old_chunks:
    # Chunks were already deleted in previous run, read from file directly
    with open('/app/large_knowledge_base_updated.txt', 'r') as f:
        full_text = f.read()
else:
    full_text = " ".join([r[0] for r in old_chunks])

print(f"Text: {len(full_text.split())} words")

# 3. Delete old chunks from PostgreSQL
db.execute(text("DELETE FROM document_chunks WHERE file_id=:fid"), {"fid": FILE_ID})
db.commit()
print("Old chunks deleted from PostgreSQL")

# 4. Delete old vectors from Qdrant
vs = VectorStoreService()
vs.delete_file_vectors(uuid.UUID(TENANT_ID), uuid.UUID(FILE_ID))
print("Old vectors deleted from Qdrant")

# 5. Re-chunk with new settings (200 words, 30 overlap)
chunker = ChunkingService()
new_chunks_data = chunker.split_text_into_chunks(full_text)
print(f"New chunks created: {len(new_chunks_data)}")

# 6. Save new chunks to PostgreSQL using raw SQL (to include knowledge_base_id)
from models.document_chunk import DocumentChunk

new_chunk_objects = []
for cd in new_chunks_data:
    chunk_id = uuid.uuid4()
    db.execute(text("""
        INSERT INTO document_chunks (id, tenant_id, knowledge_base_id, file_id, chunk_index, content, content_hash, page_number, token_count, metadata)
        VALUES (:id, :tenant_id, :kb_id, :file_id, :chunk_index, :content, :content_hash, :page_number, :token_count, '{}')
    """), {
        "id": str(chunk_id),
        "tenant_id": TENANT_ID,
        "kb_id": KB_ID,
        "file_id": FILE_ID,
        "chunk_index": cd["chunk_index"],
        "content": cd["content"],
        "content_hash": cd["content_hash"],
        "page_number": cd.get("page_number", 1),
        "token_count": cd["token_count"],
    })
    
    # Create a simple object for the vector store
    class ChunkRef:
        pass
    ref = ChunkRef()
    ref.id = chunk_id
    ref.content = cd["content"]
    ref.chunk_index = cd["chunk_index"]
    new_chunk_objects.append(ref)

db.commit()
print(f"Saved {len(new_chunk_objects)} chunks to PostgreSQL")

# 7. Generate embeddings and index in Qdrant
embedder = EmbeddingService()
texts = [c.content for c in new_chunk_objects]
embeddings = [embedder.embed_text(t) for t in texts]
print(f"Generated {len(embeddings)} embeddings")

indexed = vs.upsert_chunks(
    tenant_id=uuid.UUID(TENANT_ID),
    knowledge_base_id=uuid.UUID(KB_ID),
    file_id=uuid.UUID(FILE_ID),
    chunks=new_chunk_objects,
    embeddings=embeddings,
)
print(f"Indexed {indexed} vectors in Qdrant")

# 8. Verify
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
client = QdrantClient(url=settings.qdrant_url, check_compatibility=False)
count_filter = Filter(must=[FieldCondition(key='file_id', match=MatchValue(value=FILE_ID))])
final_count = client.count(collection_name='document_chunks', count_filter=count_filter).count
print(f"\nVerification: {final_count} vectors in Qdrant for this file")

# 9. Quick search test
query_vec = embedder.embed_text("TechNova core values")
q_filter = Filter(must=[
    FieldCondition(key='tenant_id', match=MatchValue(value=TENANT_ID)),
    FieldCondition(key='knowledge_base_id', match=MatchValue(value=KB_ID)),
])
if hasattr(client, 'query_points'):
    res_obj = client.query_points(collection_name='document_chunks', query=query_vec, query_filter=q_filter, limit=5)
    results = res_obj.points
else:
    results = client.search(collection_name='document_chunks', query_vector=query_vec, query_filter=q_filter, limit=5)

print("\nTop 5 search results for 'TechNova core values':")
for i, sr in enumerate(results):
    print(f"  #{i+1} Score: {sr.score:.4f} | file_id: {sr.payload.get('file_id','?')[:12]}... | content: {sr.payload.get('content','')[:120]}")

db.close()
print("\nDone!")
