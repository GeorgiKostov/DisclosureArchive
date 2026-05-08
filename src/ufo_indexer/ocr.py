from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import pypdfium2 as pdfium
from PIL import Image
from tqdm import tqdm

from .common import clean, read_json, sha1_file, sha1_text, write_json


def default_ocr_cache_path(derived_root: Path, pdf_path: Path) -> Path:
    return derived_root / "text" / "ocr" / f"{sha1_text(str(pdf_path))[:16]}.json"


def extracted_cache_path(derived_root: Path, pdf_path: Path) -> Path:
    return derived_root / "text" / f"{sha1_text(str(pdf_path))[:16]}.json"


def text_poor_pages(derived_root: Path, pdf_path: Path, min_chars: int) -> Optional[Set[int]]:
    cache = extracted_cache_path(derived_root, pdf_path)
    if not cache.exists():
        return None
    data = read_json(cache, {})
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
    with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
        image.save(image_file.name)
        cmd = [tesseract_bin, image_file.name, "stdout", "-l", lang, "--psm", psm]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(proc.stderr.strip() or f"tesseract exited {proc.returncode}")
        return proc.stdout


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
) -> Dict:
    output_path = default_ocr_cache_path(derived_root, pdf_path)
    file_hash = sha1_file(pdf_path)
    if output_path.exists() and not force:
        existing = read_json(output_path, {})
        if existing.get("file_hash") == file_hash:
            return existing

    start = time.time()
    page_results: List[Dict] = []
    with pdfium.PdfDocument(str(pdf_path)) as pdf:
        page_count = len(pdf)
        wanted = pages or set(range(1, page_count + 1))
        for page_number in tqdm(range(1, page_count + 1), desc=pdf_path.name, leave=False):
            if page_number not in wanted:
                continue
            try:
                page = pdf[page_number - 1]
                image = render_page(page, dpi)
                text = tesseract_image(image, lang=lang, psm=psm, tesseract_bin=tesseract_bin)
                page_results.append({"page": page_number, "text": text, "error": None})
            except Exception as exc:
                page_results.append({"page": page_number, "text": "", "error": repr(exc)})

    payload = {
        "source_path": str(pdf_path),
        "file_hash": file_hash,
        "dpi": dpi,
        "lang": lang,
        "psm": psm,
        "seconds": round(time.time() - start, 2),
        "pages": page_results,
    }
    write_json(output_path, payload)
    return payload


def candidate_pdfs(source_root: Path) -> List[Path]:
    documents = source_root / "documents"
    if not documents.exists():
        return []
    return sorted(documents.glob("*.pdf"))


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="OCR scanned or text-poor UFO release PDFs.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--derived-root", type=Path, default=Path("derived"))
    parser.add_argument("--pdf", type=Path, action="append", help="Specific PDF to OCR. Repeatable.")
    parser.add_argument("--limit", type=int, help="Maximum number of PDFs to process.")
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
            f"Missing {args.tesseract_bin!r}. On macOS, install it with: brew install tesseract"
        )

    source_root = args.source_root.expanduser().resolve()
    derived_root = args.derived_root
    if not derived_root.is_absolute():
        derived_root = Path.cwd() / derived_root

    pdfs = [p.expanduser().resolve() for p in args.pdf] if args.pdf else candidate_pdfs(source_root)
    if args.limit:
        pdfs = pdfs[: args.limit]

    summary = []
    for pdf_path in tqdm(pdfs, desc="OCR PDFs"):
        pages = None if args.all_pages else text_poor_pages(derived_root, pdf_path, args.min_page_chars)
        if pages == set():
            summary.append({"pdf": str(pdf_path), "skipped": True, "reason": "all pages have text"})
            continue
        result = ocr_pdf(
            pdf_path,
            derived_root=derived_root,
            pages=pages,
            dpi=args.dpi,
            lang=args.lang,
            psm=args.psm,
            tesseract_bin=args.tesseract_bin,
            force=args.force,
        )
        summary.append(
            {
                "pdf": str(pdf_path),
                "pages_ocrd": len(result.get("pages", [])),
                "chars": sum(len(clean(page.get("text"))) for page in result.get("pages", [])),
                "seconds": result.get("seconds"),
            }
        )

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
