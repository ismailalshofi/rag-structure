"""Every vector database must behave the same way. One set of checks, run against each backend.

pgvector runs when PGVECTOR_TEST_URL points to a Postgres with the extension (CI starts one).
"""

import os
import uuid

import pytest

from app.models import Chunk

BACKENDS = ["memory", "chroma", "qdrant", "pgvector"]


def make_store(backend):
    if backend == "memory":
        from app.providers.vectordb.memory import MemoryVectorStore

        return MemoryVectorStore()
    if backend == "chroma":
        from app.providers.vectordb.chroma import ChromaVectorStore

        return ChromaVectorStore()
    if backend == "qdrant":
        from app.providers.vectordb.qdrant import QdrantVectorStore

        return QdrantVectorStore(":memory:")
    url = os.environ.get("PGVECTOR_TEST_URL")
    if not url:
        pytest.skip("set PGVECTOR_TEST_URL to run the pgvector tests")
    from app.providers.vectordb.pgvector import PgVectorStore

    return PgVectorStore(url)


@pytest.fixture(params=BACKENDS)
def store(request):
    s = make_store(request.param)
    yield s
    s.close()


@pytest.fixture
def collection(store):
    name = f"test_{uuid.uuid4().hex[:8]}"
    store.ensure_collection(name, 3)
    yield name
    store.drop_collection(name)


def chunk(file_id, i, text="t", page=None):
    return Chunk(text=text, file_id=file_id, chunk_index=i, page=page)


def test_nearest_vector_comes_first_with_cosine_scores(store, collection):
    store.upsert(collection, [chunk("a", 0, "north"), chunk("a", 1, "east")], [[0, 1, 0], [1, 0, 0]])

    hits = store.search(collection, [0, 0.9, 0.1], top_k=2)

    assert [h.chunk.text for h in hits] == ["north", "east"]
    assert hits[0].score == pytest.approx(0.994, abs=0.01)
    assert hits[1].score == pytest.approx(0.0, abs=0.01)


def test_chunk_fields_survive_the_round_trip(store, collection):
    store.upsert(collection, [chunk("doc.pdf", 7, "hello", page=3)], [[1, 0, 0]])

    hit = store.search(collection, [1, 0, 0], top_k=1)[0]

    assert (hit.chunk.file_id, hit.chunk.chunk_index, hit.chunk.page, hit.chunk.text) == ("doc.pdf", 7, 3, "hello")


def test_search_can_be_limited_to_one_file(store, collection):
    store.upsert(collection, [chunk("a", 0), chunk("b", 0)], [[1, 0, 0], [1, 0, 0]])

    hits = store.search(collection, [1, 0, 0], top_k=5, file_id="b")

    assert [h.chunk.file_id for h in hits] == ["b"]


def test_upserting_the_same_chunk_replaces_it(store, collection):
    store.upsert(collection, [chunk("a", 0, "old")], [[1, 0, 0]])
    store.upsert(collection, [chunk("a", 0, "new")], [[1, 0, 0]])

    assert store.count(collection) == 1
    assert store.search(collection, [1, 0, 0], top_k=1)[0].chunk.text == "new"


def test_delete_file_removes_only_that_file(store, collection):
    store.upsert(collection, [chunk("a", 0), chunk("a", 1), chunk("b", 0)], [[1, 0, 0], [0, 1, 0], [0, 0, 1]])

    store.delete_file(collection, "a")

    assert store.count(collection) == 1
    assert store.search(collection, [1, 0, 0], top_k=5)[0].chunk.file_id == "b"


def test_missing_collection_is_empty_not_an_error(store):
    assert store.search("never_created", [1, 0, 0], top_k=3) == []
    assert store.count("never_created") == 0
