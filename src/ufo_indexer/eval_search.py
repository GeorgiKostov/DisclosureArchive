from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .common import DEFAULT_MODEL, clean, read_json, write_json
from .db import connect
from .search import hybrid_search, keyword_search, snippet
from .embeddings import vector_search


MODES = ["keyword", "vector", "hybrid"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def row_path(row) -> str:
    metadata = json.loads(row["metadata_json"] or "{}")
    return clean(metadata.get("local_path"))


def result_payload(score: float, row, rank: int) -> Dict:
    return {
        "rank": rank,
        "score": score,
        "chunk_id": row["chunk_id"],
        "doc_id": row["doc_id"],
        "title": row["title"],
        "agency": row["agency"],
        "incident_date": row["incident_date"],
        "incident_location": row["incident_location"],
        "source_kind": row["source_kind"],
        "page_number": row["page_number"],
        "path": row_path(row),
        "snippet": snippet(row["text"], max_chars=360),
        "text": row["text"],
    }


def contains(haystack: str, needle: str) -> bool:
    return clean(needle).casefold() in clean(haystack).casefold()


def expected_matches(result: Dict, expected: Dict) -> bool:
    title_contains = expected.get("title_contains")
    if title_contains and not contains(result["title"], title_contains):
        return False

    path_contains = expected.get("path_contains")
    if path_contains and not contains(result["path"], path_contains):
        return False

    source_kinds = expected.get("source_kinds") or []
    if source_kinds and result["source_kind"] not in source_kinds:
        return False

    text_contains = expected.get("text_contains") or []
    if text_contains and not all(contains(result["text"], value) for value in text_contains):
        return False

    return True


def best_match(results: List[Dict], expected_items: List[Dict], top_n: int) -> Optional[Dict]:
    for result in results[:top_n]:
        for expected_index, expected in enumerate(expected_items):
            if expected_matches(result, expected):
                return {
                    "rank": result["rank"],
                    "chunk_id": result["chunk_id"],
                    "title": result["title"],
                    "source_kind": result["source_kind"],
                    "expected_index": expected_index,
                }
    return None


def run_search(conn, query: str, mode: str, model: str, limit: int) -> List[Tuple[float, object]]:
    if mode == "keyword":
        return keyword_search(conn, query, limit)
    if mode == "vector":
        return vector_search(conn, query, model_name=model, limit=limit)
    if mode == "hybrid":
        return hybrid_search(conn, query, model, limit)
    raise ValueError(f"Unknown mode: {mode}")


def evaluate_query(conn, query_item: Dict, *, model: str, limit: int, pass_top_n: int) -> Dict:
    expected_items = query_item.get("expected", [])
    modes: Dict[str, Dict] = {}
    for mode in MODES:
        results = [
            result_payload(score, row, rank)
            for rank, (score, row) in enumerate(run_search(conn, query_item["query"], mode, model, limit), start=1)
        ]
        match_top3 = best_match(results, expected_items, min(3, pass_top_n))
        match_topn = best_match(results, expected_items, pass_top_n)
        modes[mode] = {
            "passed": bool(match_topn),
            "pass_top_n": pass_top_n,
            "best_rank": match_topn["rank"] if match_topn else None,
            "top3_match": match_top3,
            "best_match": match_topn,
            "results": [{k: v for k, v in result.items() if k != "text"} for result in results],
        }

    return {
        "id": query_item["id"],
        "query": query_item["query"],
        "expected": expected_items,
        "modes": modes,
    }


def summarize(evaluations: List[Dict]) -> Dict:
    by_mode = {}
    failure_highlights = []
    for mode in MODES:
        mode_results = [item["modes"][mode] for item in evaluations]
        passed = [item for item in mode_results if item["passed"]]
        ranks = [item["best_rank"] for item in passed if item["best_rank"] is not None]
        by_mode[mode] = {
            "passed": len(passed),
            "failed": len(mode_results) - len(passed),
            "average_best_rank": round(sum(ranks) / len(ranks), 2) if ranks else None,
        }

    for item in evaluations:
        if not item["modes"]["hybrid"]["passed"]:
            reason = "vector_hit_hybrid_miss" if item["modes"]["vector"]["passed"] else "hybrid_miss"
            failure_highlights.append(
                {
                    "id": item["id"],
                    "query": item["query"],
                    "reason": reason,
                }
            )

    source_kind_hits = defaultdict(int)
    for item in evaluations:
        match = item["modes"]["hybrid"].get("best_match")
        if match:
            source_kind_hits[match["source_kind"]] += 1

    return {
        "queries": len(evaluations),
        "by_mode": by_mode,
        "hybrid_best_match_source_kinds": dict(sorted(source_kind_hits.items())),
        "failure_highlights": failure_highlights,
    }


def markdown_report(payload: Dict) -> str:
    lines = [
        "# Retrieval Evaluation Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"DB: `{payload['db']}`",
        f"Model: `{payload['model']}`",
        f"Queries: {payload['summary']['queries']}",
        "",
        "## Summary By Mode",
        "",
        "| Mode | Passed | Failed | Avg best rank |",
        "| --- | ---: | ---: | ---: |",
    ]
    for mode in MODES:
        stats = payload["summary"]["by_mode"][mode]
        avg = "" if stats["average_best_rank"] is None else stats["average_best_rank"]
        lines.append(f"| `{mode}` | {stats['passed']} | {stats['failed']} | {avg} |")

    lines.extend(["", "## Hybrid Source Kinds", "", "| Source kind | Hits |", "| --- | ---: |"])
    for source_kind, count in payload["summary"]["hybrid_best_match_source_kinds"].items():
        lines.append(f"| `{source_kind}` | {count} |")

    failures = payload["summary"]["failure_highlights"]
    lines.extend(["", "## Failure Highlights", ""])
    if not failures:
        lines.append("_No hybrid failures._")
    else:
        for failure in failures:
            lines.append(f"- `{failure['id']}`: {failure['reason']} for `{failure['query']}`")

    for item in payload["evaluations"]:
        lines.extend(["", f"## {item['id']}", "", f"Query: `{item['query']}`", ""])
        lines.extend(["| Mode | Pass | Best rank | Top results |", "| --- | --- | ---: | --- |"])
        for mode in MODES:
            result = item["modes"][mode]
            top_results = []
            for hit in result["results"][:3]:
                page = f" p.{hit['page_number']}" if hit["page_number"] else ""
                top_results.append(
                    f"#{hit['rank']} {hit['title']} ({hit['source_kind']}{page})"
                )
            best_rank = result["best_rank"] or ""
            passed = "yes" if result["passed"] else "no"
            lines.append(f"| `{mode}` | {passed} | {best_rank} | {'<br>'.join(top_results)} |")

    return "\n".join(lines) + "\n"


def default_markdown_path(json_path: Path) -> Path:
    return json_path.with_suffix(".md")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate retrieval quality across keyword, vector, and hybrid search.")
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("reports/retrieval_eval.json"))
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--pass-top-n", type=int, default=5)
    args = parser.parse_args(argv)

    query_payload = read_json(args.queries, {})
    query_items = query_payload.get("queries", [])
    if not query_items:
        raise SystemExit(f"No queries found in {args.queries}")

    conn = connect(args.db)
    evaluations = [
        evaluate_query(conn, item, model=args.model, limit=args.limit, pass_top_n=args.pass_top_n)
        for item in query_items
    ]
    payload = {
        "generated_at": now_iso(),
        "db": str(args.db),
        "queries_path": str(args.queries),
        "model": args.model,
        "limit": args.limit,
        "pass_top_n": args.pass_top_n,
        "summary": summarize(evaluations),
        "evaluations": evaluations,
    }
    write_json(args.out, payload)
    markdown_path = args.markdown_out or default_markdown_path(args.out)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown_report(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, ensure_ascii=False))
    print(f"Wrote {args.out}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
