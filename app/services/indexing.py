from app.providers.embeddings import Embedder
from app.providers.vectordb import VectorStore
from app.services.processing import ProcessingService
from app.services.project import ProjectService


class IndexingService:
    """Chunk a file, embed the chunks and store them in the project's collection."""

    def __init__(self, embedder: Embedder, store: VectorStore):
        self.embedder = embedder
        self.store = store

    def index_file(self, project_id: str, file_path: str, file_id: str, chunk_size: int, overlap: int) -> int:
        chunks = ProcessingService.process(file_path, file_id, chunk_size, overlap)
        collection = ProjectService.collection_name(project_id)
        self.store.ensure_collection(collection, self.embedder.dim)
        # Re-indexing replaces the file's old chunks, even if it now has fewer of them
        self.store.delete_file(collection, file_id)
        if chunks:
            vectors = self.embedder.embed_documents([c.text for c in chunks])
            self.store.upsert(collection, chunks, vectors)
        return len(chunks)

    def delete_file(self, project_id: str, file_id: str) -> None:
        self.store.delete_file(ProjectService.collection_name(project_id), file_id)
