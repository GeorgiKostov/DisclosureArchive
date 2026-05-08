from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import pdfplumber
from tqdm import tqdm

from .common import (
    DEFAULT_DIM,
    DEFAULT_MODEL,
    chunk_text,
    clean,
    csv_record,
    manifest_entries_by_row,
    read_csv_rows,
    read_json,
    sha1_file,
    sha1_text,
    video_by_id,
    write_json,
)
from .db import connect, init_db, reset_db
from .embeddings import embed_texts, missing_embedding_chunks, pack_vector
from .ocr import default_ocr_cache_path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def local_path(source_root: Path, target: str) -> Optional[Path]:
    if not target:
        return None
    path = source_root / target
    return path if path.exists() else None


def find_video_path(source_root: Path, video_id: str) -> Optional[Path]:
    if not video_id:
        return None
    videos = source_root / "videos"
    if not videos.exists():
        return None
    matches = sorted(videos.glob(f"{video_id}_*.mp4"))
    return matches[0] if matches else None


def file_info(path: Optional[Path]) -> Tuple[str, int]:
    if not path or not path.exists():
        return "", 0
    return sha1_file(path), path.stat().st_size


def upsert_document(conn, record, content_hash: str) -> None:
    conn.execute(
        """
        INSERT INTO documents (
          doc_id, row_number, title, release_type, agency, release_date,
          incident_date, incident_location, description, source_url,
          dvids_video_id, content_hash, indexed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(doc_id) DO UPDATE SET
          row_number=excluded.row_number,
          title=excluded.title,
          release_type=excluded.release_type,
          agency=excluded.agency,
          release_date=excluded.release_date,
          incident_date=excluded.incident_date,
          incident_location=excluded.incident_location,
          description=excluded.description,
          source_url=excluded.source_url,
          dvids_video_id=excluded.dvids_video_id,
          content_hash=excluded.content_hash,
          indexed_at=excluded.indexed_at
        """,
        (
            record.doc_id,
            record.row_number,
            record.title,
            record.release_type,
            record.agency,
            record.release_date,
            record.incident_date,
            record.incident_location,
            record.description,
            record.source_url,
            record.dvids_video_id,
            content_hash,
            now_iso(),
        ),
    )


def add_asset(conn, doc_id: str, kind: str, path: Optional[Path], url: str, metadata: Dict) -> None:
    content_hash, byte_count = file_info(path)
    seed = "|".join([doc_id, kind, str(path or ""), url])
    conn.execute(
        """
        INSERT INTO assets (
          asset_id, doc_id, kind, local_path, source_url, content_hash, bytes, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(asset_id) DO UPDATE SET
          local_path=excluded.local_path,
          source_url=excluded.source_url,
          content_hash=excluded.content_hash,
          bytes=excluded.bytes,
          metadata_json=excluded.metadata_json
        """,
        (
            sha1_text(seed)[:20],
            doc_id,
            kind,
            str(path) if path else "",
            url,
            content_hash,
            byte_count,
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        ),
    )


def clear_chunks(conn, doc_id: str) -> None:
    chunk_ids = [r["chunk_id"] for r in conn.execute("SELECT chunk_id FROM chunks WHERE doc_id = ?", (doc_id,))]
    if chunk_ids:
        conn.executemany("DELETE FROM chunks_fts WHERE chunk_id = ?", [(cid,) for cid in chunk_ids])
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))


def add_chunk(
    conn,
    *,
    record,
    source_kind: str,
    page_number: Optional[int],
    chunk_index: int,
    text: str,
    metadata: Dict,
) -> None:
    text = clean(text)
    if not text:
        return
    text_hash = sha1_text(text)
    seed = "|".join([record.doc_id, source_kind, str(page_number or ""), str(chunk_index), text_hash])
    chunk_id = sha1_text(seed)[:24]
    conn.execute(
        """
        INSERT INTO chunks (
          chunk_id, doc_id, source_kind, page_number, chunk_index, title,
          agency, incident_date, incident_location, text, text_hash, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(chunk_id) DO UPDATE SET
          text=excluded.text,
          text_hash=excluded.text_hash,
          metadata_json=excluded.metadata_json
        """,
        (
            chunk_id,
            record.doc_id,
            source_kind,
            page_number,
            chunk_index,
            record.title,
            record.agency,
            record.incident_date,
            record.incident_location,
            text,
            text_hash,
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        ),
    )
    conn.execute(
        """
        INSERT INTO chunks_fts (chunk_id, doc_id, title, agency, incident_location, text)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (chunk_id, record.doc_id, record.title, record.agency, record.incident_location, text),
    )


def metadata_text(record, extra: Optional[str] = None) -> str:
    parts = [
        f"Title: {record.title}",
        f"Type: {record.release_type}",
        f"Agency: {record.agency}",
        f"Release Date: {record.release_date}",
        f"Incident Date: {record.incident_date}",
        f"Incident Location: {record.incident_location}",
        f"Description: {record.description}",
    ]
    if extra:
        parts.append(extra)
    return "\n".join(p for p in parts if clean(p))


def extract_pdf_pages(pdf_path: Path, cache_path: Path) -> List[Dict]:
    file_hash = sha1_file(pdf_path)
    if cache_path.exists():
        cached = read_json(cache_path, {})
        if cached.get("file_hash") == file_hash:
            return cached.get("pages", [])

    pages: List[Dict] = []
    error = None
    start = time.time()
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                except Exception as exc:  # keep indexing resilient for damaged pages
                    text = ""
                    pages.append({"page": page_number, "text": "", "error": repr(exc)})
                    continue
                pages.append({"page": page_number, "text": text, "error": None})
    except Exception as exc:
        error = repr(exc)

    write_json(
        cache_path,
        {
            "source_path": str(pdf_path),
            "file_hash": file_hash,
            "seconds": round(time.time() - start, 2),
            "error": error,
            "pages": pages,
        },
    )
    return pages


def caption_texts(source_root: Path, video_id: str) -> List[Tuple[Path, str]]:
    caption_dir = source_root / "videos" / "captions"
    if not caption_dir.exists():
        return []
    out = []
    for path in sorted(caption_dir.glob(f"{video_id}.*")):
        if path.suffix.lower() not in {".srt", ".vtt", ".txt"}:
            continue
        out.append((path, path.read_text(encoding="utf-8", errors="ignore")))
    return out


def ocr_pages(derived_root: Path, pdf_path: Path) -> List[Dict]:
    path = default_ocr_cache_path(derived_root, pdf_path)
    if not path.exists():
        return []
    data = read_json(path, {})
    if data.get("file_hash") != sha1_file(pdf_path):
        return []
    return data.get("pages", [])


def index_record(conn, source_root: Path, derived_root: Path, record, entries: List[Dict], video: Optional[Dict]) -> Dict:
    primary_paths: List[Path] = []
    asset_hashes: List[str] = []
    resolved_entries: List[Tuple[Dict, Optional[Path]]] = []
    for entry in entries:
        path = local_path(source_root, clean(entry.get("target")))
        resolved_entries.append((entry, path))
        if path and clean(entry.get("category")) == "document":
            primary_paths.append(path)
            h, _ = file_info(path)
            asset_hashes.append(h)
            ocr_path = default_ocr_cache_path(derived_root, path)
            if ocr_path.exists():
                asset_hashes.append(sha1_file(ocr_path))

    vpath = None
    caption_paths: List[Path] = []
    if record.dvids_video_id:
        vpath = find_video_path(source_root, record.dvids_video_id)
        if vpath:
            h, _ = file_info(vpath)
            asset_hashes.append(h)
        for cpath, _ in caption_texts(source_root, record.dvids_video_id):
            caption_paths.append(cpath)

    content_hash = sha1_text("|".join([record.description, *asset_hashes]))
    existing = conn.execute(
        "SELECT content_hash FROM documents WHERE doc_id = ?", (record.doc_id,)
    ).fetchone()
    existing_chunk_count = conn.execute(
        "SELECT count(*) FROM chunks WHERE doc_id = ?", (record.doc_id,)
    ).fetchone()[0]
    unchanged = bool(existing and existing["content_hash"] == content_hash and existing_chunk_count)

    upsert_document(conn, record, content_hash)

    for entry, path in resolved_entries:
        add_asset(conn, record.doc_id, clean(entry.get("category")), path, clean(entry.get("url")), entry)

    if record.dvids_video_id:
        add_asset(conn, record.doc_id, "video", vpath, clean((video or {}).get("best_mp4")), video or {})
        for cpath in caption_paths:
            add_asset(conn, record.doc_id, "caption", cpath, "", {"video_id": record.dvids_video_id})

    if unchanged:
        return {
            "doc_id": record.doc_id,
            "title": record.title,
            "pages": 0,
            "pdf_text_chars": 0,
            "skipped": True,
        }

    clear_chunks(conn, record.doc_id)

    add_chunk(
        conn,
        record=record,
        source_kind="metadata",
        page_number=None,
        chunk_index=0,
        text=metadata_text(record, extra=clean((video or {}).get("description"))),
        metadata={"row_number": record.row_number, "source": "csv"},
    )

    total_pdf_pages = 0
    total_pdf_text_chars = 0
    total_ocr_chars = 0
    for pdf_path in primary_paths:
        if pdf_path.suffix.lower() != ".pdf":
            continue
        cache_path = derived_root / "text" / f"{sha1_text(str(pdf_path))[:16]}.json"
        pages = extract_pdf_pages(pdf_path, cache_path)
        total_pdf_pages += len(pages)
        chunk_index = 1
        for page in pages:
            page_text = clean(page.get("text"))
            total_pdf_text_chars += len(page_text)
            for part in chunk_text(page_text):
                add_chunk(
                    conn,
                    record=record,
                    source_kind="pdf_text",
                    page_number=int(page.get("page") or 0),
                    chunk_index=chunk_index,
                    text=part,
                    metadata={"local_path": str(pdf_path), "page": page.get("page")},
                )
                chunk_index += 1

        ocr_chunk_index = 1
        for page in ocr_pages(derived_root, pdf_path):
            page_text = clean(page.get("text"))
            total_ocr_chars += len(page_text)
            for part in chunk_text(page_text):
                add_chunk(
                    conn,
                    record=record,
                    source_kind="ocr_text",
                    page_number=int(page.get("page") or 0),
                    chunk_index=ocr_chunk_index,
                    text=part,
                    metadata={
                        "local_path": str(pdf_path),
                        "page": page.get("page"),
                        "ocr": True,
                    },
                )
                ocr_chunk_index += 1

    if video:
        video_extra = "\n".join(
            [
                f"DVIDS title: {clean(video.get('dvids_title'))}",
                f"DVIDS date: {clean(video.get('date'))}",
                f"DVIDS description: {clean(video.get('description'))}",
            ]
        )
        for index, part in enumerate(chunk_text(video_extra), start=1):
            add_chunk(
                conn,
                record=record,
                source_kind="video_metadata",
                page_number=None,
                chunk_index=index,
                text=part,
                metadata={"video_id": record.dvids_video_id},
            )
        for cpath, ctext in caption_texts(source_root, record.dvids_video_id):
            for index, part in enumerate(chunk_text(ctext), start=1):
                add_chunk(
                    conn,
                    record=record,
                    source_kind="caption",
                    page_number=None,
                    chunk_index=index,
                    text=part,
                    metadata={"video_id": record.dvids_video_id, "local_path": str(cpath)},
                )

    return {
        "doc_id": record.doc_id,
        "title": record.title,
        "pages": total_pdf_pages,
        "pdf_text_chars": total_pdf_text_chars,
        "ocr_text_chars": total_ocr_chars,
        "skipped": False,
    }


def build_embeddings(conn, model_name: str, batch_size: int) -> int:
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=model_name)
    total = 0
    remaining = conn.execute(
        """
        SELECT count(*)
        FROM chunks c
        LEFT JOIN embeddings e
          ON e.chunk_id = c.chunk_id AND e.model = ?
        WHERE e.chunk_id IS NULL
        """,
        (model_name,),
    ).fetchone()[0]
    progress = tqdm(total=remaining, desc="Embedding chunks")
    while True:
        rows = missing_embedding_chunks(conn, model_name=model_name, limit=batch_size)
        if not rows:
            break
        vectors = list(model.embed([r["text"] for r in rows]))
        conn.executemany(
            """
            INSERT OR REPLACE INTO embeddings (chunk_id, model, dim, vector)
            VALUES (?, ?, ?, ?)
            """,
            [
                (row["chunk_id"], model_name, len(vector), pack_vector(vector))
                for row, vector in zip(rows, vectors)
            ],
        )
        conn.commit()
        total += len(rows)
        progress.update(len(rows))
    progress.close()
    return total


def pdf_cache_totals(derived_root: Path) -> Dict[str, int]:
    pages = 0
    chars = 0
    for path in (derived_root / "text").glob("*.json"):
        cached = read_json(path, {})
        cached_pages = cached.get("pages", [])
        pages += len(cached_pages)
        chars += sum(len(clean(page.get("text"))) for page in cached_pages)
    ocr_pages_total = 0
    ocr_chars = 0
    for path in (derived_root / "text" / "ocr").glob("*.json"):
        cached = read_json(path, {})
        cached_pages = cached.get("pages", [])
        ocr_pages_total += len(cached_pages)
        ocr_chars += sum(len(clean(page.get("text"))) for page in cached_pages)
    return {
        "pdf_pages_cached_total": pages,
        "pdf_text_chars_cached_total": chars,
        "ocr_pages_cached_total": ocr_pages_total,
        "ocr_text_chars_cached_total": ocr_chars,
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build/update local UFO release search index.")
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--video-manifest", type=Path)
    parser.add_argument("--derived-root", type=Path, default=Path("derived"))
    parser.add_argument("--rebuild", action="store_true")
    parser.add_argument("--skip-embeddings", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=128)
    args = parser.parse_args(argv)

    source_root = args.source_root.expanduser().resolve()
    csv_path = args.csv or source_root / "uap-csv.cdp.csv"
    manifest_path = args.manifest or source_root / "uap_download_manifest.json"
    video_manifest_path = args.video_manifest or source_root / "dvids_video_manifest.cdp.json"
    derived_root = args.derived_root
    if not derived_root.is_absolute():
        derived_root = Path.cwd() / derived_root

    if args.rebuild:
        reset_db(args.db)

    rows = [csv_record(row) for row in read_csv_rows(csv_path)]
    manifest = read_json(manifest_path, {"entries": []})
    entries_by_row = manifest_entries_by_row(manifest)
    videos = video_by_id(read_json(video_manifest_path, []))

    conn = connect(args.db)
    init_db(conn)

    results = []
    for record in tqdm(rows, desc="Indexing records"):
        results.append(
            index_record(
                conn,
                source_root,
                derived_root,
                record,
                entries_by_row.get(record.row_number, []),
                videos.get(record.dvids_video_id),
            )
        )
        conn.commit()

    embedded = 0
    if not args.skip_embeddings:
        embedded = build_embeddings(conn, args.model, args.batch_size)

    cache_totals = pdf_cache_totals(derived_root)
    summary = {
        "source_root": str(source_root),
        "csv": str(csv_path),
        "db": str(args.db),
        "documents": conn.execute("SELECT count(*) FROM documents").fetchone()[0],
        "assets": conn.execute("SELECT count(*) FROM assets").fetchone()[0],
        "chunks": conn.execute("SELECT count(*) FROM chunks").fetchone()[0],
        "documents_skipped_unchanged": sum(1 for item in results if item.get("skipped")),
        "embeddings_added": embedded,
        "embeddings_total": conn.execute("SELECT count(*) FROM embeddings").fetchone()[0],
        "pdf_pages_processed_this_run": sum(item["pages"] for item in results),
        "pdf_text_chars_processed_this_run": sum(item["pdf_text_chars"] for item in results),
        "ocr_text_chars_processed_this_run": sum(item.get("ocr_text_chars", 0) for item in results),
        **cache_totals,
        "model": args.model,
        "indexed_at": now_iso(),
    }
    write_json(Path(args.db).with_suffix(".summary.json"), summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
