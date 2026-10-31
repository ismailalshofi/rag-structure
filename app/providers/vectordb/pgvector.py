import re

import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql
from psycopg.types.json import Jsonb

from app.models import Chunk, SearchHit
from app.providers.vectordb.base import VectorStore


class PgVectorStore(VectorStore):
    """PostgreSQL with the pgvector extension. One table per collection, with an HNSW cosine index."""

    def __init__(self, url: str):
        self.conn = psycopg.connect(url, autocommit=True)
        self.conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(self.conn)

    @staticmethod
    def _table_name(name: str) -> str:
        # Table names come from project ids, so keep them to safe characters
        return "rag_" + re.sub(r"[^a-z0-9_]", "_", name.lower())

    def _table(self, name: str) -> sql.Identifier:
        return sql.Identifier(self._table_name(name))

    def _exists(self, name: str) -> bool:
        return self.conn.execute("SELECT to_regclass(%s) IS NOT NULL", (self._table_name(name),)).fetchone()[0]

    def ensure_collection(self, name: str, dim: int) -> None:
        table = self._table_name(name)
        self.conn.execute(
            sql.SQL(
                "CREATE TABLE IF NOT EXISTS {} (id uuid PRIMARY KEY, file_id text NOT NULL, "
                "payload jsonb NOT NULL, embedding vector({}) NOT NULL)"
            ).format(sql.Identifier(table), sql.Literal(dim))
        )
        self.conn.execute(
            sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} USING hnsw (embedding vector_cosine_ops)").format(
                sql.Identifier(f"{table}_hnsw"), sql.Identifier(table)
            )
        )
        self.conn.execute(
            sql.SQL("CREATE INDEX IF NOT EXISTS {} ON {} (file_id)").format(
                sql.Identifier(f"{table}_file"), sql.Identifier(table)
            )
        )

    def upsert(self, name: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if not chunks:
            return
        query = sql.SQL(
            "INSERT INTO {} (id, file_id, payload, embedding) VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET file_id = EXCLUDED.file_id, payload = EXCLUDED.payload, "
            "embedding = EXCLUDED.embedding"
        ).format(self._table(name))
        with self.conn.cursor() as cur:
            cur.executemany(
                query,
                [
                    (c.id, c.file_id, Jsonb(c.payload()), np.asarray(v, dtype=np.float32))
                    for c, v in zip(chunks, vectors, strict=True)
                ],
            )

    def search(self, name: str, vector: list[float], top_k: int, file_id: str | None = None) -> list[SearchHit]:
        if not self._exists(name):
            return []
        where = sql.SQL("WHERE file_id = %s") if file_id else sql.SQL("")
        query = sql.SQL(
            "SELECT payload, 1 - (embedding <=> %s) AS score FROM {} {} ORDER BY embedding <=> %s LIMIT %s"
        ).format(self._table(name), where)
        v = np.asarray(vector, dtype=np.float32)
        params = (v, file_id, v, top_k) if file_id else (v, v, top_k)
        rows = self.conn.execute(query, params).fetchall()
        return [SearchHit(Chunk.from_payload(payload), float(score)) for payload, score in rows]

    def delete_file(self, name: str, file_id: str) -> None:
        if self._exists(name):
            self.conn.execute(sql.SQL("DELETE FROM {} WHERE file_id = %s").format(self._table(name)), (file_id,))

    def count(self, name: str) -> int:
        if not self._exists(name):
            return 0
        return self.conn.execute(sql.SQL("SELECT count(*) FROM {}").format(self._table(name))).fetchone()[0]

    def drop_collection(self, name: str) -> None:
        self.conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(self._table(name)))

    def close(self) -> None:
        self.conn.close()
