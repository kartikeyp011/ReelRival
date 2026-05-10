import os
import logging
import numpy as np
import faiss
from backend.config import settings

logger = logging.getLogger(__name__)


class FAISSStore:
    """
    Manages the FAISS index for dense vector similarity search.
    Uses IndexFlatIP (inner product) with L2-normalized vectors
    which is equivalent to cosine similarity.

    Thread-safety: single-process use only (fine for local dev).
    """

    def __init__(self):
        self.dim = settings.embedding_dim
        self.index_path = settings.faiss_index_path
        self.index: faiss.IndexFlatIP = None
        self._next_id: int = 0
        self._load_or_create()

    def _load_or_create(self):
        """Load existing index from disk or create a fresh one."""
        if os.path.exists(self.index_path):
            try:
                self.index = faiss.read_index(self.index_path)
                self._next_id = self.index.ntotal
                logger.info(f"FAISS index loaded from {self.index_path} — {self._next_id} vectors")
                return
            except Exception as e:
                logger.warning(f"Failed to load FAISS index: {e}. Creating fresh index.")

        self.index = faiss.IndexFlatIP(self.dim)
        self._next_id = 0
        logger.info(f"Created fresh FAISS IndexFlatIP with dim={self.dim}")

    def add(self, embeddings: list[list[float]]) -> list[int]:
        """
        Add a batch of embeddings to the index.
        Normalizes vectors before insertion (required for cosine similarity).
        Returns list of assigned FAISS IDs.
        """
        vectors = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)

        assigned_ids = list(range(self._next_id, self._next_id + len(vectors)))
        self.index.add(vectors)
        self._next_id += len(vectors)

        logger.info(f"Added {len(vectors)} vectors. Total: {self._next_id}")
        return assigned_ids

    def search(self, query_embedding: list[float], k: int = None) -> list[tuple[int, float]]:
        """
        Search for k nearest neighbors to the query vector.
        Returns list of (faiss_id, score) sorted by score descending.
        Score is cosine similarity (0.0 to 1.0).
        """
        if k is None:
            k = settings.top_k_chunks

        if self._next_id == 0:
            logger.warning("FAISS index is empty — no vectors to search.")
            return []

        # Cap k to available vectors
        k = min(k, self._next_id)

        query = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query)

        scores, ids = self.index.search(query, k)

        results = []
        for score, idx in zip(scores[0], ids[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(score)))

        return results

    def save(self):
        """Persist index to disk."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        logger.info(f"FAISS index saved to {self.index_path} ({self._next_id} vectors)")

    def delete_by_video_id(self, video_id: str, faiss_ids: list[int]):
        """
        FAISS IndexFlatIP does not support selective deletion.
        We handle this by rebuilding the index without the target vectors.
        Called only during re-ingestion of an already-indexed video.
        """
        # This is a no-op at the FAISS level — metadata store handles
        # logical deletion by ignoring orphaned IDs during retrieval.
        # Full index rebuild is handled at the orchestration layer.
        logger.info(f"Logical delete requested for video_id={video_id} — {len(faiss_ids)} vectors marked stale.")

    @property
    def total_vectors(self) -> int:
        return self._next_id


# Singleton instance — imported everywhere
faiss_store = FAISSStore()