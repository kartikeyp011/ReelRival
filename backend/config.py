from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # YouTube
    youtube_api_key: str

    # Kaggle GPU Services
    embed_service_url: str = "http://localhost:8001"
    llm_service_url: str = "http://localhost:8002"
    kaggle_service_token: str = "dev_token"

    # FAISS + Metadata
    faiss_index_path: str = "./data/faiss_index.bin"
    metadata_store_path: str = "./data/metadata_store.json"

    # Embedding
    embedding_dim: int = 1024

    # Retrieval
    top_k_chunks: int = 5

    # Chat / Memory
    max_memory_turns: int = 6

    # App
    app_env: str = "development"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()


def kaggle_upstream_headers() -> dict[str, str]:
    """Headers for outbound calls to Kaggle services (ngrok + optional token auth)."""
    return {
        "x-service-token": settings.kaggle_service_token,
        # Required for ngrok free tier when the interstitial would block httpx.
        "ngrok-skip-browser-warning": "true",
    }

# Ensure data directory exists
Path("./data").mkdir(exist_ok=True)