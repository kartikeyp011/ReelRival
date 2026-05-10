import os
import json
import logging
from backend.config import settings
from backend.models import TranscriptChunk

logger = logging.getLogger(__name__)


class MetadataStore:
    """
    Parallel metadata store for FAISS vectors.
    Maps FAISS integer ID → TranscriptChunk metadata.

    Storage: JSON file on disk.
    In-memory dict for fast lookups during search.

    Key rule: faiss_id in this store always matches the
    positional index of the vector in the FAISS index.
    """

    def __init__(self):
        self.store_path = settings.metadata_store_path
        # { "faiss_id_str": chunk_dict }
        self._data: dict[str, dict] = {}
        # { "video_id": [faiss_id, ...] } for per-video operations
        self._video_index: dict[str, list[int]] = {}
        self._load()

    def _load(self):
        """Load metadata from disk if it exists."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self._data = saved.get("chunks", {})
                    self._video_index = saved.get("video_index", {})
                logger.info(f"Metadata store loaded — {len(self._data)} chunks across {len(self._video_index)} videos")
            except Exception as e:
                logger.warning(f"Failed to load metadata store: {e}. Starting fresh.")
                self._data = {}
                self._video_index = {}

    def save(self):
        """Persist metadata to disk."""
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        with open(self.store_path, "w", encoding="utf-8") as f:
            json.dump(
                {"chunks": self._data, "video_index": self._video_index},
                f,
                indent=2,
                ensure_ascii=False,
            )
        logger.info(f"Metadata store saved — {len(self._data)} chunks")

    def add_chunks(self, chunks: list[TranscriptChunk], faiss_ids: list[int]):
        """
        Store chunk metadata keyed by FAISS ID.
        Must be called immediately after FAISSStore.add() with matching IDs.
        """
        assert len(chunks) == len(faiss_ids), "Chunks and FAISS IDs must have equal length"

        for chunk, faiss_id in zip(chunks, faiss_ids):
            chunk.faiss_id = faiss_id
            self._data[str(faiss_id)] = chunk.model_dump()

            # Update video index
            vid = chunk.video_id
            if vid not in self._video_index:
                self._video_index[vid] = []
            self._video_index[vid].append(faiss_id)

        logger.info(f"Stored metadata for {len(chunks)} chunks")

    def get_chunk(self, faiss_id: int) -> dict | None:
        """Retrieve chunk metadata by FAISS ID."""
        return self._data.get(str(faiss_id))

    def get_chunks_by_ids(self, faiss_ids: list[int]) -> list[dict]:
        """Retrieve multiple chunks by FAISS IDs. Skips missing IDs."""
        results = []
        for fid in faiss_ids:
            chunk = self._data.get(str(fid))
            if chunk:
                results.append(chunk)
        return results

    def get_video_ids_in_store(self) -> list[str]:
        """Return all video IDs currently indexed."""
        return list(self._video_index.keys())

    def get_faiss_ids_for_video(self, video_id: str) -> list[int]:
        """Return all FAISS IDs belonging to a video."""
        return self._video_index.get(video_id, [])

    def remove_video(self, video_id: str):
        """
        Remove all metadata entries for a video.
        Called during re-ingestion to clean stale data.
        """
        faiss_ids = self._video_index.pop(video_id, [])
        for fid in faiss_ids:
            self._data.pop(str(fid), None)
        logger.info(f"Removed {len(faiss_ids)} chunks for video_id={video_id}")

    def video_exists(self, video_id: str) -> bool:
        return video_id in self._video_index

    @property
    def total_chunks(self) -> int:
        return len(self._data)


# Singleton instance
metadata_store = MetadataStore()