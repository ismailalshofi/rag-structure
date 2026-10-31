from app.config import Settings
from app.providers.embeddings.base import Embedder


def create_embedder(settings: Settings) -> Embedder:
    if settings.EMBEDDING_PROVIDER == "fastembed":
        from app.providers.embeddings.fastembed import FastEmbedEmbedder

        return FastEmbedEmbedder(settings.EMBEDDING_MODEL)
    if settings.EMBEDDING_PROVIDER == "openai":
        from app.providers.embeddings.openai import OpenAIEmbedder

        return OpenAIEmbedder(settings.EMBEDDING_MODEL, settings.EMBEDDING_API_KEY, settings.EMBEDDING_BASE_URL)
    raise ValueError(f"Unknown EMBEDDING_PROVIDER: {settings.EMBEDDING_PROVIDER}")


__all__ = ["Embedder", "create_embedder"]
