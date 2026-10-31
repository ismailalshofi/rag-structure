from app.providers.vectordb.memory import MemoryVectorStore
from evals.run import run

from .conftest import FakeEmbedder, FakeLLM


def test_eval_runner_reports_retrieval_and_cleans_up():
    store = MemoryVectorStore()

    report = run(FakeEmbedder(), store, top_k=5, chunk_size=800, overlap=120)

    assert report["questions"] == 14
    assert report["out_of_scope"] == 4
    # Even a bag-of-words embedder finds most answers in these two documents
    assert report["hit@5"] >= 0.7
    assert 0 < report["mrr"] <= 1
    assert store._collections == {}


def test_min_score_counts_answered_and_refused_questions():
    # The real separation is measured with a real model (see README); here, the counting at the edges
    let_all_through = run(FakeEmbedder(), MemoryVectorStore(), top_k=5, chunk_size=800, overlap=120, min_score=0.0)
    refuse_all = run(FakeEmbedder(), MemoryVectorStore(), top_k=5, chunk_size=800, overlap=120, min_score=1.01)

    assert (let_all_through["answered"], let_all_through["refused"]) == (1.0, 0.0)
    assert (refuse_all["answered"], refuse_all["refused"]) == (0.0, 1.0)


def test_eval_runner_checks_answers_when_given_an_llm():
    report = run(
        FakeEmbedder(), MemoryVectorStore(), top_k=3, chunk_size=800, overlap=120, llm=FakeLLM(), min_score=0.0
    )

    assert report["grounded"] == 1.0
