import hashlib
import re
from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.embeddings import Embedder
from app.providers.llm import LLM
from app.providers.vectordb.memory import MemoryVectorStore
from app.services import ProjectService

SAMPLES = Path(__file__).resolve().parent.parent / "samples"


class FakeEmbedder(Embedder):
    """Bag of words hashed into 512 dims: texts that share words end up close. No model download."""

    dim = 512

    def _embed(self, text: str) -> list[float]:
        v = np.zeros(self.dim, dtype=np.float32)
        for word in re.findall(r"[a-z]+", text.lower()):
            if len(word) > 2:
                v[int(hashlib.md5(word.encode()).hexdigest(), 16) % self.dim] += 1
        return (v / (np.linalg.norm(v) or 1)).tolist()

    def embed_documents(self, texts):
        return [self._embed(t) for t in texts]

    def embed_query(self, text):
        return self._embed(text)


class FakeLLM(LLM):
    """Replies from a queue and remembers every prompt it got."""

    def __init__(self, replies: list[str] | None = None):
        self.replies = list(replies or [])
        self.calls: list[list[dict]] = []

    def complete(self, messages):
        self.calls.append(messages)
        return self.replies.pop(0) if self.replies else "Answer [1]."


@pytest.fixture
def embedder():
    return FakeEmbedder()


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(tmp_path, monkeypatch, embedder, llm):
    monkeypatch.setattr(ProjectService, "FILES_DIR", str(tmp_path / "files"))
    # The hashing embedder scores lower than a real model, so the evidence threshold is lower too
    settings = Settings(_env_file=None, VECTOR_DB="memory", MIN_SCORE=0.1, CHUNK_SIZE=400, CHUNK_OVERLAP=50)
    app = create_app(settings, embedder=embedder, store=MemoryVectorStore(), llm=llm)
    with TestClient(app) as c:
        yield c


@pytest.fixture
def indexed(client):
    """The sports sample uploaded and indexed in project 'demo'. Returns its file_id."""
    with open(SAMPLES / "sports.pdf", "rb") as f:
        file_id = client.post("/api/document/upload/demo", files={"file": ("sports.pdf", f, "application/pdf")}).json()[
            "file_id"
        ]
    response = client.post("/api/document/index/demo", json={"file_id": file_id})
    assert response.status_code == 200, response.text
    return file_id
