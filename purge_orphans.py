"""One-time cleanup: purge orphan vectors from Qdrant whose file_id no longer exists in PostgreSQL."""
from sqlalchemy import create_engine, text
from app.config import get_settings
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

settings = get_settings()
engine = create_engine(settings.application_database_url)
client = QdrantClient(url=settings.qdrant_url, check_compatibility=False)
collection = settings.qdrant_collection_name

# 1. Get all file_ids that exist in PostgreSQL
with engine.connect() as conn:
    rows = conn.execute(text("SELECT id::text FROM files")).fetchall()
    valid_file_ids = {r[0] for r in rows}

print(f"Valid file_ids in PostgreSQL: {len(valid_file_ids)}")
for fid in valid_file_ids:
    print(f"  {fid}")

# 2. Get all unique file_ids from Qdrant
results = client.scroll(collection_name=collection, limit=500, with_payload=True, with_vectors=False)
qdrant_file_ids = set()
for pt in results[0]:
    fid = pt.payload.get('file_id', '')
    if fid:
        qdrant_file_ids.add(fid)

print(f"\nUnique file_ids in Qdrant: {len(qdrant_file_ids)}")
for fid in qdrant_file_ids:
    print(f"  {fid}")

# 3. Find orphans
orphan_file_ids = qdrant_file_ids - valid_file_ids
print(f"\nOrphan file_ids to purge: {len(orphan_file_ids)}")

# 4. Delete orphan vectors from Qdrant
total_deleted = 0
for orphan_fid in orphan_file_ids:
    print(f"  Deleting vectors for orphan file_id: {orphan_fid}...")
    # Count before deletion
    count_filter = Filter(must=[FieldCondition(key='file_id', match=MatchValue(value=orphan_fid))])
    count_before = client.count(collection_name=collection, count_filter=count_filter).count
    
    # Delete
    client.delete(
        collection_name=collection,
        points_selector=count_filter,
    )
    total_deleted += count_before
    print(f"    Deleted {count_before} vectors")

print(f"\nTotal orphan vectors deleted: {total_deleted}")

# 5. Verify
info = client.get_collection(collection)
print(f"Qdrant collection now has: {info.points_count} points")
