from qdrant_client import QdrantClient, models

from app.models import Chunk, SearchHit
from app.providers.vectordb.base import VectorStore


class QdrantVectorStore(VectorStore):
    """Qdrant. url=":memory:" runs it in-process, "http://localhost:6333" talks to a server or Qdrant Cloud."""

    def __init__(self, url: str = ":memory:", api_key: str | None = None):
        self.local = url == ":memory:"
        self.client = QdrantClient(location=":memory:") if self.local else QdrantClient(url=url, api_key=api_key)

    def ensure_collection(self, name: str, dim: int) -> None:
        if not self.client.collection_exists(name):
            self.client.create_collection(
                name, vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE)
            )
            # A Qdrant server needs an index to filter by file quickly; the in-process mode ignores it
            if not self.local:
                self.client.create_payload_index(name, "file_id", models.PayloadSchemaType.KEYWORD)

    def upsert(self, name: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if not chunks:
            return
        self.client.upsert(
            name,
            points=[
                models.PointStruct(id=c.id, vector=v, payload=c.payload()) for c, v in zip(chunks, vectors, strict=True)
            ],
        )

    def search(self, name: str, vector: list[float], top_k: int, file_id: str | None = None) -> list[SearchHit]:
        if not self.client.collection_exists(name):
            return []
        result = self.client.query_points(
            name, query=vector, limit=top_k, query_filter=self._file_filter(file_id), with_payload=True
        )
        return [SearchHit(Chunk.from_payload(p.payload), float(p.score)) for p in result.points]

    def delete_file(self, name: str, file_id: str) -> None:
        if self.client.collection_exists(name):
            self.client.delete(name, points_selector=models.FilterSelector(filter=self._file_filter(file_id)))

    def count(self, name: str) -> int:
        if not self.client.collection_exists(name):
            return 0
        return self.client.count(name, exact=True).count

    def drop_collection(self, name: str) -> None:
        if self.client.collection_exists(name):
            self.client.delete_collection(name)

    def close(self) -> None:
        self.client.close()

    @staticmethod
    def _file_filter(file_id: str | None):
        if not file_id:
            return None
        return models.Filter(must=[models.FieldCondition(key="file_id", match=models.MatchValue(value=file_id))])
