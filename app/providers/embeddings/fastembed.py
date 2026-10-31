from fastembed import TextEmbedding

from app.providers.embeddings.base import Embedder


class FastEmbedEmbedder(Embedder):
    """Local ONNX embeddings on the CPU: no API key, no GPU. The model downloads once (~130 MB)."""

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5"):
        self.model = TextEmbedding(model)
        self.dim = len(next(iter(self.model.embed(["probe"]))))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self.model.passage_embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        return next(iter(self.model.query_embed(text))).tolist()
