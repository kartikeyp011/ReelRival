from pydantic import BaseModel, HttpUrl
from typing import Optional
from enum import Enum


# ─── Enums ────────────────────────────────────────────

class Platform(str, Enum):
    youtube = "youtube"
    unsupported = "unsupported"


class ChunkType(str, Enum):
    summary = "summary"
    transcript = "transcript"
    HOOK = "hook"


# ─── Ingestion Schemas ────────────────────────────────

class IngestRequest(BaseModel):
    url_a: str
    url_b: str


class VideoMetadata(BaseModel):
    video_id: str
    url: str
    platform: Platform
    title: str
    channel: str
    publish_date: Optional[str] = None
    duration_seconds: Optional[int] = None
    view_count: int
    like_count: int
    comment_count: int
    engagement_rate: float          # computed locally
    transcript_available: bool = False


class TranscriptChunk(BaseModel):
    chunk_id: str                   # f"{video_id}_chunk_{index}"
    video_id: str
    video_title: str
    chunk_index: int
    chunk_type: ChunkType
    start_time: Optional[float] = None   # seconds
    end_time: Optional[float] = None     # seconds
    start_label: Optional[str] = None    # "1:23"
    end_label: Optional[str] = None      # "2:15"
    text: str
    faiss_id: Optional[int] = None       # assigned after FAISS insert


class IngestResponse(BaseModel):
    session_id: str
    video_a: VideoMetadata
    video_b: VideoMetadata
    total_chunks: int
    status: str = "ready"


# ─── Chat Schemas ─────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str


class CitationSource(BaseModel):
    video_id: str
    video_title: str
    start_label: Optional[str] = None
    end_label: Optional[str] = None
    chunk_type: ChunkType
    excerpt: str                    # first 120 chars of chunk text


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    sources: list[CitationSource]


# ─── Health Schemas ───────────────────────────────────

class ServiceHealth(BaseModel):
    embed_service: bool
    llm_service: bool
    faiss_loaded: bool


class HealthResponse(BaseModel):
    status: str
    services: ServiceHealth