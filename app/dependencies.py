from dataclasses import dataclass

from fastapi import HTTPException, Request, status

from app.config import Settings
from app.providers.embeddings import Embedder
from app.providers.llm import LLM
from app.providers.vectordb import VectorStore
from app.services import AnswerService, ConversationMemory, IndexingService, ProjectService, RetrievalService


@dataclass
class RAG:
    """Everything the routes need, built once when the app starts."""

    settings: Settings
    store: VectorStore
    indexing: IndexingService
    retrieval: RetrievalService
    answers: AnswerService
    memory: ConversationMemory

    @classmethod
    def build(cls, settings: Settings, embedder: Embedder, store: VectorStore, llm: LLM) -> "RAG":
        memory = ConversationMemory(settings.MEMORY_TURNS)
        retrieval = RetrievalService(embedder, store)
        return cls(
            settings=settings,
            store=store,
            indexing=IndexingService(embedder, store),
            retrieval=retrieval,
            answers=AnswerService(retrieval, llm, memory, settings.MIN_SCORE),
            memory=memory,
        )


def get_rag(request: Request) -> RAG:
    return request.app.state.rag


def valid_project(project_id: str) -> str:
    if not ProjectService.is_valid_id(project_id):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "project_id may only use letters, digits, - and _")
    return project_id
