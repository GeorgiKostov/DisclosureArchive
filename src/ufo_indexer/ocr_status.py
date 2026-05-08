from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .common import clean, read_json, write_json
from .ocr import portable_source_key, read_portable_cache


LOW_AVG_CHARS_PER_PAGE = 40


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_classification(path: Optional[Path]) -> Dict[str, Dict]:
    if not path:
        return {}
    payload = read_json(path, {})
    return {
        item["relative_path"]: item
        for item in payload.get("pdfs", [])
        if item.get("relative_path")
    }


def candidate_pdfs(source_root: Path, classification: Dict[str, Dict]) -> List[Path]:
    if classification:
        return [
            source_root / relative_path
            for relative_path in sorted(classification)
            if (source_root / relative_path).exists()
        ]
    documents = source_root / "documents"
    if not documents.exists():
        return []
    return sorted(documents.glob("*.pdf"))


def expected_ocr_pages(item: Optional[Dict]) -> int:
    if not item:
        return 0
    action = item.get("recommended_action")
    if action == "none":
        return 0
    if action == "ocr_all_pages":
        return int(item.get("page_count") or 0)
    return int(item.get("text_poor_page_count") or 0)


def page_numbers(pages: List[Dict]) -> List[int]:
    return sorted(int(page.get("page") or 0) for page in pages if page.get("page"))


def status_for_pdf(source_root: Path, derived_root: Path, pdf_path: Path, classification: Dict[str, Dict]) -> Dict:
    relative_path = portable_source_key(pdf_path, source_root)
    class_item = classification.get(relative_path)
    cache_path, cache = read_portable_cache(
        derived_root=derived_root,
        pdf_path=pdf_path,
        source_root=source_root,
        ocr=True,
    )
    pages = cache.get("pages", []) if cache else []
    expected_pages = expected_ocr_pages(class_item)
    ocr_pages = len(pages)
    text_lengths = [len(clean(page.get("text"))) for page in pages]
    text_chars = sum(text_lengths)
    zero_text_pages = [
        int(page.get("page") or 0)
        for page, length in zip(pages, text_lengths)
        if page.get("page") and length == 0 and not page.get("error")
    ]
    error_pages = [
        {
            "page": int(page.get("page") or 0),
            "error": clean(page.get("error")),
        }
        for page in pages
        if page.get("error")
    ]
    avg_chars = round(text_chars / ocr_pages, 1) if ocr_pages else 0.0
    expected_numbers = set(range(1, expected_pages + 1)) if (class_item and class_item.get("recommended_action") == "ocr_all_pages") else set()
    if class_item and class_item.get("recommended_action") != "ocr_all_pages":
        # For mixed/low-text PDFs, classification currently records the count
        # but not exact page numbers. Treat matching counts as complete.
        expected_numbers = set()
    seen_numbers = set(page_numbers(pages))
    missing_pages = sorted(expected_numbers - seen_numbers)

    if expected_pages == 0:
        status = "not_needed"
    elif not cache:
        status = "missing"
    elif error_pages or missing_pages or ocr_pages < expected_pages:
        status = "partial"
    else:
        status = "complete"

    review_reasons: List[str] = []
    if status in {"missing", "partial"}:
        review_reasons.append(status)
    if error_pages:
        review_reasons.append("ocr_errors")
    if zero_text_pages:
        review_reasons.append("zero_text_pages")
    if ocr_pages and avg_chars < LOW_AVG_CHARS_PER_PAGE:
        review_reasons.append("low_avg_chars")

    return {
        "relative_path": relative_path,
        "local_path": str(pdf_path),
        "classification": class_item.get("classification") if class_item else None,
        "recommended_action": class_item.get("recommended_action") if class_item else None,
        "status": status,
        "page_count": int(class_item.get("page_count") or 0) if class_item else None,
        "expected_ocr_pages": expected_pages,
        "ocr_pages": ocr_pages,
        "ocr_text_chars": text_chars,
        "avg_ocr_chars_per_page": avg_chars,
        "zero_text_page_count": len(zero_text_pages),
        "zero_text_pages": zero_text_pages[:50],
        "error_page_count": len(error_pages),
        "error_pages": error_pages[:20],
        "missing_pages": missing_pages[:50],
        "cache_path": str(cache_path) if cache_path else None,
        "cache_seconds": cache.get("seconds") if cache else None,
        "needs_review": bool(review_reasons),
        "review_reasons": review_reasons,
    }


def build_report(source_root: Path, derived_root: Path, classification_path: Optional[Path]) -> Dict:
    classification = load_classification(classification_path)
    pdfs = [
        status_for_pdf(source_root, derived_root, pdf_path, classification)
        for pdf_path in candidate_pdfs(source_root, classification)
    ]
    status_counts = Counter(item["status"] for item in pdfs)
    review_counts = Counter(reason for item in pdfs for reason in item["review_reasons"])
    return {
        "generated_at": now_iso(),
        "source_root": str(source_root),
        "derived_root": str(derived_root),
        "classification_report": str(classification_path) if classification_path else None,
        "thresholds": {"low_avg_chars_per_page": LOW_AVG_CHARS_PER_PAGE},
        "totals": {
            "pdfs": len(pdfs),
            "by_status": dict(sorted(status_counts.items())),
            "needs_review": sum(1 for item in pdfs if item["needs_review"]),
            "by_review_reason": dict(sorted(review_counts.items())),
            "expected_ocr_pages": sum(item["expected_ocr_pages"] for item in pdfs),
            "ocr_pages": sum(item["ocr_pages"] for item in pdfs),
            "ocr_text_chars": sum(item["ocr_text_chars"] for item in pdfs),
            "zero_text_pages": sum(item["zero_text_page_count"] for item in pdfs),
            "error_pages": sum(item["error_page_count"] for item in pdfs),
        },
        "pdfs": pdfs,
    }


def markdown_report(payload: Dict) -> str:
    totals = payload["totals"]
    lines = [
        "# OCR Status Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"Source root: `{payload['source_root']}`",
        f"PDFs: {totals['pdfs']}",
        "",
        "## Summary",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Expected OCR pages | {totals['expected_ocr_pages']} |",
        f"| Cached OCR pages | {totals['ocr_pages']} |",
        f"| OCR text chars | {totals['ocr_text_chars']} |",
        f"| PDFs needing review | {totals['needs_review']} |",
        f"| Zero-text OCR pages | {totals['zero_text_pages']} |",
        f"| OCR error pages | {totals['error_pages']} |",
        "",
        "## Status Counts",
        "",
        "| Status | PDFs |",
        "| --- | ---: |",
    ]
    for status, count in totals["by_status"].items():
        lines.append(f"| `{status}` | {count} |")

    review_items = sorted(
        [item for item in payload["pdfs"] if item["needs_review"]],
        key=lambda item: (
            item["status"] == "complete",
            -item["error_page_count"],
            -item["zero_text_page_count"],
            item["avg_ocr_chars_per_page"],
            item["relative_path"],
        ),
    )
    lines.extend(["", "## Review Candidates", ""])
    if not review_items:
        lines.append("_No OCR review candidates found._")
    else:
        lines.extend(
            [
                "| PDF | Class | Status | OCR pages | Chars | Avg/page | Zero-text | Errors | Reasons |",
                "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for item in review_items:
            reasons = ", ".join(f"`{reason}`" for reason in item["review_reasons"])
            lines.append(
                "| `{relative_path}` | `{classification}` | `{status}` | {ocr_pages}/{expected_ocr_pages} | "
                "{ocr_text_chars} | {avg_ocr_chars_per_page} | {zero_text_page_count} | {error_page_count} | "
                "{reasons} |".format(**{**item, "reasons": reasons})
            )

    return "\n".join(lines) + "\n"


def default_markdown_path(json_path: Path) -> Path:
    return json_path.with_suffix(".md")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize OCR cache coverage and review candidates.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--derived-root", type=Path, default=Path("derived"))
    parser.add_argument("--classification", type=Path, default=Path("reports/pdf_classification.json"))
    parser.add_argument("--out", type=Path, default=Path("reports/ocr_status.json"))
    parser.add_argument("--markdown-out", type=Path)
    args = parser.parse_args(argv)

    source_root = args.source_root.expanduser().resolve()
    derived_root = args.derived_root
    if not derived_root.is_absolute():
        derived_root = Path.cwd() / derived_root
    classification = args.classification if args.classification and args.classification.exists() else None

    report = build_report(source_root, derived_root, classification)
    write_json(args.out, report)
    markdown_path = args.markdown_out or default_markdown_path(args.out)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown_report(report), encoding="utf-8")
    print(json.dumps(report["totals"], indent=2))
    print(f"Wrote {args.out}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
