import numpy as np
from backend.ingestion.youtube import fetch_video_data, fetch_transcript
from backend.ingestion.chunker import build_all_chunks
from backend.retrieval.faiss_store import faiss_store
from backend.retrieval.metadata_store import metadata_store
from backend.retrieval.retriever import retrieve, format_chunks_for_prompt

# ── Ingest ──────────────────────────────────────────
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print("=== INGESTION ===")
meta = fetch_video_data(url)
print(f"Video: {meta.title} | Engagement: {meta.engagement_rate}%")

segments = fetch_transcript(meta.video_id)
print(f"Transcript segments: {len(segments) if segments else 0}")

chunks = build_all_chunks(meta, segments)
print(f"Chunks built: {len(chunks)}")

# ── Fake embeddings (1024-dim random unit vectors) ──
print("\n=== FAISS STORE ===")
dim = 1024
fake_embeddings = [
    (np.random.randn(dim) / np.linalg.norm(np.random.randn(dim))).tolist()
    for _ in chunks
]

faiss_ids = faiss_store.add(fake_embeddings)
metadata_store.add_chunks(chunks, faiss_ids)

faiss_store.save()
metadata_store.save()

print(f"Vectors in FAISS: {faiss_store.total_vectors}")
print(f"Chunks in metadata store: {metadata_store.total_chunks}")
print(f"Videos indexed: {metadata_store.get_video_ids_in_store()}")

# ── Fake retrieval ──────────────────────────────────
print("\n=== RETRIEVAL ===")
fake_query = (np.random.randn(dim) / np.linalg.norm(np.random.randn(dim))).tolist()
results = retrieve(fake_query, k=3)

print(f"Retrieved {len(results)} chunks:")
for r in results:
    print(f"  [{r['chunk_type']}] {r['chunk_id']} | score={r['score']:.4f} | {r['text'][:80]}...")

print("\n=== PROMPT EVIDENCE BLOCK ===")
print(format_chunks_for_prompt(results))