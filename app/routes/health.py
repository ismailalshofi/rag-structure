from fastapi import APIRouter, Depends

from app.dependencies import RAG, get_rag

health_router = APIRouter(prefix="", tags=["Health"])


@health_router.get("/")
def health(rag: RAG = Depends(get_rag)):
    settings = rag.settings
    return {
        "message": "Welcome!",
        "appName": settings.APP_NAME,
        "appVersion": settings.APP_VERSION,
        "vectorDb": settings.VECTOR_DB,
        "embeddings": f"{settings.EMBEDDING_PROVIDER}:{settings.EMBEDDING_MODEL}",
        "llm": settings.LLM_MODEL,
    }
