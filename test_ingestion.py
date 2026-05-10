from backend.ingestion.youtube import fetch_video_data, fetch_transcript
from backend.ingestion.chunker import build_all_chunks

# In test_ingestion.py — swap to this URL temporarily
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

print("Fetching video metadata...")
meta = fetch_video_data(url)
print(f"Title: {meta.title}")
print(f"Views: {meta.view_count:,}")
print(f"Engagement Rate: {meta.engagement_rate}%")
print(f"Transcript Available: {meta.transcript_available}")

print("\nFetching transcript...")
segments = fetch_transcript(meta.video_id)
print(f"Segments fetched: {len(segments) if segments else 0}")

print("\nBuilding chunks...")
chunks = build_all_chunks(meta, segments)
print(f"Total chunks: {len(chunks)}")
for c in chunks[:3]:
    print(f"  [{c.chunk_type}] {c.chunk_id} | {c.start_label} → {c.end_label}")
    print(f"    {c.text[:120]}...")