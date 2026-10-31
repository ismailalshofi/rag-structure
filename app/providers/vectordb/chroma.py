import chromadb

from app.models import Chunk, SearchHit
from app.providers.vectordb.base import VectorStore


class ChromaVectorStore(VectorStore):
    """Chroma, embedded and saved to a folder. No server to run."""

    def __init__(self, path: str | None = None):
        self.client = chromadb.PersistentClient(path=path) if path else chromadb.EphemeralClient()

    def _collection(self, name: str):
        return self.client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})

    def ensure_collection(self, name: str, dim: int) -> None:
        self._collection(name)

    def upsert(self, name: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if not chunks:
            return
        self._collection(name).upsert(
            ids=[c.id for c in chunks],
            embeddings=vectors,
            documents=[c.text for c in chunks],
            # Chroma metadata can't hold None
            metadatas=[{k: v for k, v in c.payload().items() if k != "text" and v is not None} for c in chunks],
        )

    def search(self, name: str, vector: list[float], top_k: int, file_id: str | None = None) -> list[SearchHit]:
        collection = self._collection(name)
        if collection.count() == 0:
            return []
        result = collection.query(
            query_embeddings=[vector],
            n_results=min(top_k, collection.count()),
            where={"file_id": file_id} if file_id else None,
        )
        hits = []
        for text, meta, distance in zip(
            result["documents"][0], result["metadatas"][0], result["distances"][0], strict=True
        ):
            # Chroma returns cosine distance; turn it back into similarity
            hits.append(SearchHit(Chunk.from_payload({"text": text, **meta}), 1.0 - float(distance)))
        return hits

    def delete_file(self, name: str, file_id: str) -> None:
        self._collection(name).delete(where={"file_id": file_id})

    def count(self, name: str) -> int:
        return self._collection(name).count()

    def drop_collection(self, name: str) -> None:
        try:
            self.client.delete_collection(name)
        except Exception:
            pass
