from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional


DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
DEFAULT_DIM = 384


def clean(value: object) -> str:
    if value is None:
        return ""
    text = str(value).replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def sha1_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for index, row in enumerate(rows, start=1):
        row["_row_number"] = str(index)
        for key, value in list(row.items()):
            row[key] = clean(value)
    return rows


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def words(text: str) -> List[str]:
    return re.findall(r"\S+", text)


def chunk_text(text: str, *, max_words: int = 220, overlap_words: int = 45) -> Iterator[str]:
    parts = words(clean(text))
    if not parts:
        return
    if len(parts) <= max_words:
        yield " ".join(parts)
        return
    step = max(1, max_words - overlap_words)
    for start in range(0, len(parts), step):
        window = parts[start : start + max_words]
        if len(window) < 35 and start:
            break
        yield " ".join(window)


@dataclass(frozen=True)
class CsvRecord:
    row_number: int
    title: str
    release_type: str
    agency: str
    release_date: str
    incident_date: str
    incident_location: str
    description: str
    source_url: str
    modal_image_url: str
    dvids_video_id: str

    @property
    def doc_id(self) -> str:
        seed = "|".join(
            [
                str(self.row_number),
                self.title,
                self.release_type,
                self.source_url,
                self.dvids_video_id,
            ]
        )
        return sha1_text(seed)[:16]


def csv_record(row: Dict[str, str]) -> CsvRecord:
    return CsvRecord(
        row_number=int(row.get("_row_number", "0") or 0),
        title=clean(row.get("Title")),
        release_type=clean(row.get("Type")),
        agency=clean(row.get("Agency")),
        release_date=clean(row.get("Release Date")),
        incident_date=clean(row.get("Incident Date")),
        incident_location=clean(row.get("Incident Location")),
        description=clean(row.get("Description Blurb")),
        source_url=clean(row.get("PDF | Image Link")),
        modal_image_url=clean(row.get("Modal Image")),
        dvids_video_id=clean(row.get("DVIDS Video ID")),
    )


def manifest_entries_by_row(manifest: Dict) -> Dict[int, List[Dict]]:
    by_row: Dict[int, List[Dict]] = {}
    for entry in manifest.get("entries", []):
        row = int(entry.get("row") or 0)
        by_row.setdefault(row, []).append(entry)
    return by_row


def video_by_id(video_manifest: List[Dict]) -> Dict[str, Dict]:
    return {clean(v.get("video_id")): v for v in video_manifest if clean(v.get("video_id"))}
