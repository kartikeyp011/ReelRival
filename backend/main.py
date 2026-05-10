import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.config import settings
from backend.models import (
    IngestRequest,
    IngestResponse,
    ChatRequest,
    HealthResponse,
    ServiceHealth,
)
from backend.ingestion.youtube import fetch_video_data, fetch_transcript
from backend.ingestion.chunker import build_all_chunks
from backend.services.embedder_client import embed_texts
from backend.retrieval.faiss_store import faiss_store
from backend.retrieval.metadata_store import metadata_store
from backend.chat.pipeline import run_chat_stream
from backend.chat.memory import clear_session, session_exists
from backend.services.health import check_services

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Session → video_ids map (so chat knows which videos to filter by)
_session_videos: dict[str, list[str]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ReelRival backend starting...")
    logger.info(f"FAISS vectors loaded: {faiss_store.total_vectors}")
    logger.info(f"Metadata chunks loaded: {metadata_store.total_chunks}")
    yield
    logger.info("ReelRival backend shutting down.")


app = FastAPI(title="ReelRival API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Health ───────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    services = await check_services()
    status = "ok" if services["embed_service"] and services["llm_service"] else "degraded"
    return HealthResponse(
        status=status,
        services=ServiceHealth(
            embed_service=services["embed_service"],
            llm_service=services["llm_service"],
            faiss_loaded=services["faiss_loaded"],
        ),
    )


# ─── Ingestion ────────────────────────────────────────

@app.post("/ingest", response_model=IngestResponse)
async def ingest(request: IngestRequest):
    """
    Ingest two video URLs:
    1. Fetch metadata + transcripts
    2. Build chunks
    3. Embed chunks via Kaggle
    4. Store in FAISS + metadata store
    5. Return video stats + session ID
    """
    session_id = str(uuid.uuid4())

    # Fetch both videos
    try:
        meta_a = fetch_video_data(request.url_a)
        meta_b = fetch_video_data(request.url_b)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    results = []
    for meta in [meta_a, meta_b]:
        # Skip re-ingestion if already indexed
        if metadata_store.video_exists(meta.video_id):
            logger.info(f"Video {meta.video_id} already indexed — skipping.")
            results.append(meta)
            continue

        # Fetch transcript
        segments = fetch_transcript(meta.video_id)
        meta.transcript_available = segments is not None

        # Build chunks
        chunks = build_all_chunks(meta, segments)

        # Embed all chunk texts
        chunk_texts = [c.text for c in chunks]
        try:
            embeddings = await embed_texts(chunk_texts)
        except RuntimeError as e:
            raise HTTPException(status_code=503, detail=str(e))

        # Store in FAISS + metadata
        faiss_ids = faiss_store.add(embeddings)
        metadata_store.add_chunks(chunks, faiss_ids)

        results.append(meta)

    # Persist to disk
    faiss_store.save()
    metadata_store.save()

    # Map session to these two video IDs
    video_ids = [meta_a.video_id, meta_b.video_id]
    _session_videos[session_id] = video_ids

    total_chunks = sum(
        len(metadata_store.get_faiss_ids_for_video(vid))
        for vid in video_ids
    )

    return IngestResponse(
        session_id=session_id,
        video_a=results[0],
        video_b=results[1],
        total_chunks=total_chunks,
        status="ready",
    )


# ─── Chat ─────────────────────────────────────────────

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming RAG chat endpoint.
    Returns SSE-compatible text/plain stream of tokens.
    """
    if request.session_id not in _session_videos:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please ingest two videos first."
        )

    video_ids = _session_videos[request.session_id]

    async def generate():
        try:
            async for token in run_chat_stream(
                session_id=request.session_id,
                user_message=request.message,
                video_ids=video_ids,
            ):
                yield token
        except RuntimeError as e:
            yield f"\n\n[Service Error: {str(e)}]"

    return StreamingResponse(generate(), media_type="text/plain")


# ─── Session Management ───────────────────────────────

@app.delete("/session/{session_id}")
async def reset_session(session_id: str):
    """Clear conversation memory for a session."""
    clear_session(session_id)
    _session_videos.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}


@app.get("/session/{session_id}/videos")
async def get_session_videos(session_id: str):
    """Return video IDs for a session — used by frontend."""
    if session_id not in _session_videos:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "video_ids": _session_videos[session_id]}