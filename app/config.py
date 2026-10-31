from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "rag-structure"
    APP_VERSION: str = "1.0"

    # Upload
    FILE_ALLOWED_TYPES: list[str] = ["text/plain", "application/pdf", "text/markdown"]
    FILE_MAX_SIZE: int = 10_485_760  # 10 MB
    FILE_CHUNK_SIZE: int = 512_000  # read uploads 512 KB at a time

    # Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # Embeddings: "fastembed" runs locally on CPU, "openai" is any OpenAI-compatible embeddings API
    EMBEDDING_PROVIDER: Literal["fastembed", "openai"] = "fastembed"
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_API_KEY: str = ""
    EMBEDDING_BASE_URL: str | None = None

    # Vector database
    VECTOR_DB: Literal["memory", "chroma", "qdrant", "pgvector"] = "chroma"
    CHROMA_PATH: str = "data/chroma"
    QDRANT_URL: str = ":memory:"
    QDRANT_API_KEY: str | None = None
    PGVECTOR_URL: str = "postgresql://postgres:postgres@localhost:5432/rag"

    # LLM: any OpenAI-compatible chat API (OpenRouter by default)
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_MODEL: str = "openai/gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1

    # Retrieval and answers
    TOP_K: int = 5
    # Below this similarity a chunk is not trusted as evidence, so the API says it doesn't know
    MIN_SCORE: float = 0.55
    MEMORY_TURNS: int = 6


@lru_cache
def get_settings() -> Settings:
    return Settings()
