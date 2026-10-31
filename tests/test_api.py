from app.services.answer import NOT_FOUND

from .conftest import SAMPLES


def test_health_reports_the_providers(client):
    body = client.get("/").json()
    assert body["vectorDb"] == "memory"


def test_upload_rejects_unsupported_files(client):
    response = client.post("/api/document/upload/demo", files={"file": ("data.exe", b"MZ", "application/octet-stream")})
    assert response.status_code == 400
    assert response.json()["message"] == "file_type_not_supported"


def test_bad_project_id_is_rejected(client):
    response = client.post("/api/query/search/..%2Fetc", json={"query": "x"})
    assert response.status_code in (400, 404)
    assert client.post("/api/query/search/a b", json={"query": "x"}).status_code == 400


def test_index_needs_an_uploaded_file(client):
    response = client.post("/api/document/index/demo", json={"file_id": "../../secret.txt"})
    assert response.status_code == 404


def test_upload_index_and_search(client, indexed):
    results = client.post(
        "/api/query/search/demo", json={"query": "What surfaces do tennis players compete on?"}
    ).json()["results"]
    assert results
    top = results[0]
    assert top["file_id"] == indexed
    assert "clay" in top["text"]
    assert top["page"] == 1


def test_reindexing_does_not_duplicate_chunks(client, indexed):
    first = client.post("/api/document/index/demo", json={"file_id": indexed}).json()["total_chunks"]
    second = client.post("/api/document/index/demo", json={"file_id": indexed}).json()["total_chunks"]
    store = client.app.state.rag.store
    assert first == second == store.count("project_demo")


def test_ask_returns_a_cited_answer(client, llm, indexed):
    llm.replies = ["Football is the most popular sport [1]."]

    body = client.post("/api/query/ask/demo", json={"question": "Which sport is the most popular in the world?"}).json()

    assert body["grounded"] is True
    assert body["cited"] == [1]
    assert "most popular sport" in body["sources"][0]["text"]
    # The sources are in the system prompt, numbered
    assert "[1]" in llm.calls[0][0]["content"]


def test_ask_says_it_does_not_know_without_calling_the_llm(client, llm, indexed):
    body = client.post("/api/query/ask/demo", json={"question": "quantum chromodynamics lattice gauge"}).json()

    assert body["answer"] == NOT_FOUND
    assert body["grounded"] is False
    assert llm.calls == []


def test_follow_up_questions_use_the_conversation(client, llm, indexed):
    llm.replies = [
        "Football is the most popular sport [1].",
        "What tournaments does football have?",  # the rewritten follow-up
        "The FIFA World Cup and the UEFA Champions League [1].",
    ]
    client.post("/api/query/ask/demo", json={"question": "Which sport is the most popular?", "session_id": "s1"})

    body = client.post(
        "/api/query/ask/demo", json={"question": "Which tournaments does it have?", "session_id": "s1"}
    ).json()

    assert body["search_query"] == "What tournaments does football have?"
    # The rewritten question found the tournaments, which "it" alone never would
    assert any("Champions League" in s["text"] for s in body["sources"])
    # The earlier turn is passed to the LLM
    assert any(m["content"] == "Which sport is the most popular?" for m in llm.calls[2])

    client.delete("/api/query/session/s1")
    assert client.app.state.rag.memory.get("s1") == []


def test_search_in_one_file_only(client, indexed):
    with open(SAMPLES / "music.pdf", "rb") as f:
        music = client.post("/api/document/upload/demo", files={"file": ("music.pdf", f, "application/pdf")}).json()[
            "file_id"
        ]
    client.post("/api/document/index/demo", json={"file_id": music})

    results = client.post("/api/query/search/demo", json={"query": "streaming platforms", "file_id": music}).json()[
        "results"
    ]

    assert results and all(r["file_id"] == music for r in results)


def test_deleted_file_is_no_longer_searchable(client, indexed):
    client.delete(f"/api/document/demo/{indexed}")
    assert client.post("/api/query/search/demo", json={"query": "tennis"}).json()["results"] == []


def test_server_starts_without_an_llm_key_and_ask_explains(tmp_path, monkeypatch, embedder):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app
    from app.providers.llm import create_llm
    from app.providers.vectordb.memory import MemoryVectorStore
    from app.services import ProjectService

    monkeypatch.setattr(ProjectService, "FILES_DIR", str(tmp_path / "files"))
    settings = Settings(_env_file=None, VECTOR_DB="memory", LLM_API_KEY="", MIN_SCORE=0.0)
    app = create_app(settings, embedder=embedder, store=MemoryVectorStore(), llm=create_llm(settings))
    with TestClient(app) as client:
        client.post("/api/document/upload/p", files={"file": ("n.txt", b"Tennis is played on clay.", "text/plain")})
        file_id = next(iter((tmp_path / "files" / "p").iterdir())).name
        client.post("/api/document/index/p", json={"file_id": file_id})

        assert client.post("/api/query/search/p", json={"query": "tennis clay"}).json()["results"]
        response = client.post("/api/query/ask/p", json={"question": "Where is tennis played?"})
        assert response.status_code == 503
        assert "LLM_API_KEY" in response.json()["detail"]
