from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.dependencies import RAG
from app.providers.embeddings import Embedder, create_embedder
from app.providers.llm import LLM, create_llm
from app.providers.vectordb import VectorStore, create_vector_store
from app.routes import document, health, query


def create_app(
    settings: Settings | None = None,
    embedder: Embedder | None = None,
    store: VectorStore | None = None,
    llm: LLM | None = None,
) -> FastAPI:
    """Providers come from the settings, unless passed in (the tests pass fakes)."""

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        s = settings or get_settings()
        vector_store = store or create_vector_store(s)
        app.state.rag = RAG.build(s, embedder or create_embedder(s), vector_store, llm or create_llm(s))
        yield
        vector_store.close()

    app = FastAPI(title="rag-structure", lifespan=lifespan)
    app.include_router(health.health_router)
    app.include_router(document.document_router)
    app.include_router(query.query_router)
    return app


app = create_app()
