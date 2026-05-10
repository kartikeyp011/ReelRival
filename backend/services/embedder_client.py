import logging
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)

# Shared async client — reused across requests for connection pooling
_client: httpx.AsyncClient = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            headers={"x-service-token": settings.kaggle_service_token},
        )
    return _client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Send texts to Kaggle embedding service.
    Returns list of normalized float32 embedding vectors.
    Raises RuntimeError if the service is unreachable.
    """
    if not texts:
        return []

    client = get_client()

    try:
        response = await client.post(
            f"{settings.embed_service_url}/embed",
            json={"texts": texts},
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", [])

        if len(embeddings) != len(texts):
            raise ValueError(
                f"Embedding count mismatch: sent {len(texts)}, got {len(embeddings)}"
            )

        logger.info(f"Embedded {len(texts)} texts (dim={data.get('dim', '?')})")
        return embeddings

    except httpx.ConnectError:
        raise RuntimeError(
            "Embedding service is offline. Please restart your Kaggle notebook."
        )
    except httpx.TimeoutException:
        raise RuntimeError(
            "Embedding service timed out. The model may still be loading."
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"Embedding service error {e.response.status_code}: {e.response.text}")


async def embed_query(query: str) -> list[float]:
    """Embed a single query string. Returns one vector."""
    results = await embed_texts([query])
    return results[0]