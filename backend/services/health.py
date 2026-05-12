import logging
import httpx
from backend.config import kaggle_upstream_headers, settings
from backend.retrieval.faiss_store import faiss_store

logger = logging.getLogger(__name__)


async def check_services() -> dict:
    """
    Check health of both Kaggle GPU services and local FAISS.
    Returns a dict with status of each component.
    """
    headers = kaggle_upstream_headers()

    embed_ok = False
    llm_ok = False

    async with httpx.AsyncClient(timeout=10.0) as client:
        # Check embedding service
        try:
            r = await client.get(
                f"{settings.embed_service_url}/health",
                headers=headers
            )
            embed_ok = r.status_code == 200
        except Exception as e:
            logger.warning(f"Embed service health check failed: {e}")

        # Check LLM service
        try:
            r = await client.get(
                f"{settings.llm_service_url}/health",
                headers=headers
            )
            llm_ok = r.status_code == 200
        except Exception as e:
            logger.warning(f"LLM service health check failed: {e}")

    return {
        "embed_service": embed_ok,
        "llm_service": llm_ok,
        "faiss_loaded": faiss_store.total_vectors > 0,
        "total_vectors": faiss_store.total_vectors,
    }