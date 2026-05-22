"""Set the original-file (DVIDS public page) link on each Release 02 video/audio
row, and remove the previously-indexed media docs so they can be cleanly
re-indexed with a populated source_url.

Run BEFORE re-running build_release02_source.py + the indexer.
"""
from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "DisclosureArchivePackage" / "release02_src" / "_staging"
CSV_PATH = STAGING / "release02.csv"
DVIDS_PATH = STAGING / "dvids_raw.json"
DB = ROOT / "indexes" / "uap_release.sqlite"


def fix_csv() -> int:
    url_by_dvids = {
        str(r["dvids"]): (r.get("url") or "").strip()
        for r in json.loads(DVIDS_PATH.read_text(encoding="utf-8"))
    }
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        fields = reader.fieldnames
        rows = list(reader)
    filled = 0
    for row in rows:
        if (row.get("Type") or "").strip() in ("VID", "AUD"):
            vid = (row.get("DVIDS Video ID") or "").strip()
            url = url_by_dvids.get(vid, "")
            if url:
                row["PDF | Image Link"] = url
                filled += 1
    with CSV_PATH.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return filled


def delete_media_docs() -> int:
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys=ON")
    doc_ids = [
        r[0]
        for r in conn.execute(
            "SELECT doc_id FROM documents WHERE release_date='5/22/26' "
            "AND release_type IN ('VID','AUD')"
        ).fetchall()
    ]
    if doc_ids:
        marks = ",".join("?" * len(doc_ids))
        conn.execute(f"DELETE FROM chunks_fts WHERE doc_id IN ({marks})", doc_ids)
        conn.execute(f"DELETE FROM documents WHERE doc_id IN ({marks})", doc_ids)
        conn.commit()
    conn.close()
    return len(doc_ids)


if __name__ == "__main__":
    filled = fix_csv()
    print(f"CSV: set DVIDS source link on {filled} video/audio rows")
    deleted = delete_media_docs()
    print(f"DB: deleted {deleted} previously-indexed media docs (cascade assets/chunks/locations)")
