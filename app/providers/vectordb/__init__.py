from app.config import Settings
from app.providers.vectordb.base import VectorStore


def create_vector_store(settings: Settings) -> VectorStore:
    """Pick the vector database from VECTOR_DB. Each backend is imported only when it's used,
    so you only install the client you need."""
    if settings.VECTOR_DB == "memory":
        from app.providers.vectordb.memory import MemoryVectorStore

        return MemoryVectorStore()
    if settings.VECTOR_DB == "chroma":
        from app.providers.vectordb.chroma import ChromaVectorStore

        return ChromaVectorStore(settings.CHROMA_PATH)
    if settings.VECTOR_DB == "qdrant":
        from app.providers.vectordb.qdrant import QdrantVectorStore

        return QdrantVectorStore(settings.QDRANT_URL, settings.QDRANT_API_KEY)
    if settings.VECTOR_DB == "pgvector":
        from app.providers.vectordb.pgvector import PgVectorStore

        return PgVectorStore(settings.PGVECTOR_URL)
    raise ValueError(f"Unknown VECTOR_DB: {settings.VECTOR_DB}")


__all__ = ["VectorStore", "create_vector_store"]
