import logging
from backend.retrieval.faiss_store import faiss_store
from backend.retrieval.metadata_store import metadata_store
from backend.models import TranscriptChunk, CitationSource, ChunkType
from backend.config import settings

logger = logging.getLogger(__name__)

def retrieve(
    query_embedding: list[float],
    k: int = None,
    video_ids: list[str] = None,
) -> list[dict]:
    """
    Retrieve top-k relevant chunks for a query embedding.
    Returns list of **chunk dicts** (not tuples) sorted by relevance.
    """
    if k is None:
        k = settings.top_k_chunks

    fetch_k = k * 3 if video_ids else k
    raw_results = faiss_store.search(query_embedding, k=fetch_k)

    if not raw_results:
        return []

    enriched = []
    for faiss_id, score in raw_results:
        chunk_dict = metadata_store.get_chunk(faiss_id)
        if not chunk_dict:
            continue

        # Filter by video_ids if specified
        if video_ids and chunk_dict.get("video_id") not in video_ids:
            continue

        # Convert dict to include score
        chunk_with_score = {**chunk_dict, "score": float(score)}
        enriched.append(chunk_with_score)

        if len(enriched) >= k:
            break

    logger.info(f"Retrieved {len(enriched)} chunks (requested k={k})")
    return enriched

def build_citations(retrieved_chunks: list[dict]) -> list[CitationSource]:
    """
    Convert retrieved chunk dicts into CitationSource objects for the response.
    """
    citations = []
    seen_chunk_ids = set()

    for chunk in retrieved_chunks:
        chunk_id = chunk.get("chunk_id", "")
        if chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk_id)

        citations.append(CitationSource(
            video_id=chunk.get("video_id", ""),
            video_title=chunk.get("video_title", ""),
            start_label=chunk.get("start_label"),
            end_label=chunk.get("end_label"),
            chunk_type=chunk.get("chunk_type", ChunkType.transcript),
            excerpt=chunk.get("text", "")[:120],
        ))

    return citations


def format_chunks_for_prompt(retrieved_chunks: list[dict]) -> str:
    """
    Format retrieved chunks into a structured evidence block for the LLM prompt.
    Each chunk is clearly labeled with video title and timestamp.
    """
    if not retrieved_chunks:
        return "No relevant transcript evidence found."

    lines = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        video_title = chunk.get("video_title", "Unknown Video")
        video_id = chunk.get("video_id", "")
        chunk_type = chunk.get("chunk_type", "transcript")
        start = chunk.get("start_label")
        end = chunk.get("end_label")
        text = chunk.get("text", "").strip()
        score = chunk.get("score", 0.0)

        if chunk_type == "summary":
            label = f"[Source {i}] VIDEO STATS — {video_title}"
        else:
            label = f"[Source {i}] {video_title} @ {start} – {end}"

        lines.append(f"{label}\n{text}\n")

    return "\n".join(lines)