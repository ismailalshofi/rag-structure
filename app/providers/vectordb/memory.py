import numpy as np

from app.models import Chunk, SearchHit
from app.providers.vectordb.base import VectorStore


class MemoryVectorStore(VectorStore):
    """Brute-force cosine search in NumPy. For tests and quick local runs: nothing is saved."""

    def __init__(self):
        self._collections: dict[str, dict[str, tuple[Chunk, np.ndarray]]] = {}

    def ensure_collection(self, name: str, dim: int) -> None:
        self._collections.setdefault(name, {})

    def upsert(self, name: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        collection = self._collections.setdefault(name, {})
        for chunk, vector in zip(chunks, vectors, strict=True):
            v = np.asarray(vector, dtype=np.float32)
            collection[chunk.id] = (chunk, v / (np.linalg.norm(v) or 1.0))

    def search(self, name: str, vector: list[float], top_k: int, file_id: str | None = None) -> list[SearchHit]:
        items = [
            (chunk, v)
            for chunk, v in self._collections.get(name, {}).values()
            if file_id is None or chunk.file_id == file_id
        ]
        if not items:
            return []
        query = np.asarray(vector, dtype=np.float32)
        query /= np.linalg.norm(query) or 1.0
        scores = np.stack([v for _, v in items]) @ query
        best = np.argsort(-scores)[:top_k]
        return [SearchHit(items[i][0], float(scores[i])) for i in best]

    def delete_file(self, name: str, file_id: str) -> None:
        collection = self._collections.get(name, {})
        for key in [k for k, (chunk, _) in collection.items() if chunk.file_id == file_id]:
            del collection[key]

    def count(self, name: str) -> int:
        return len(self._collections.get(name, {}))

    def drop_collection(self, name: str) -> None:
        self._collections.pop(name, None)
