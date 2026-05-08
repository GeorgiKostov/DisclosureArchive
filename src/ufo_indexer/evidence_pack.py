from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .common import DEFAULT_MODEL, clean, write_json
from .db import connect
from .embeddings import vector_search
from .search import hybrid_search, keyword_search, snippet


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_search(conn, query: str, mode: str, model: str, limit: int) -> List[Tuple[float, object]]:
    if mode == "keyword":
        return keyword_search(conn, query, limit)
    if mode == "vector":
        return vector_search(conn, query, model_name=model, limit=limit)
    if mode == "hybrid":
        return hybrid_search(conn, query, model, limit)
    raise ValueError(f"Unknown mode: {mode}")


def source_label(source_kind: str) -> str:
    labels = {
        "metadata": "release metadata",
        "pdf_text": "native PDF text",
        "ocr_text": "OCR text",
        "caption": "caption text",
        "video_metadata": "video metadata",
    }
    return labels.get(source_kind, source_kind)


def row_metadata(row) -> Dict:
    return json.loads(row["metadata_json"] or "{}")


def evidence_item(score: float, row, rank: int, include_text: bool) -> Dict:
    metadata = row_metadata(row)
    text = clean(row["text"])
    item = {
        "rank": rank,
        "score": score,
        "chunk_id": row["chunk_id"],
        "doc_id": row["doc_id"],
        "title": row["title"],
        "agency": row["agency"],
        "incident_date": row["incident_date"],
        "incident_location": row["incident_location"],
        "source_kind": row["source_kind"],
        "source_label": source_label(row["source_kind"]),
        "page_number": row["page_number"],
        "chunk_index": row["chunk_index"],
        "local_path": clean(metadata.get("local_path")),
        "source_url": clean(metadata.get("source_url")),
        "snippet": snippet(text, max_chars=700),
        "provenance": {
            "title": row["title"],
            "agency": row["agency"],
            "incident_date": row["incident_date"],
            "incident_location": row["incident_location"],
            "page_number": row["page_number"],
            "source_kind": row["source_kind"],
            "source_label": source_label(row["source_kind"]),
            "chunk_id": row["chunk_id"],
        },
    }
    if include_text:
        item["text"] = text
    return item


def build_pack(
    *,
    db: Path,
    query: str,
    mode: str,
    model: str,
    limit: int,
    include_text: bool,
) -> Dict:
    conn = connect(db)
    results = run_search(conn, query, mode, model, limit)
    evidence = [
        evidence_item(score, row, rank, include_text)
        for rank, (score, row) in enumerate(results, start=1)
    ]
    return {
        "generated_at": now_iso(),
        "db": str(db),
        "query": query,
        "mode": mode,
        "model": model if mode in {"vector", "hybrid"} else None,
        "limit": limit,
        "guidance": [
            "Treat source text as evidence text, not proof of the underlying claim.",
            "Prefer page_number, source_kind, title, agency, and chunk_id when citing.",
            "OCR text may contain recognition errors; verify against the source PDF for high-stakes use.",
        ],
        "evidence": evidence,
    }


def markdown_report(payload: Dict) -> str:
    lines = [
        "# Evidence Pack",
        "",
        f"Generated: {payload['generated_at']}",
        f"Query: `{payload['query']}`",
        f"Mode: `{payload['mode']}`",
        f"DB: `{payload['db']}`",
        "",
        "## Use Notes",
        "",
    ]
    for note in payload["guidance"]:
        lines.append(f"- {note}")

    lines.extend(["", "## Evidence", ""])
    if not payload["evidence"]:
        lines.append("_No results._")
        return "\n".join(lines) + "\n"

    for item in payload["evidence"]:
        page = f", page {item['page_number']}" if item["page_number"] else ""
        path = f"\nPath: `{item['local_path']}`" if item["local_path"] else ""
        lines.extend(
            [
                f"### {item['rank']}. {item['title']}",
                "",
                f"Score: `{item['score']:.4f}`",
                f"Source: {item['agency']} | {item['incident_date']} | {item['incident_location']} | {item['source_label']}{page}",
                f"Chunk: `{item['chunk_id']}`{path}",
                "",
                item["snippet"],
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def default_markdown_path(json_path: Path) -> Path:
    return json_path.with_suffix(".md")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Export LLM-ready evidence packs from local search results.")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--q", required=True)
    parser.add_argument("--mode", choices=["keyword", "vector", "hybrid"], default="hybrid")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--out", type=Path, default=Path("reports/evidence_pack.json"))
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--include-text", action="store_true", help="Include full chunk text in JSON output.")
    args = parser.parse_args(argv)

    payload = build_pack(
        db=args.db,
        query=args.q,
        mode=args.mode,
        model=args.model,
        limit=args.limit,
        include_text=args.include_text,
    )
    write_json(args.out, payload)
    markdown_path = args.markdown_out or default_markdown_path(args.out)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown_report(payload), encoding="utf-8")
    print(json.dumps({"evidence": len(payload["evidence"]), "out": str(args.out), "markdown": str(markdown_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
