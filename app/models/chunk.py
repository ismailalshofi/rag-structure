import uuid
from dataclasses import dataclass, field


@dataclass
class Chunk:
    text: str
    file_id: str
    chunk_index: int
    page: int | None = None
    metadata: dict = field(default_factory=dict)

    @property
    def id(self) -> str:
        # Stable id: indexing the same file again replaces its chunks instead of duplicating them
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.file_id}#{self.chunk_index}"))

    def payload(self) -> dict:
        return {
            "text": self.text,
            "file_id": self.file_id,
            "chunk_index": self.chunk_index,
            "page": self.page,
            **self.metadata,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "Chunk":
        data = dict(payload)
        return cls(
            text=data.pop("text"),
            file_id=data.pop("file_id"),
            chunk_index=int(data.pop("chunk_index")),
            page=data.pop("page", None),
            metadata=data,
        )


@dataclass
class SearchHit:
    chunk: Chunk
    # Cosine similarity, higher is closer. Every vector store returns the same scale.
    score: float
