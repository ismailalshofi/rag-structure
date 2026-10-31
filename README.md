# rag-structure

[![CI](https://github.com/ismailalshofi/rag-structure/actions/workflows/ci.yml/badge.svg)](https://github.com/ismailalshofi/rag-structure/actions/workflows/ci.yml)

A Retrieval-Augmented Generation API: upload documents, index them in the vector database you choose, search them, and get answers that cite their sources. It remembers the conversation, so follow-up questions work, and it comes with an eval so changes are measured, not guessed.

**The vector database is a setting.** The same code runs on Chroma, Qdrant, PostgreSQL with pgvector, or in memory. Switching is one line in `.env`, and every backend passes the same tests.

---

## How it works

```
Indexing   file ─▶ pages ─▶ chunks (page numbers kept) ─▶ embeddings ─▶ vector DB

Answering  question ─▶ rewrite follow-ups with the conversation ─▶ embed ─▶ search
                    ─▶ drop chunks below MIN_SCORE ─▶ LLM with numbered sources ─▶ answer + citations
```

A few decisions that matter more than the libraries:

- **No evidence, no answer.** If no chunk is similar enough (`MIN_SCORE`), the API answers "I couldn't find this in the documents" and doesn't call the LLM at all. An LLM given weak context answers from its own memory, and that's how a RAG starts making things up.
- **Citations are checked, not trusted.** The LLM must cite sources as `[1]`, `[2]`. The response lists which sources were cited and sets `grounded` only when the answer actually cites one.
- **Follow-ups are rewritten before searching.** "Which tournaments does it have?" means nothing to a vector database. With a `session_id`, the question is first rewritten into a standalone one ("What tournaments does football have?"), and that is what gets searched.
- **One score scale everywhere.** Chroma returns a distance, Qdrant a similarity, pgvector an operator result. Every store converts to cosine similarity, so `MIN_SCORE` means the same thing whichever database is behind it.
- **Re-indexing replaces.** Chunk ids are derived from the file and the chunk position, and a file's old chunks are removed first. Indexing the same file twice never duplicates it.

## Pick your vector database

| `VECTOR_DB` | Runs as | Good for |
|---|---|---|
| `chroma` (default) | embedded, saved to `CHROMA_PATH` | local work, no server to run |
| `qdrant` | in-process (`:memory:`), a server, or Qdrant Cloud | production vector search, filtering at scale |
| `pgvector` | any PostgreSQL with the `vector` extension | when you already run Postgres and want one database |
| `memory` | NumPy in the process | tests and quick experiments, nothing is saved |

Install only the client you need:

```bash
pip install -e ".[fastembed,chroma]"     # or [qdrant], [pgvector], or [all]
```

**Adding another database** (Milvus, Pinecone, Weaviate...) is one class with six methods ([`base.py`](app/providers/vectordb/base.py)), one line in the [factory](app/providers/vectordb/__init__.py), and one entry in the contract tests, which then check it behaves like the others.

## Embeddings and the LLM

| | Setting | Default |
|---|---|---|
| Embeddings | `EMBEDDING_PROVIDER=fastembed` | `BAAI/bge-small-en-v1.5`, local on the CPU, free, no API key |
| | `EMBEDDING_PROVIDER=openai` | any OpenAI-compatible embeddings API (OpenAI, Ollama, vLLM...) |
| LLM | `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` | OpenRouter, `openai/gpt-4o-mini`. Any OpenAI-compatible chat API works |

Search works without any API key. Only `/ask` needs the LLM.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -e ".[dev]"
cp .env.example .env              # add LLM_API_KEY for /ask
uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for the interactive API.

With Docker, the API runs with Chroma on its own, and Qdrant or pgvector start with a profile:

```bash
docker compose up api
docker compose --profile pgvector up      # with VECTOR_DB=pgvector in .env
```

## API

| Method | Path | |
|---|---|---|
| `POST` | `/api/document/upload/{project_id}` | Upload a `.pdf`, `.txt` or `.md` file. Returns its `file_id` |
| `POST` | `/api/document/index/{project_id}` | `{file_id, chunk_size?, overlap?}`: chunk, embed and store it |
| `DELETE` | `/api/document/{project_id}/{file_id}` | Remove a file from the index |
| `POST` | `/api/query/search/{project_id}` | `{query, top_k?, file_id?}`: the closest chunks, with page and score |
| `POST` | `/api/query/ask/{project_id}` | `{question, session_id?, top_k?, file_id?}`: an answer with cited sources |
| `DELETE` | `/api/query/session/{session_id}` | Forget a conversation |

Each project is its own collection, so documents from different projects never mix.

```json
POST /api/query/ask/demo
{"question": "Which tournaments does it have?", "session_id": "s1"}

{
  "answer": "The FIFA World Cup and the UEFA Champions League [1].",
  "search_query": "What tournaments does football have?",
  "grounded": true,
  "cited": [1],
  "sources": [{"number": 1, "file_id": "x7k2_sports.pdf", "page": 1, "score": 0.71, "text": "Football, known as soccer..."}]
}
```

## Evaluate

[`evals/`](evals) has 14 questions about the two sample documents in [`samples/`](samples), each with the file and the phrase the right chunk must contain, plus 4 questions the documents can't answer.

```bash
python -m evals.run                  # retrieval: hit rate, MRR and MIN_SCORE, no API key needed
python -m evals.run --answers        # also checks the LLM's answers cite their sources
python -m evals.run --vector-db qdrant --chunk-size 500
```

Results with `BAAI/bge-small-en-v1.5`, chunks of 800 characters, top 5:

| | Chroma | Qdrant | In memory |
|---|---|---|---|
| hit@5 | 100% | 100% | 100% |
| MRR | 0.90 | 0.90 | 0.90 |

The same numbers on every database: the backend changes where the vectors live, not what gets found.

**Chunk size** is a trade-off that the eval makes visible:

| Chunk size | hit@1 | hit@5 |
|---|---|---|
| 400 | 86% | 100% |
| 800 (default) | 86% | 100% |
| 1500 | 93% | 93% |

Bigger chunks put the right answer first more often, but a phrase cut in two at a chunk border can't be found at all.

**`MIN_SCORE` is measured too, not guessed.** With this model, questions the documents answer score **0.66–0.81**, and questions they can't answer still score **0.41–0.49**. That's why the default is 0.55: all 14 real questions get through, and all 4 unanswerable ones are refused without calling the LLM. A different embedding model has a different scale, so run the eval again when you change it.

## Tests

```bash
pytest
ruff check . && ruff format --check .
```

No API keys and no model downloads: the tests use a small hashing embedder and a scripted LLM. The [vector store tests](tests/test_vector_stores.py) run the same checks against every backend. pgvector runs when `PGVECTOR_TEST_URL` is set, and CI starts a real Postgres with pgvector for it.

## Project layout

```
app/
  main.py                    app factory: builds the providers from the settings
  config.py                  every setting, with defaults
  dependencies.py            wires the services together once at startup
  routes/                    document (upload, index, delete) and query (search, ask)
  services/
    processing.py            file -> pages -> chunks
    indexing.py              chunks -> embeddings -> vector DB
    retrieval.py             question -> closest chunks
    answer.py                retrieval + LLM + citations + follow-up rewriting
    memory.py                recent turns per session
  providers/
    vectordb/                memory, chroma, qdrant, pgvector behind one interface
    embeddings/              fastembed (local) or any OpenAI-compatible API
    llm.py                   any OpenAI-compatible chat API
evals/                       questions, expected sources, and the runner
samples/                     two test documents used by the evals and tests
tests/
```

## License

[MIT](LICENSE)
