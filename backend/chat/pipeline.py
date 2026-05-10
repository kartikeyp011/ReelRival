import logging
import uuid
from typing import AsyncGenerator

from backend.services.embedder_client import embed_query
from backend.retrieval.retriever import retrieve, build_citations
from backend.chat.prompt_builder import build_prompt
from backend.chat.memory import (
    format_history_for_prompt,
    add_turn,
    get_history,
)
from backend.services.llm_client import stream_chat
from backend.models import CitationSource

logger = logging.getLogger(__name__)


async def run_chat_stream(
    session_id: str,
    user_message: str,
    video_ids: list[str],
) -> AsyncGenerator[str, None]:
    """
    Full RAG chat pipeline with streaming output.

    Steps:
    1. Embed user query
    2. Retrieve relevant chunks from FAISS
    3. Build prompt with evidence + memory
    4. Stream LLM response token by token
    5. Collect full response for memory storage
    6. Save turn to memory after stream ends

    Yields: string tokens for SSE streaming to frontend
    """
    # Step 1: embed query
    logger.info(f"[{session_id}] Embedding query...")
    query_embedding = await embed_query(user_message)

    # Step 2: retrieve relevant chunks
    logger.info(f"[{session_id}] Retrieving chunks...")
    chunks = retrieve(query_embedding, video_ids=video_ids)

    # Step 3: build prompt
    history_text = format_history_for_prompt(session_id)
    prompt = build_prompt(
        user_message=user_message,
        retrieved_chunks=chunks,
        session_id=session_id,
        conversation_history=history_text,
    )
    logger.info(f"[{session_id}] Prompt built ({len(prompt)} chars). Streaming...")

    # Step 4 + 5: stream and collect
    full_response = ""
    async for token in stream_chat(prompt):
        full_response += token
        yield token

    # Step 6: save to memory after stream completes
    add_turn(session_id, user_message, full_response)
    logger.info(f"[{session_id}] Turn saved to memory.")


def get_citations_for_query(
    query_embedding: list[float],
    video_ids: list[str],
) -> list[CitationSource]:
    """
    Retrieve citations separately (used for non-streaming response metadata).
    """
    chunks = retrieve(query_embedding, video_ids=video_ids)
    return build_citations(chunks)