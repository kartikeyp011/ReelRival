import logging
from typing import AsyncGenerator
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)


async def stream_chat(prompt: str) -> AsyncGenerator[str, None]:
    """
    Stream tokens from Kaggle LLM service (DeepSeek-R1:8b).
    Yields string tokens as they arrive.
    Raises RuntimeError if service is unreachable.
    """
    headers = {"x-service-token": settings.kaggle_service_token}

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(300.0)
        ) as client:
            async with client.stream(
                "POST",
                f"{settings.llm_service_url}/chat/stream",
                json={"prompt": prompt},
                headers=headers,
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_text():
                    if chunk:
                        yield chunk

    except httpx.ConnectError:
        raise RuntimeError(
            "LLM service is offline. Please restart your Kaggle notebook."
        )
    except httpx.TimeoutException:
        raise RuntimeError(
            "LLM service timed out. Try a shorter prompt or restart Kaggle."
        )
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"LLM service error {e.response.status_code}: {e.response.text}")


async def generate_chat(prompt: str) -> str:
    """
    Non-streaming version — collects full response.
    Used for testing only.
    """
    headers = {"x-service-token": settings.kaggle_service_token}

    async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as client:
        response = await client.post(
            f"{settings.llm_service_url}/chat",
            json={"prompt": prompt},
            headers=headers,
        )
        response.raise_for_status()
        return response.json().get("response", "")