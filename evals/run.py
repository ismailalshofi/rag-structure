"""Measure retrieval (and optionally answers) on the sample documents.

    python -m evals.run                   # retrieval only: hit rate and MRR, no API key needed
    python -m evals.run --answers         # also ask the LLM and check the answers cite their sources
    python -m evals.run --vector-db qdrant --top-k 3

A question counts as a hit when one of the top-k chunks comes from the expected file and
contains every phrase in `must_contain`. Change the chunk size, the embedding model or the
vector database, run this again, and compare the numbers instead of guessing.
"""

import argparse
import json
import sys
import uuid
from pathlib import Path

from app.config import get_settings
from app.providers.embeddings import Embedder, create_embedder
from app.providers.llm import LLM, create_llm
from app.providers.vectordb import VectorStore, create_vector_store
from app.services import AnswerService, ConversationMemory, IndexingService, ProjectService, RetrievalService

ROOT = Path(__file__).resolve().parent.parent
DATASET = Path(__file__).resolve().parent / "dataset.json"
SAMPLES = ROOT / "samples"


def is_relevant(text: str, file_id: str, case: dict) -> bool:
    return file_id == case["file"] and all(p.lower() in text.lower() for p in case["must_contain"])


def run(
    embedder: Embedder,
    store: VectorStore,
    top_k: int,
    chunk_size: int,
    overlap: int,
    llm: LLM | None = None,
    min_score: float = 0.0,
) -> dict:
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    project_id = f"eval_{uuid.uuid4().hex[:8]}"
    indexing = IndexingService(embedder, store)
    retrieval = RetrievalService(embedder, store)
    for path in sorted(SAMPLES.glob("*.pdf")):
        indexing.index_file(project_id, str(path), path.name, chunk_size, overlap)

    rows = []
    try:
        for case in cases:
            hits = retrieval.search(project_id, case["question"], top_k)
            top_score = hits[0].score if hits else 0.0
            row = {"question": case["question"], "in_scope": case["file"] is not None, "top_score": top_score}
            if row["in_scope"]:
                row["rank"] = next(
                    (i for i, h in enumerate(hits, 1) if is_relevant(h.chunk.text, h.chunk.file_id, case)), None
                )
                if llm:
                    answer = AnswerService(retrieval, llm, ConversationMemory(), min_score).ask(
                        project_id, case["question"], top_k
                    )
                    row["grounded"] = answer.grounded
            rows.append(row)
    finally:
        store.drop_collection(ProjectService.collection_name(project_id))

    in_scope = [r for r in rows if r["in_scope"]]
    out_of_scope = [r for r in rows if not r["in_scope"]]
    found = [r["rank"] for r in in_scope if r["rank"]]
    report = {
        "questions": len(in_scope),
        "out_of_scope": len(out_of_scope),
        f"hit@{top_k}": len(found) / len(in_scope),
        "mrr": sum(1 / r for r in found) / len(in_scope),
        # MIN_SCORE has two jobs: let real questions through, and stop the ones the documents can't answer
        "answered": sum(r["top_score"] >= min_score for r in in_scope) / len(in_scope),
        "refused": sum(r["top_score"] < min_score for r in out_of_scope) / max(len(out_of_scope), 1),
        "rows": rows,
    }
    if llm:
        report["grounded"] = sum(r["grounded"] for r in in_scope) / len(in_scope)
    return report


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Evaluate retrieval on the sample documents.")
    parser.add_argument("--vector-db", default=settings.VECTOR_DB)
    parser.add_argument("--top-k", type=int, default=settings.TOP_K)
    parser.add_argument("--chunk-size", type=int, default=settings.CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=settings.CHUNK_OVERLAP)
    parser.add_argument("--answers", action="store_true", help="also ask the LLM (needs LLM_API_KEY)")
    parser.add_argument("--min-hit-rate", type=float, default=0.0, help="exit with an error below this hit rate")
    args = parser.parse_args()

    settings.VECTOR_DB = args.vector_db
    store = create_vector_store(settings)
    llm = create_llm(settings) if args.answers else None
    report = run(create_embedder(settings), store, args.top_k, args.chunk_size, args.overlap, llm, settings.MIN_SCORE)
    store.close()

    for row in report["rows"]:
        if row["in_scope"]:
            rank = f"#{row['rank']}" if row["rank"] else "miss"
        else:
            rank = "refused" if row["top_score"] < settings.MIN_SCORE else "LEAKED"
        grounded = "" if "grounded" not in row else ("  cited" if row["grounded"] else "  NOT cited")
        print(f"{rank:>8}  {row['top_score']:.2f}  {row['question']}{grounded}")
    hit = report[f"hit@{args.top_k}"]
    print(
        f"\n{settings.EMBEDDING_MODEL} · {args.vector_db} · chunk {args.chunk_size}/{args.overlap}"
        f" · MIN_SCORE {settings.MIN_SCORE}\n"
        f"hit@{args.top_k}: {hit:.0%}   MRR: {report['mrr']:.2f}   "
        f"in-scope answered: {report['answered']:.0%}   out-of-scope refused: {report['refused']:.0%}"
        + (f"   answers citing sources: {report['grounded']:.0%}" if "grounded" in report else "")
    )
    return 0 if hit >= args.min_hit_rate else 1


if __name__ == "__main__":
    sys.exit(main())
