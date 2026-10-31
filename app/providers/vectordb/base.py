from abc import ABC, abstractmethod

from app.models import Chunk, SearchHit


class VectorStore(ABC):
    """What the RAG needs from a vector database, and nothing more.

    One collection per project. Scores are cosine similarity (higher is closer) for every
    backend, so MIN_SCORE means the same thing whichever database is behind it.
    """

    @abstractmethod
    def ensure_collection(self, name: str, dim: int) -> None: ...

    @abstractmethod
    def upsert(self, name: str, chunks: list[Chunk], vectors: list[list[float]]) -> None: ...

    @abstractmethod
    def search(self, name: str, vector: list[float], top_k: int, file_id: str | None = None) -> list[SearchHit]: ...

    @abstractmethod
    def delete_file(self, name: str, file_id: str) -> None: ...

    @abstractmethod
    def count(self, name: str) -> int: ...

    @abstractmethod
    def drop_collection(self, name: str) -> None: ...

    def close(self) -> None:  # noqa: B027 - optional: only stores with a connection override it
        pass
