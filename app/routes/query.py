from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import RAG, get_rag, valid_project
from app.providers.llm import LLMNotConfigured
from app.schemas import AskRequest, AskResponse, SearchRequest, SearchResponse, Source

query_router = APIRouter(prefix="/api/query", tags=["Query"])


@query_router.post("/search/{project_id}", response_model=SearchResponse)
def search(request: SearchRequest, project_id: str = Depends(valid_project), rag: RAG = Depends(get_rag)):
    hits = rag.retrieval.search(project_id, request.query, request.top_k or rag.settings.TOP_K, request.file_id)
    return SearchResponse(results=[Source.from_hit(i, h) for i, h in enumerate(hits, start=1)])


@query_router.post("/ask/{project_id}", response_model=AskResponse)
def ask(request: AskRequest, project_id: str = Depends(valid_project), rag: RAG = Depends(get_rag)):
    try:
        result = rag.answers.ask(
            project_id, request.question, request.top_k or rag.settings.TOP_K, request.session_id, request.file_id
        )
    except LLMNotConfigured as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e)) from e
    return AskResponse(
        answer=result.answer,
        search_query=result.search_query,
        grounded=result.grounded,
        cited=result.cited,
        sources=[Source.from_hit(i, h) for i, h in enumerate(result.sources, start=1)],
    )


@query_router.delete("/session/{session_id}")
def clear_session(session_id: str, rag: RAG = Depends(get_rag)):
    rag.memory.clear(session_id)
    return {"message": "session_cleared", "session_id": session_id}
