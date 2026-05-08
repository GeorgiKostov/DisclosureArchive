from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .common import DEFAULT_MODEL, clean
from .db import connect
from .embeddings import vector_search


def snippet(text: str, max_chars: int = 420) -> str:
    text = clean(text)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1].rstrip() + "..."


def keyword_search(conn, query: str, limit: int) -> List[Tuple[float, object]]:
    rows = conn.execute(
        """
        SELECT c.*, bm25(chunks_fts) AS score
        FROM chunks_fts
        JOIN chunks c ON c.chunk_id = chunks_fts.chunk_id
        WHERE chunks_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()
    return [(1.0 / (1.0 + abs(float(row["score"]))), row) for row in rows]


def hybrid_search(conn, query: str, model: str, limit: int) -> List[Tuple[float, object]]:
    combined: Dict[str, Tuple[float, object]] = {}
    for rank, (score, row) in enumerate(keyword_search(conn, query, limit * 3), start=1):
        combined[row["chunk_id"]] = (combined.get(row["chunk_id"], (0.0, row))[0] + 1.0 / rank, row)
    for rank, (score, row) in enumerate(vector_search(conn, query, model_name=model, limit=limit * 3), start=1):
        combined[row["chunk_id"]] = (
            combined.get(row["chunk_id"], (0.0, row))[0] + score + 0.25 / rank,
            row,
        )
    return sorted(combined.values(), key=lambda item: item[0], reverse=True)[:limit]


def format_result(score: float, row, index: int) -> str:
    metadata = json.loads(row["metadata_json"] or "{}")
    page = f", page {row['page_number']}" if row["page_number"] else ""
    path = metadata.get("local_path", "")
    return "\n".join(
        [
            f"{index}. score={score:.4f} | {row['title']} | {row['agency']} | {row['incident_date']} | {row['incident_location']} | {row['source_kind']}{page}",
            f"   chunk_id: {row['chunk_id']}",
            f"   path: {path}",
            f"   {snippet(row['text'])}",
        ]
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Search the local UFO release index.")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--q", required=True)
    parser.add_argument("--mode", choices=["keyword", "vector", "hybrid"], default="keyword")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    conn = connect(args.db)
    if args.mode == "keyword":
        results = keyword_search(conn, args.q, args.limit)
    elif args.mode == "vector":
        results = vector_search(conn, args.q, model_name=args.model, limit=args.limit)
    else:
        results = hybrid_search(conn, args.q, args.model, args.limit)

    if args.json:
        payload = []
        for score, row in results:
            payload.append(
                {
                    "score": score,
                    "chunk_id": row["chunk_id"],
                    "doc_id": row["doc_id"],
                    "title": row["title"],
                    "agency": row["agency"],
                    "incident_date": row["incident_date"],
                    "incident_location": row["incident_location"],
                    "source_kind": row["source_kind"],
                    "page_number": row["page_number"],
                    "text": row["text"],
                    "metadata": json.loads(row["metadata_json"] or "{}"),
                }
            )
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0

    for index, (score, row) in enumerate(results, start=1):
        print(format_result(score, row, index))
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
