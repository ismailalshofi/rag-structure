from app.models import SearchHit
from app.providers.embeddings import Embedder
from app.providers.vectordb import VectorStore
from app.services.project import ProjectService


class RetrievalService:
    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    def search(self, project_id: str, query: str, top_k: int, file_id: str | None = None) -> list[SearchHit]:
        vector = self.embedder.embed_query(query)
        return self.store.search(ProjectService.collection_name(project_id), vector, top_k, file_id)
