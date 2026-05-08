from __future__ import annotations

import sqlite3
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from .common import DEFAULT_DIM, DEFAULT_MODEL


def pack_vector(values: Sequence[float]) -> bytes:
    arr = np.asarray(values, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.astype(np.float32).tobytes()


def unpack_vector(blob: bytes, dim: int = DEFAULT_DIM) -> np.ndarray:
    arr = np.frombuffer(blob, dtype=np.float32)
    if dim and arr.size != dim:
        return arr
    return arr


def embed_texts(texts: Sequence[str], model_name: str = DEFAULT_MODEL) -> List[np.ndarray]:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=model_name)
    vectors = list(model.embed(list(texts)))
    return [np.asarray(vector, dtype=np.float32) for vector in vectors]


def missing_embedding_chunks(
    conn: sqlite3.Connection, model_name: str = DEFAULT_MODEL, limit: int = 256
) -> List[sqlite3.Row]:
    return conn.execute(
        """
        SELECT c.chunk_id, c.text
        FROM chunks c
        LEFT JOIN embeddings e
          ON e.chunk_id = c.chunk_id AND e.model = ?
        WHERE e.chunk_id IS NULL
        ORDER BY c.rowid
        LIMIT ?
        """,
        (model_name, limit),
    ).fetchall()


def vector_search(
    conn: sqlite3.Connection, query: str, model_name: str = DEFAULT_MODEL, limit: int = 10
) -> List[Tuple[float, sqlite3.Row]]:
    query_vec = embed_texts([query], model_name=model_name)[0]
    query_blob = pack_vector(query_vec)
    q = unpack_vector(query_blob)
    rows = conn.execute(
        """
        SELECT c.*, e.vector, e.dim
        FROM embeddings e
        JOIN chunks c ON c.chunk_id = e.chunk_id
        WHERE e.model = ?
        """,
        (model_name,),
    ).fetchall()
    scored: List[Tuple[float, sqlite3.Row]] = []
    for row in rows:
        vec = unpack_vector(row["vector"], row["dim"])
        if vec.size != q.size:
            continue
        scored.append((float(np.dot(q, vec)), row))
    scored.sort(key=lambda item: item[0], reverse=True)
    return scored[:limit]
