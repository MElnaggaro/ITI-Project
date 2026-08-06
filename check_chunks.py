from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from services.embedding_service import EmbeddingService

client = QdrantClient(url='http://qdrant:6333', check_compatibility=False)
embedder = EmbeddingService()

tenant_id = '8d93d4f8-997e-4c49-b8cb-c8d55ee2defe'
kb_id = '64720854-afa1-48b4-b14d-f3f71f6da003'

query_vec = embedder.embed_text("TechNova core values")

q_filter = Filter(must=[
    FieldCondition(key='tenant_id', match=MatchValue(value=tenant_id)),
    FieldCondition(key='knowledge_base_id', match=MatchValue(value=kb_id)),
])

if hasattr(client, 'query_points'):
    res_obj = client.query_points(
        collection_name='document_chunks',
        query=query_vec,
        query_filter=q_filter,
        limit=142,  # Get ALL results
    )
    search_result = res_obj.points
else:
    search_result = client.search(
        collection_name='document_chunks',
        query_vector=query_vec,
        query_filter=q_filter,
        limit=142,
    )

print("Total search results:", len(search_result))

# Find where the actual correct file appears
correct_file_id = '06d34858-8fb1-4148-b251-e55875c40731'
for i, sr in enumerate(search_result):
    fid = sr.payload.get('file_id', '?')
    if fid == correct_file_id:
        print(f"\n*** CORRECT FILE (large_knowledge_base_updated.txt) found at position {i+1} ***")
        print(f"  Score: {sr.score}")
        print(f"  Content preview: {sr.payload.get('content','')[:200]}")

# Show orphan file IDs (in Qdrant but not in files table)
print("\n=== Orphan file_ids in Qdrant (old deleted files still taking up space) ===")
orphan_ids = set()
for sr in search_result:
    fid = sr.payload.get('file_id', '?')
    if fid in ['f5f6b93e-1e51-44ba-b2b6-5ec7de3e56f5', '5dc8fd5d-6230-47fb-afda-d076dee35caf']:
        orphan_ids.add(fid)
print(f"Orphan vectors found: {len([sr for sr in search_result if sr.payload.get('file_id','?') in orphan_ids])} out of {len(search_result)} total")

# Count per file_id in results
file_counts = {}
for sr in search_result:
    fid = sr.payload.get('file_id', '?')[:12]
    file_counts[fid] = file_counts.get(fid, 0) + 1
print("\nVector distribution in Qdrant by file:")
for fid, cnt in sorted(file_counts.items(), key=lambda x: -x[1]):
    print(f"  {fid}... | {cnt} vectors")
