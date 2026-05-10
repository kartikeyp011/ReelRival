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

    Args:
        query_embedding: embedded query vector from Kaggle embedding service
        k: number of results to return (defaults to settings.top_k_chunks)
        video_ids: optional filter — only return chunks from these video IDs

    Returns:
        List of chunk metadata dicts sorted by relevance score descending.
        Each dict includes all TranscriptChunk fields plus a 'score' key.
    """
    if k is None:
        k = settings.top_k_chunks

    # Fetch more than k if filtering by video_id to ensure we have enough after filter
    fetch_k = k * 3 if video_ids else k

    raw_results = faiss_store.search(query_embedding, k=fetch_k)

    if not raw_results:
        logger.warning("FAISS search returned no results.")
        return []

    enriched = []
    for faiss_id, score in raw_results:
        chunk = metadata_store.get_chunk(faiss_id)
        if not chunk:
            continue

        # Apply video_id filter if specified
        if video_ids and chunk.get("video_id") not in video_ids:
            continue

        enriched.append({**chunk, "score": score})

        if len(enriched) >= k:
            break

    logger.info(f"Retrieved {len(enriched)} chunks for query (k={k})")
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