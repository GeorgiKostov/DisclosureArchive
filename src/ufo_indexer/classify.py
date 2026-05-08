from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pdfplumber
from tqdm import tqdm

from .common import clean, read_json, sha1_file, write_json
from .ocr import extracted_cache_path, portable_source_key, read_portable_cache, reusable_ocr_cache


DEFAULT_MIN_PAGE_CHARS = 80
DEFAULT_MIN_AVG_CHARS = 300
DEFAULT_MIXED_PAGE_RATIO = 0.25
DEFAULT_TEXT_NATIVE_POOR_RATIO = 0.10


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def candidate_pdfs(source_root: Path) -> List[Path]:
    documents = source_root / "documents"
    if not documents.exists():
        return []
    return sorted(documents.glob("*.pdf"))


def extract_pages_for_classification(pdf_path: Path) -> Tuple[List[Dict], Optional[str]]:
    pages: List[Dict] = []
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                    pages.append({"page": page_number, "text": text, "error": None})
                except Exception as exc:
                    pages.append({"page": page_number, "text": "", "error": repr(exc)})
        return pages, None
    except Exception as exc:
        return [], repr(exc)


def pages_from_cache_or_pdf(derived_root: Path, pdf_path: Path, source_root: Path) -> Tuple[List[Dict], Optional[str], str]:
    cache_path, cached = read_portable_cache(
        derived_root=derived_root,
        pdf_path=pdf_path,
        source_root=source_root,
        ocr=False,
    )
    if cached:
        portable_path = extracted_cache_path(derived_root, pdf_path, source_root)
        if cache_path != portable_path or cached.get("source_key") != portable_source_key(pdf_path, source_root):
            cached = {
                **cached,
                "source_path": str(pdf_path),
                "source_key": portable_source_key(pdf_path, source_root),
            }
            write_json(portable_path, cached)
        return cached.get("pages", []), cached.get("error"), "cache"

    pages, error = extract_pages_for_classification(pdf_path)
    payload = {
        "source_path": str(pdf_path),
        "source_key": portable_source_key(pdf_path, source_root),
        "file_hash": sha1_file(pdf_path),
        "error": error,
        "pages": pages,
    }
    write_json(extracted_cache_path(derived_root, pdf_path, source_root), payload)
    return pages, error, "pdf"


def existing_ocr_pages(derived_root: Path, pdf_path: Path, source_root: Path) -> int:
    _, cached = read_portable_cache(
        derived_root=derived_root,
        pdf_path=pdf_path,
        source_root=source_root,
        ocr=True,
    )
    if not cached or not reusable_ocr_cache(cached):
        return 0
    return len(cached.get("pages", []))


def classify_pdf(
    *,
    pdf_path: Path,
    source_root: Path,
    derived_root: Path,
    min_page_chars: int,
    min_avg_chars: int,
    mixed_page_ratio: float,
    text_native_poor_ratio: float,
) -> Dict:
    pages, error, source = pages_from_cache_or_pdf(derived_root, pdf_path, source_root)
    page_count = len(pages)
    page_char_counts = [len(clean(page.get("text"))) for page in pages]
    extracted_text_chars = sum(page_char_counts)
    avg_chars_per_page = round(extracted_text_chars / page_count, 1) if page_count else 0.0
    text_poor_page_count = sum(1 for count in page_char_counts if count < min_page_chars)
    text_rich_page_count = page_count - text_poor_page_count
    text_poor_ratio = (text_poor_page_count / page_count) if page_count else 1.0
    ocr_page_count = existing_ocr_pages(derived_root, pdf_path, source_root)

    if page_count == 0:
        classification = "low_text"
        recommended_action = "inspect_pdf"
    elif extracted_text_chars == 0 or text_rich_page_count == 0:
        classification = "scan_only"
        recommended_action = "ocr_all_pages"
    elif text_poor_ratio <= text_native_poor_ratio and avg_chars_per_page >= min_avg_chars:
        classification = "text_native"
        recommended_action = "none"
    elif text_poor_ratio >= mixed_page_ratio:
        classification = "mixed"
        recommended_action = "ocr_text_poor_pages"
    else:
        classification = "low_text"
        recommended_action = "ocr_text_poor_pages" if text_poor_page_count else "ocr_all_pages"

    return {
        "relative_path": portable_source_key(pdf_path, source_root),
        "local_path": str(pdf_path),
        "classification": classification,
        "recommended_action": recommended_action,
        "page_count": page_count,
        "extracted_text_chars": extracted_text_chars,
        "avg_chars_per_page": avg_chars_per_page,
        "text_poor_page_count": text_poor_page_count,
        "text_rich_page_count": text_rich_page_count,
        "existing_ocr_page_count": ocr_page_count,
        "cache_source": source,
        "error": error,
    }


def markdown_report(payload: Dict) -> str:
    items = payload["pdfs"]
    by_class = defaultdict(list)
    for item in items:
        by_class[item["classification"]].append(item)

    lines = [
        "# PDF Classification Report",
        "",
        f"Generated: {payload['generated_at']}",
        f"Source root: `{payload['source_root']}`",
        f"PDFs: {payload['totals']['pdfs']}",
        "",
        "## Summary",
        "",
        "| Classification | Count | Recommended next step |",
        "| --- | ---: | --- |",
    ]
    labels = {
        "scan_only": "OCR all pages",
        "low_text": "OCR text-poor pages",
        "mixed": "OCR text-poor pages",
        "text_native": "No OCR needed",
    }
    for classification in ["scan_only", "low_text", "mixed", "text_native"]:
        lines.append(
            f"| `{classification}` | {payload['totals']['by_classification'].get(classification, 0)} | {labels[classification]} |"
        )

    for classification in ["scan_only", "low_text", "mixed", "text_native"]:
        rows = sorted(
            by_class.get(classification, []),
            key=lambda item: (
                item["recommended_action"] == "none",
                -(item["text_poor_page_count"]),
                item["relative_path"],
            ),
        )
        lines.extend(["", f"## {classification}", ""])
        if not rows:
            lines.append("_No PDFs in this class._")
            continue
        lines.extend(
            [
                "| PDF | Pages | Text chars | Avg chars/page | Text-poor pages | OCR pages | Action |",
                "| --- | ---: | ---: | ---: | ---: | ---: | --- |",
            ]
        )
        for item in rows:
            lines.append(
                "| `{relative_path}` | {page_count} | {extracted_text_chars} | {avg_chars_per_page} | "
                "{text_poor_page_count} | {existing_ocr_page_count} | `{recommended_action}` |".format(**item)
            )

    return "\n".join(lines) + "\n"


def build_report(
    *,
    source_root: Path,
    derived_root: Path,
    min_page_chars: int,
    min_avg_chars: int,
    mixed_page_ratio: float,
    text_native_poor_ratio: float,
) -> Dict:
    pdfs = [
        classify_pdf(
            pdf_path=pdf_path,
            source_root=source_root,
            derived_root=derived_root,
            min_page_chars=min_page_chars,
            min_avg_chars=min_avg_chars,
            mixed_page_ratio=mixed_page_ratio,
            text_native_poor_ratio=text_native_poor_ratio,
        )
        for pdf_path in tqdm(candidate_pdfs(source_root), desc="Classifying PDFs")
    ]
    counts = Counter(item["classification"] for item in pdfs)
    return {
        "generated_at": now_iso(),
        "source_root": str(source_root),
        "derived_root": str(derived_root),
        "thresholds": {
            "min_page_chars": min_page_chars,
            "min_avg_chars": min_avg_chars,
            "mixed_page_ratio": mixed_page_ratio,
            "text_native_poor_ratio": text_native_poor_ratio,
        },
        "totals": {
            "pdfs": len(pdfs),
            "by_classification": dict(sorted(counts.items())),
            "text_poor_pages": sum(item["text_poor_page_count"] for item in pdfs),
            "existing_ocr_pages": sum(item["existing_ocr_page_count"] for item in pdfs),
        },
        "pdfs": pdfs,
    }


def default_markdown_path(json_path: Path) -> Path:
    return json_path.with_suffix(".md")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Classify PDFs by extracted text coverage.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--derived-root", type=Path, default=Path("derived"))
    parser.add_argument("--out", type=Path, default=Path("reports/pdf_classification.json"))
    parser.add_argument("--markdown-out", type=Path)
    parser.add_argument("--min-page-chars", type=int, default=DEFAULT_MIN_PAGE_CHARS)
    parser.add_argument("--min-avg-chars", type=int, default=DEFAULT_MIN_AVG_CHARS)
    parser.add_argument("--mixed-page-ratio", type=float, default=DEFAULT_MIXED_PAGE_RATIO)
    parser.add_argument("--text-native-poor-ratio", type=float, default=DEFAULT_TEXT_NATIVE_POOR_RATIO)
    args = parser.parse_args(argv)

    source_root = args.source_root.expanduser().resolve()
    derived_root = args.derived_root
    if not derived_root.is_absolute():
        derived_root = Path.cwd() / derived_root

    report = build_report(
        source_root=source_root,
        derived_root=derived_root,
        min_page_chars=args.min_page_chars,
        min_avg_chars=args.min_avg_chars,
        mixed_page_ratio=args.mixed_page_ratio,
        text_native_poor_ratio=args.text_native_poor_ratio,
    )
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
