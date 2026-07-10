from __future__ import annotations

import argparse
import json
import re
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
from .ocr import default_ocr_cache_path, extracted_cache_path, portable_source_key, read_portable_cache, reusable_ocr_cache


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


GEOCODE_LOCATIONS = {
    "aegean sea": (38.5, 25.0, "region", 0.45),
    "albuquerque, nm": (35.0844, -106.6504, "city", 0.8),
    "amarillo, tx": (35.2220, -101.8313, "city", 0.8),
    "arabian gulf": (26.8, 52.0, "region", 0.45),
    "arabian sea": (15.0, 65.0, "region", 0.35),
    "azerbaijan": (40.3, 47.7, "country", 0.55),
    "detroit, mi": (42.3314, -83.0458, "city", 0.8),
    "djibouti": (11.8251, 42.5903, "country", 0.55),
    "east china sea": (29.0, 125.0, "region", 0.35),
    "georgia": (42.3154, 43.3569, "country", 0.5),
    "germany": (51.1657, 10.4515, "country", 0.55),
    "greece": (39.0742, 21.8243, "country", 0.55),
    "gulf of aden": (12.0, 48.0, "region", 0.45),
    "gulf of oman": (25.0, 58.0, "region", 0.45),
    "iran": (32.4279, 53.6880, "country", 0.55),
    "iraq": (33.2232, 43.6793, "country", 0.55),
    "japan": (36.2048, 138.2529, "country", 0.55),
    "kazakhstan": (48.0196, 66.9237, "country", 0.55),
    "los alamos, nm": (35.8881, -106.3031, "city", 0.8),
    "mediterranean sea": (35.0, 18.0, "region", 0.35),
    "mexico": (23.6345, -102.5528, "country", 0.55),
    "middle east": (29.3, 47.6, "region", 0.3),
    "netherlands": (52.1326, 5.2913, "country", 0.55),
    "new mexico": (34.5199, -105.8701, "region", 0.4),
    "north america": (48.0, -100.0, "region", 0.25),
    "pacific ocean": (0.0, -160.0, "region", 0.2),
    "papua new guinea": (-6.3150, 143.9555, "country", 0.55),
    "persian gulf": (26.8, 52.0, "region", 0.45),
    "sary shagan": (46.0500, 73.5000, "region", 0.55),
    "southern united states": (33.0, -90.0, "region", 0.35),
    "strait of hormuz": (26.6, 56.25, "region", 0.5),
    "syria": (34.8021, 38.9968, "country", 0.55),
    "turkmenistan": (38.9697, 59.5563, "country", 0.55),
    "united arab emirates": (23.4241, 53.8478, "country", 0.55),
    "united states": (39.8283, -98.5795, "country", 0.45),
    "western united states": (39.0, -114.0, "region", 0.35),
    # Combatant-command areas of responsibility (coarse region centroids).
    "centcom": (26.8, 52.0, "region", 0.30),
    "northcom": (44.0, -98.0, "region", 0.25),
    "indopacom": (15.0, 130.0, "region", 0.22),
    "eucom": (50.0, 15.0, "region", 0.28),
    "africom": (8.0, 21.0, "region", 0.22),
    "southcom": (-15.0, -60.0, "region", 0.22),
    # Regions / seas seen in Release 2 video metadata and titles.
    "southeastern united states": (31.0, -84.0, "region", 0.35),
    "midwestern united states": (41.5, -93.0, "region", 0.35),
    "north atlantic ocean": (40.0, -40.0, "region", 0.22),
    "yellow sea": (35.5, 123.5, "region", 0.40),
    "gulf of arabia": (20.0, 60.0, "region", 0.40),
    "texas": (31.0, -99.0, "region", 0.40),
    "afghanistan": (33.9391, 67.7100, "country", 0.55),
    "kabul": (34.5553, 69.2075, "city", 0.75),
    "lake huron": (44.8, -82.4, "lake", 0.75),
    "tyndall afb": (30.07, -85.58, "base", 0.78),
    "eglin afb": (30.46, -86.55, "base", 0.78),
    # Release 3 locations (CSV "Incident Location" exact-match keys).
    "harare, zimbabwe": (-17.8252, 31.0335, "city", 0.8),
    "zimbabwe": (-19.0154, 29.1549, "country", 0.55),
    "colorado springs, colorado, u.s.": (38.8339, -104.8214, "city", 0.8),
    "cape kennedy, florida": (28.4889, -80.5778, "base", 0.78),
    "budapest, hungary": (47.4979, 19.0402, "city", 0.8),
    "hungary": (47.1625, 19.5033, "country", 0.55),
    "houston, texas": (29.7604, -95.3698, "city", 0.8),
    "baku, azerbaijan": (40.4093, 49.8671, "city", 0.8),
    "new jersey, united states": (40.0583, -74.4057, "region", 0.45),
    "washington state, united states": (47.7511, -120.7401, "region", 0.4),
    "northeastern united states": (42.5, -73.5, "region", 0.35),
    "australia": (-25.2744, 133.7751, "country", 0.5),
    "ussr": (55.7558, 37.6173, "country", 0.4),
    # Typo seen in the live CSV (7 R3 rows): "Westen" -> Western United States.
    "westen united states": (39.0, -114.0, "region", 0.35),
    # Catch-all for orbital records; placed over the equator at GEO-ish lon
    # so they at least appear on the map rather than getting dropped silently.
    "low earth orbit": (0.0, 0.0, "region", 0.15),
    # Release 4 locations (CSV "Incident Location" exact-match keys). Several of
    # these are AARO combatant-command sea/region labels for infrared UAP videos.
    "low-earth orbit": (0.0, 0.0, "region", 0.15),
    "eastern united states": (37.5, -76.5, "region", 0.35),
    "atlantic ocean": (30.0, -50.0, "region", 0.20),
    "south china sea": (13.0, 114.0, "region", 0.35),
    "gulf of america": (25.0, -90.0, "region", 0.35),
    "virginia": (37.5, -78.6, "region", 0.45),
}

# Specific place phrases to look for inside a record title; the first (most
# specific) match wins over the broader incident_location gazetteer so videos
# tagged only with a combatant command still land on a meaningful point.
TITLE_PLACE_KEYS = [
    ("lake huron", "lake huron"),
    ("tyndall", "tyndall afb"),
    ("eglin", "eglin afb"),
    ("kabul", "kabul"),
    ("strait of hormuz", "strait of hormuz"),
    ("persian gulf", "persian gulf"),
    ("gulf of arabia", "gulf of arabia"),
    ("gulf of oman", "gulf of oman"),
    ("arabian gulf", "arabian gulf"),
    ("arabian sea", "arabian sea"),
    ("east china sea", "east china sea"),
    ("yellow sea", "yellow sea"),
    ("kazakhstan", "kazakhstan"),
    ("djibouti", "djibouti"),
    ("syria", "syria"),
    ("iran", "iran"),
]

# Human-readable labels for gazetteer keys whose title-cased form is awkward.
LOCATION_LABELS = {
    "tyndall afb": "Tyndall AFB",
    "eglin afb": "Eglin AFB",
    "gulf of arabia": "Gulf of Arabia",
    "gulf of oman": "Gulf of Oman",
    "north atlantic ocean": "North Atlantic Ocean",
    "east china sea": "East China Sea",
    "yellow sea": "Yellow Sea",
    "centcom": "CENTCOM region",
    "northcom": "NORTHCOM region",
    "indopacom": "INDOPACOM region",
    "eucom": "EUCOM region",
    "africom": "AFRICOM region",
    "southcom": "SOUTHCOM region",
}


DECIMAL_COORD_RE = re.compile(
    r"(?<![\d.])([+-]?(?:[0-8]?\d|90)\.\d{2,})\s*,\s*([+-]?(?:1[0-7]\d|[0-9]?\d|180)\.\d{2,})(?![\d.])"
)
DMS_COORD_RE = re.compile(
    r"(\d{1,2})\s*[°º]\s*(\d{1,2})?\s*['’]?\s*(\d{1,2}(?:\.\d+)?)?\s*[\"”]?\s*([NS])"
    r"[\s,;/]+"
    r"(\d{1,3})\s*[°º]\s*(\d{1,2})?\s*['’]?\s*(\d{1,2}(?:\.\d+)?)?\s*[\"”]?\s*([EW])",
    re.IGNORECASE,
)


def dms_to_decimal(degrees: str, minutes: Optional[str], seconds: Optional[str], hemi: str) -> float:
    value = float(degrees) + (float(minutes or 0) / 60.0) + (float(seconds or 0) / 3600.0)
    return -value if hemi.upper() in {"S", "W"} else value


def valid_dms(minutes: Optional[str], seconds: Optional[str]) -> bool:
    return float(minutes or 0) < 60 and float(seconds or 0) < 60


def clear_locations(conn, doc_id: str) -> None:
    conn.execute("DELETE FROM locations WHERE doc_id = ?", (doc_id,))


def add_location(
    conn,
    *,
    doc_id: str,
    chunk_id: Optional[str],
    raw_location: str,
    normalized_location: str,
    latitude: float,
    longitude: float,
    precision: str,
    confidence: float,
    source_kind: str,
    method: str,
    metadata: Dict,
) -> None:
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return
    seed = "|".join(
        [
            doc_id,
            chunk_id or "",
            raw_location.lower(),
            f"{latitude:.6f}",
            f"{longitude:.6f}",
            source_kind,
            method,
        ]
    )
    conn.execute(
        """
        INSERT OR IGNORE INTO locations (
          location_id, doc_id, chunk_id, raw_location, normalized_location,
          latitude, longitude, precision, confidence, source_kind, method,
          metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sha1_text(seed)[:24],
            doc_id,
            chunk_id,
            raw_location,
            normalized_location,
            latitude,
            longitude,
            precision,
            confidence,
            source_kind,
            method,
            json.dumps(metadata, ensure_ascii=False, sort_keys=True),
        ),
    )


def add_incident_location(conn, record) -> None:
    raw = clean(record.incident_location)
    title = clean(record.title).lower()

    # 1. Prefer a specific place named in the title (e.g. "Lake Huron",
    #    "Persian Gulf") over a broad combatant-command label.
    for phrase, key in TITLE_PLACE_KEYS:
        if phrase in title:
            geo = GEOCODE_LOCATIONS.get(key)
            if geo:
                latitude, longitude, precision, confidence = geo
                add_location(
                    conn,
                    doc_id=record.doc_id,
                    chunk_id=None,
                    raw_location=raw or phrase,
                    normalized_location=LOCATION_LABELS.get(key, key.title()),
                    latitude=latitude,
                    longitude=longitude,
                    precision=precision,
                    confidence=confidence,
                    source_kind="metadata",
                    method="title_place_gazetteer",
                    metadata={"field": "title", "matched_place": key},
                )
                return

    # 2. Fall back to the incident_location gazetteer (now incl. commands).
    if not raw or raw == "N/A":
        return
    geo = GEOCODE_LOCATIONS.get(raw.lower())
    if not geo:
        return
    latitude, longitude, precision, confidence = geo
    add_location(
        conn,
        doc_id=record.doc_id,
        chunk_id=None,
        raw_location=raw,
        normalized_location=LOCATION_LABELS.get(raw.lower(), raw),
        latitude=latitude,
        longitude=longitude,
        precision=precision,
        confidence=confidence,
        source_kind="metadata",
        method="incident_location_gazetteer",
        metadata={"field": "incident_location"},
    )


def add_coordinate_locations(conn, record, chunk_id: Optional[str], source_kind: str, text: str) -> None:
    for match in DECIMAL_COORD_RE.finditer(text):
        latitude = float(match.group(1))
        longitude = float(match.group(2))
        add_location(
            conn,
            doc_id=record.doc_id,
            chunk_id=chunk_id,
            raw_location=match.group(0),
            normalized_location=f"{latitude:.6f}, {longitude:.6f}",
            latitude=latitude,
            longitude=longitude,
            precision="coordinate",
            confidence=0.95,
            source_kind=source_kind,
            method="decimal_coordinate_regex",
            metadata={},
        )
    for match in DMS_COORD_RE.finditer(text):
        if not valid_dms(match.group(2), match.group(3)) or not valid_dms(match.group(6), match.group(7)):
            continue
        latitude = dms_to_decimal(match.group(1), match.group(2), match.group(3), match.group(4))
        longitude = dms_to_decimal(match.group(5), match.group(6), match.group(7), match.group(8))
        add_location(
            conn,
            doc_id=record.doc_id,
            chunk_id=chunk_id,
            raw_location=match.group(0),
            normalized_location=f"{latitude:.6f}, {longitude:.6f}",
            latitude=latitude,
            longitude=longitude,
            precision="coordinate",
            confidence=0.95,
            source_kind=source_kind,
            method="dms_coordinate_regex",
            metadata={},
        )


def add_locations_from_existing_chunks(conn, record) -> None:
    for row in conn.execute(
        "SELECT chunk_id, source_kind, text FROM chunks WHERE doc_id = ?",
        (record.doc_id,),
    ):
        add_coordinate_locations(conn, record, row["chunk_id"], row["source_kind"], row["text"])


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
) -> Optional[str]:
    text = clean(text)
    if not text:
        return None
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
    add_coordinate_locations(conn, record, chunk_id, source_kind, text)
    return chunk_id


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


def extract_pdf_pages(pdf_path: Path, cache_path: Path, source_root: Optional[Path] = None) -> List[Dict]:
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
            "source_key": portable_source_key(pdf_path, source_root),
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


def ocr_pages(derived_root: Path, pdf_path: Path, source_root: Path) -> List[Dict]:
    cache_path, data = read_portable_cache(
        derived_root=derived_root,
        pdf_path=pdf_path,
        source_root=source_root,
        ocr=True,
    )
    if not data or not reusable_ocr_cache(data):
        return []
    portable_path = default_ocr_cache_path(derived_root, pdf_path, source_root)
    migrated = False
    if data.get("source_key") != portable_source_key(pdf_path, source_root):
        data = {
            **data,
            "source_path": str(pdf_path),
            "source_key": portable_source_key(pdf_path, source_root),
        }
        migrated = True
    if cache_path != portable_path or not portable_path.exists() or migrated:
        write_json(portable_path, data)
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
            ocr_path, _ = read_portable_cache(
                derived_root=derived_root,
                pdf_path=path,
                source_root=source_root,
                ocr=True,
            )
            if ocr_path and ocr_path.exists():
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
        clear_locations(conn, record.doc_id)
        add_incident_location(conn, record)
        add_locations_from_existing_chunks(conn, record)
        return {
            "doc_id": record.doc_id,
            "title": record.title,
            "pages": 0,
            "pdf_text_chars": 0,
            "skipped": True,
        }

    clear_locations(conn, record.doc_id)
    add_incident_location(conn, record)
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
        cache_path = extracted_cache_path(derived_root, pdf_path, source_root)
        existing_cache_path, cached = read_portable_cache(
            derived_root=derived_root,
            pdf_path=pdf_path,
            source_root=source_root,
            ocr=False,
        )
        if cached:
            migrated = False
            if cached.get("source_key") != portable_source_key(pdf_path, source_root):
                cached = {
                    **cached,
                    "source_path": str(pdf_path),
                    "source_key": portable_source_key(pdf_path, source_root),
                }
                migrated = True
            pages = cached.get("pages", [])
            if (existing_cache_path and existing_cache_path != cache_path) or not cache_path.exists() or migrated:
                write_json(cache_path, cached)
        else:
            pages = extract_pdf_pages(pdf_path, cache_path, source_root)
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
        for page in ocr_pages(derived_root, pdf_path, source_root):
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
    def cache_identity(path: Path, cached: Dict) -> Tuple[str, str]:
        source_name = Path(cached.get("source_path") or path.name).name
        return (cached.get("file_hash") or str(path), source_name)

    pages = 0
    chars = 0
    seen_text_caches = set()
    for path in (derived_root / "text").glob("*.json"):
        cached = read_json(path, {})
        cache_key = cache_identity(path, cached)
        if cache_key in seen_text_caches:
            continue
        seen_text_caches.add(cache_key)
        cached_pages = cached.get("pages", [])
        pages += len(cached_pages)
        chars += sum(len(clean(page.get("text"))) for page in cached_pages)
    ocr_pages_total = 0
    ocr_chars = 0
    seen_ocr_caches = set()
    for path in (derived_root / "text" / "ocr").glob("*.json"):
        cached = read_json(path, {})
        cache_key = cache_identity(path, cached)
        if cache_key in seen_ocr_caches:
            continue
        seen_ocr_caches.add(cache_key)
        cached_pages = [page for page in cached.get("pages", []) if not page.get("error")]
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
        "locations": conn.execute("SELECT count(*) FROM locations").fetchone()[0],
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
