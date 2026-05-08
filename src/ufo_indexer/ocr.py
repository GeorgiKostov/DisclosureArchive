from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import suppress
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pypdfium2 as pdfium
from PIL import Image
from tqdm import tqdm

from .common import clean, read_json, sha1_file, sha1_text, write_json


def portable_source_key(path: Path, source_root: Optional[Path] = None) -> str:
    if source_root:
        try:
            return path.resolve().relative_to(source_root.resolve()).as_posix()
        except ValueError:
            pass
    return str(path)


def default_ocr_cache_path(
    derived_root: Path, pdf_path: Path, source_root: Optional[Path] = None
) -> Path:
    return derived_root / "text" / "ocr" / f"{sha1_text(portable_source_key(pdf_path, source_root))[:16]}.json"


def extracted_cache_path(
    derived_root: Path, pdf_path: Path, source_root: Optional[Path] = None
) -> Path:
    return derived_root / "text" / f"{sha1_text(portable_source_key(pdf_path, source_root))[:16]}.json"


def legacy_extracted_cache_path(derived_root: Path, pdf_path: Path) -> Path:
    return derived_root / "text" / f"{sha1_text(str(pdf_path))[:16]}.json"


def legacy_ocr_cache_path(derived_root: Path, pdf_path: Path) -> Path:
    return derived_root / "text" / "ocr" / f"{sha1_text(str(pdf_path))[:16]}.json"


def candidate_cache_paths(cache_path: Path, legacy_path: Path) -> Iterable[Path]:
    yield cache_path
    if legacy_path != cache_path:
        yield legacy_path


def find_cache_by_file_hash(cache_dir: Path, file_hash: str, skip: Set[Path]) -> Optional[Tuple[Path, Dict]]:
    if not cache_dir.exists():
        return None
    for path in sorted(cache_dir.glob("*.json")):
        resolved = path.resolve()
        if resolved in skip:
            continue
        data = read_json(path, {})
        if data.get("file_hash") == file_hash:
            return path, data
    return None


def read_portable_cache(
    *,
    derived_root: Path,
    pdf_path: Path,
    source_root: Optional[Path],
    ocr: bool,
) -> Tuple[Optional[Path], Dict]:
    if ocr:
        primary = default_ocr_cache_path(derived_root, pdf_path, source_root)
        legacy = legacy_ocr_cache_path(derived_root, pdf_path)
    else:
        primary = extracted_cache_path(derived_root, pdf_path, source_root)
        legacy = legacy_extracted_cache_path(derived_root, pdf_path)
    file_hash = sha1_file(pdf_path)
    checked: Set[Path] = set()
    for path in candidate_cache_paths(primary, legacy):
        checked.add(path.resolve())
        data = read_json(path, {})
        if data.get("file_hash") == file_hash:
            return path, data
    found = find_cache_by_file_hash(primary.parent, file_hash, checked)
    if found:
        return found
    return None, {}


def text_poor_pages(
    derived_root: Path,
    pdf_path: Path,
    min_chars: int,
    source_root: Optional[Path] = None,
) -> Optional[Set[int]]:
    _, data = read_portable_cache(
        derived_root=derived_root,
        pdf_path=pdf_path,
        source_root=source_root,
        ocr=False,
    )
    if not data:
        return None
    pages = data.get("pages", [])
    if not pages:
        return None
    return {
        int(page.get("page") or 0)
        for page in pages
        if len(clean(page.get("text"))) < min_chars
    }


def render_page(page, dpi: int) -> Image.Image:
    scale = dpi / 72
    bitmap = page.render(scale=scale, rotation=0)
    return bitmap.to_pil()


def tesseract_image(image: Image.Image, *, lang: str, psm: str, tesseract_bin: str) -> str:
    image_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as image_file:
            image_path = image_file.name
        image.save(image_path)
        cmd = [tesseract_bin, image_path, "stdout", "-l", lang, "--psm", psm]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"tesseract exited {proc.returncode}")
        return proc.stdout
    finally:
        if image_path:
            with suppress(FileNotFoundError, PermissionError):
                Path(image_path).unlink()


def reusable_ocr_cache(data: Dict) -> bool:
    pages = data.get("pages", [])
    if not pages:
        return False
    return not any(page.get("error") for page in pages)


def merge_page_results(existing: Dict, page_results: List[Dict]) -> List[Dict]:
    by_page = {
        int(page.get("page") or 0): page
        for page in existing.get("pages", [])
        if page.get("page")
    }
    for page in page_results:
        if page.get("page"):
            by_page[int(page["page"])] = page
    return [by_page[page_number] for page_number in sorted(by_page)]


def ocr_pdf(
    pdf_path: Path,
    *,
    derived_root: Path,
    pages: Optional[Set[int]],
    dpi: int,
    lang: str,
    psm: str,
    tesseract_bin: str,
    force: bool,
    source_root: Optional[Path] = None,
    show_progress: bool = True,
) -> Dict:
    output_path = default_ocr_cache_path(derived_root, pdf_path, source_root)
    file_hash = sha1_file(pdf_path)
    if not force:
        existing_path, existing = read_portable_cache(
            derived_root=derived_root,
            pdf_path=pdf_path,
            source_root=source_root,
            ocr=True,
        )
        if existing and reusable_ocr_cache(existing):
            migrated = False
            if existing.get("source_key") != portable_source_key(pdf_path, source_root):
                existing = {
                    **existing,
                    "source_path": str(pdf_path),
                    "source_key": portable_source_key(pdf_path, source_root),
                }
                migrated = True
            if existing_path != output_path or migrated:
                write_json(output_path, existing)
            return existing

    start = time.time()
    page_results: List[Dict] = []
    existing_for_merge: Dict = {}
    existing_path: Optional[Path] = None
    if pages is not None:
        existing_path, existing_for_merge = read_portable_cache(
            derived_root=derived_root,
            pdf_path=pdf_path,
            source_root=source_root,
            ocr=True,
        )
    with pdfium.PdfDocument(str(pdf_path)) as pdf:
        page_count = len(pdf)
        wanted = pages or set(range(1, page_count + 1))
        iterator = range(1, page_count + 1)
        if show_progress:
            iterator = tqdm(iterator, desc=pdf_path.name, leave=False)
        for page_number in iterator:
            if page_number not in wanted:
                continue
            try:
                page = pdf[page_number - 1]
                image = render_page(page, dpi)
                text = tesseract_image(image, lang=lang, psm=psm, tesseract_bin=tesseract_bin)
                page_results.append({"page": page_number, "text": text, "error": None})
            except Exception as exc:
                page_results.append({"page": page_number, "text": "", "error": repr(exc)})

    merged_pages = merge_page_results(existing_for_merge, page_results) if existing_for_merge else page_results
    payload = {
        "source_path": str(pdf_path),
        "source_key": portable_source_key(pdf_path, source_root),
        "file_hash": file_hash,
        "dpi": dpi,
        "lang": lang,
        "psm": psm,
        "seconds": round(time.time() - start, 2),
        "pages": merged_pages,
    }
    if existing_for_merge and existing_path:
        payload["previous_cache_path"] = str(existing_path)
        payload["retry_pages"] = sorted(pages or [])
    write_json(output_path, payload)
    return payload


def candidate_pdfs(source_root: Path) -> List[Path]:
    documents = source_root / "documents"
    if not documents.exists():
        return []
    return sorted(documents.glob("*.pdf"))


def pdfs_from_classification(source_root: Path, classification_path: Path, classes: Set[str]) -> Tuple[List[Path], Dict[Path, str]]:
    report = read_json(classification_path, {})
    selected = []
    actions: Dict[Path, str] = {}
    for item in report.get("pdfs", []):
        if item.get("classification") not in classes:
            continue
        relative_path = item.get("relative_path")
        if not relative_path:
            continue
        pdf_path = (source_root / relative_path).resolve()
        if pdf_path.exists():
            selected.append((int(item.get("page_count") or 0), relative_path, pdf_path))
            actions[pdf_path] = item.get("recommended_action") or "ocr_text_poor_pages"
    pdfs = [item[2] for item in sorted(selected)]
    return list(dict.fromkeys(pdfs)), actions


def pdfs_from_status(
    source_root: Path,
    status_path: Path,
    review_reasons: Set[str],
) -> Tuple[List[Path], Dict[Path, str], Dict[Path, Set[int]]]:
    report = read_json(status_path, {})
    selected = []
    actions: Dict[Path, str] = {}
    retry_pages: Dict[Path, Set[int]] = {}
    for item in report.get("pdfs", []):
        if not item.get("needs_review"):
            continue
        item_reasons = set(item.get("review_reasons", []))
        if review_reasons and not item_reasons.intersection(review_reasons):
            continue
        relative_path = item.get("relative_path")
        if not relative_path:
            continue
        pdf_path = (source_root / relative_path).resolve()
        if not pdf_path.exists():
            continue
        selected.append((int(item.get("zero_text_page_count") or 0), relative_path, pdf_path))
        actions[pdf_path] = item.get("recommended_action") or "ocr_retry"
        pages = set(int(page) for page in item.get("zero_text_pages", []) if int(page) > 0)
        pages.update(
            int(page.get("page") or 0)
            for page in item.get("error_pages", [])
            if int(page.get("page") or 0) > 0
        )
        pages.update(int(page) for page in item.get("missing_pages", []) if int(page) > 0)
        if not pages and "low_avg_chars" in item_reasons:
            pages = set(range(1, int(item.get("ocr_pages") or 0) + 1))
        if pages:
            retry_pages[pdf_path] = pages
    pdfs = [item[2] for item in sorted(selected, key=lambda item: (-item[0], item[1]))]
    return list(dict.fromkeys(pdfs)), actions, retry_pages


def ocr_one_task(task: Dict) -> Dict:
    pdf_path = Path(task["pdf_path"])
    derived_root = Path(task["derived_root"])
    source_root = Path(task["source_root"])
    action = task.get("action")
    ocr_all_pages = bool(task.get("all_pages")) or action == "ocr_all_pages"
    if task.get("pages"):
        pages = set(int(page) for page in task["pages"])
    elif ocr_all_pages:
        pages = None
    else:
        pages = text_poor_pages(
            derived_root,
            pdf_path,
            int(task["min_page_chars"]),
            source_root=source_root,
        )
    if pages == set():
        return {
            "pdf": str(pdf_path),
            "recommended_action": action or ("ocr_all_pages" if task.get("all_pages") else "ocr_text_poor_pages"),
            "skipped": True,
            "reason": "all pages have text",
        }
    result = ocr_pdf(
        pdf_path,
        derived_root=derived_root,
        pages=pages,
        dpi=int(task["dpi"]),
        lang=str(task["lang"]),
        psm=str(task["psm"]),
        tesseract_bin=str(task["tesseract_bin"]),
        force=bool(task["force"]),
        source_root=source_root,
        show_progress=bool(task.get("show_progress")),
    )
    return {
        "pdf": str(pdf_path),
        "recommended_action": action or ("ocr_all_pages" if task.get("all_pages") else "ocr_text_poor_pages"),
        "pages_ocrd": len(pages) if pages is not None else len(result.get("pages", [])),
        "cache_pages": len(result.get("pages", [])),
        "retry_pages": sorted(pages or []),
        "cache_chars": sum(len(clean(page.get("text"))) for page in result.get("pages", [])),
        "seconds": result.get("seconds"),
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="OCR scanned or text-poor UFO release PDFs.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--derived-root", type=Path, default=Path("derived"))
    parser.add_argument("--pdf", type=Path, action="append", help="Specific PDF to OCR. Repeatable.")
    parser.add_argument("--from-classification", type=Path, help="Classification JSON from ufo_indexer.classify.")
    parser.add_argument("--from-status", type=Path, help="OCR status JSON from ufo_indexer.ocr_status.")
    parser.add_argument(
        "--review-reasons",
        nargs="+",
        choices=["missing", "partial", "ocr_errors", "zero_text_pages", "low_avg_chars"],
        default=["missing", "partial", "ocr_errors", "zero_text_pages", "low_avg_chars"],
        help="Review reasons to retry when --from-status is used.",
    )
    parser.add_argument(
        "--classes",
        nargs="+",
        choices=["scan_only", "low_text", "mixed", "text_native"],
        default=["scan_only", "low_text", "mixed"],
        help="PDF classes to OCR when --from-classification is used.",
    )
    parser.add_argument("--limit", type=int, help="Maximum number of PDFs to process.")
    parser.add_argument("--workers", type=int, default=1, help="Parallel PDF OCR workers.")
    parser.add_argument("--min-page-chars", type=int, default=80)
    parser.add_argument("--all-pages", action="store_true", help="OCR every page, not only text-poor pages.")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--lang", default="eng")
    parser.add_argument("--psm", default="6")
    parser.add_argument("--tesseract-bin", default="tesseract")
    args = parser.parse_args(argv)

    if not shutil.which(args.tesseract_bin):
        raise SystemExit(
            f"Missing {args.tesseract_bin!r}. On macOS, install it with: brew install tesseract. "
            "On Windows, install it with: winget install UB-Mannheim.TesseractOCR"
        )

    source_root = args.source_root.expanduser().resolve()
    derived_root = args.derived_root
    if not derived_root.is_absolute():
        derived_root = Path.cwd() / derived_root

    classification_actions: Dict[Path, str] = {}
    retry_pages_by_pdf: Dict[Path, Set[int]] = {}
    if args.from_status:
        pdfs, classification_actions, retry_pages_by_pdf = pdfs_from_status(
            source_root,
            args.from_status,
            set(args.review_reasons),
        )
        if args.pdf:
            pdfs.extend(p.expanduser().resolve() for p in args.pdf)
            pdfs = sorted(dict.fromkeys(pdfs))
    elif args.from_classification:
        pdfs, classification_actions = pdfs_from_classification(source_root, args.from_classification, set(args.classes))
        if args.pdf:
            pdfs.extend(p.expanduser().resolve() for p in args.pdf)
            pdfs = sorted(dict.fromkeys(pdfs))
    elif args.pdf:
        pdfs = [p.expanduser().resolve() for p in args.pdf]
    else:
        pdfs = candidate_pdfs(source_root)
    if args.limit:
        pdfs = pdfs[: args.limit]

    tasks = [
        {
            "pdf_path": str(pdf_path),
            "derived_root": str(derived_root),
            "source_root": str(source_root),
            "action": classification_actions.get(pdf_path),
            "pages": sorted(retry_pages_by_pdf.get(pdf_path, set())),
            "all_pages": args.all_pages,
            "min_page_chars": args.min_page_chars,
            "dpi": args.dpi,
            "lang": args.lang,
            "psm": args.psm,
            "tesseract_bin": args.tesseract_bin,
            "force": args.force or bool(args.from_status),
            "show_progress": args.workers <= 1,
        }
        for pdf_path in pdfs
    ]

    summary = []
    if args.workers <= 1:
        for task in tqdm(tasks, desc="OCR PDFs"):
            summary.append(ocr_one_task(task))
    else:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(ocr_one_task, task) for task in tasks]
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"OCR PDFs ({args.workers} workers)"):
                summary.append(future.result())

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
