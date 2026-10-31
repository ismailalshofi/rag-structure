from openai import OpenAI

from app.providers.embeddings.base import Embedder

BATCH_SIZE = 128


class OpenAIEmbedder(Embedder):
    """Any OpenAI-compatible embeddings API (OpenAI, Azure, Ollama, vLLM...)."""

    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.dim = len(self.embed_query("probe"))

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for i in range(0, len(texts), BATCH_SIZE):
            response = self.client.embeddings.create(model=self.model, input=texts[i : i + BATCH_SIZE])
            vectors += [item.embedding for item in response.data]
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self.client.embeddings.create(model=self.model, input=[text]).data[0].embedding
