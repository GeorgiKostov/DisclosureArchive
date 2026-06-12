#!/usr/bin/env python3
"""Assemble the Release 03 "metadata-only" source root for the UFO indexer.

Unlike Release 02 (which downloaded local PDFs/videos/thumbs and hardlinked
them into a self-contained source root), Release 03 is indexed straight off
the public source URLs:

  - PDFs / images:  https://www.war.gov/medialink/ufo/061226/release_03/...
  - Videos / audio: DVIDS public asset pages + cloudfront MP4 URLs
  - Thumbnails:     CSV "Modal Image" column (war.gov CDN)

Nothing is downloaded. The indexer's local-path branches (PDF text extraction,
OCR, file-hash content addressing of mp4s) are skipped because every manifest
entry has an empty ``target``. Each indexed record still gets:

  - a ``documents`` row with ``source_url`` populated from the CSV link
  - one ``assets`` row per entry with ``local_path=''`` and ``source_url`` set
  - a ``metadata`` chunk (CSV title/agency/date/location/blurb) and, for
    DVIDS-backed records, a ``video_metadata`` chunk (DVIDS title/date/desc)
  - incident-location geocoding and embeddings as usual

Inputs (single payload produced by the browser-scrape):
  DisclosureArchivePackage/release03_src/_staging/r3_payload.json

Outputs:
  DisclosureArchivePackage/release03_src/
    uap-csv.cdp.csv
    uap_download_manifest.json
    dvids_video_manifest.cdp.json
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
PKG = REPO_ROOT / "DisclosureArchivePackage"
SRC = PKG / "release03_src"
STAGING_PAYLOAD = SRC / "_staging" / "r3_payload.json"
OUT_CSV = SRC / "uap-csv.cdp.csv"
OUT_DOWNLOAD_MANIFEST = SRC / "uap_download_manifest.json"
OUT_VIDEO_MANIFEST = SRC / "dvids_video_manifest.cdp.json"


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def clean(value: object) -> str:
    if value is None:
        return ""
    return str(value).replace("\xa0", " ").strip()


def best_mp4_from_dvids(dvids: Dict) -> Dict:
    files = dvids.get("files") or []
    mp4s = [f for f in files if (f.get("type") or "").lower().startswith("video/")]
    if not mp4s:
        return {}
    # Highest pixel area
    def area(f: Dict) -> int:
        try:
            return int(f.get("width") or 0) * int(f.get("height") or 0)
        except Exception:
            return 0
    mp4s.sort(key=area, reverse=True)
    f = mp4s[0]
    return {
        "src": clean(f.get("src")),
        "type": clean(f.get("type")) or "video/mp4",
        "height": f.get("height"),
        "width": f.get("width"),
        "size": f.get("size"),
        "bitrate": f.get("bitrate", 0),
    }


def reshape_dvids(vid: str, dvids: Dict, row: Optional[Dict]) -> Dict:
    thumb = dvids.get("thumbnail") or {}
    return {
        "video_id": vid,
        "asset_id": clean(dvids.get("id")),
        "type": clean(dvids.get("type")),
        "titles": [t for t in [clean((row or {}).get("Title"))] if t],
        "dvids_title": clean(dvids.get("title")),
        "description": clean(dvids.get("description")),
        "date": clean(dvids.get("date")),
        "duration": dvids.get("duration"),
        "agency": clean((row or {}).get("Agency")),
        "incident_date": clean((row or {}).get("Incident Date")),
        "incident_location": clean((row or {}).get("Incident Location")),
        "unit_name": clean(dvids.get("unit_name")),
        "branch": clean(dvids.get("branch")),
        "virin": clean(dvids.get("virin")),
        "hls_url": clean(dvids.get("hls_url")),
        "image": clean(dvids.get("image")),
        "thumbnail": {
            "url": clean(thumb.get("url")),
            "width": thumb.get("width") or 0,
            "height": thumb.get("height") or 0,
        },
        "best_mp4": best_mp4_from_dvids(dvids),
        "all_mp4s": dvids.get("files") or [],
        "url": clean(dvids.get("url")),
        "source_url": clean(dvids.get("url")),
    }


def main() -> int:
    if not STAGING_PAYLOAD.exists():
        fail(f"missing staging payload: {STAGING_PAYLOAD}")
    payload = json.loads(STAGING_PAYLOAD.read_text(encoding="utf-8"))
    rows: List[Dict] = payload.get("rows") or []
    dvids_by_id: Dict[str, Dict] = payload.get("dvids") or {}
    if not rows:
        fail("payload has no rows")

    SRC.mkdir(parents=True, exist_ok=True)

    # --- Patch VID/AUD rows: populate `PDF | Image Link` with DVIDS page URL ---
    # The indexer derives `doc_id` from row_number + title + Type + source_url +
    # dvids_video_id. Putting the DVIDS page link here BEFORE indexing makes the
    # public "Government source" link work and locks the doc_id permanently.
    for row in rows:
        rt = (row.get("Type") or "").upper().strip()
        if rt in ("VID", "AUD"):
            vid = clean(row.get("DVIDS Video ID"))
            dvids = dvids_by_id.get(vid) or {}
            page = clean(dvids.get("url"))
            if page and not clean(row.get("PDF | Image Link")):
                row["PDF | Image Link"] = page

    # --- Write the CSV in the exact column order the indexer expects ---
    # Use the 17 named columns from the live feed; ignore the trailing empty
    # padding headers. The indexer reads by name, so column order is only for
    # human readability.
    columns = [
        "Featured", "Redaction", "Release Date", "Title", "Type",
        "Video Pairing", "PDF Pairing", "Description Blurb",
        "DVIDS Video ID", "Video Title", "Agency",
        "Incident Date", "Incident Location",
        "PDF | Image Link", "Modal Image", "Image Alt Text", "Image VIRIN",
    ]
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})
    print(f"CSV: wrote {len(rows)} rows -> {OUT_CSV.relative_to(REPO_ROOT)}")

    # --- Build the download manifest ---
    # One entry per row that has a CSV link or a Modal Image. `target` is empty
    # so the indexer skips local-file extraction; `url` is the public source.
    entries: List[Dict] = []
    doc_count = thumb_count = image_count = 0
    for index, row in enumerate(rows, start=1):
        rt = (row.get("Type") or "").upper().strip()
        link = clean(row.get("PDF | Image Link"))
        modal = clean(row.get("Modal Image"))
        title = clean(row.get("Title"))
        agency = clean(row.get("Agency"))
        rel_date = clean(row.get("Release Date"))
        inc_date = clean(row.get("Incident Date"))
        inc_loc = clean(row.get("Incident Location"))
        desc = clean(row.get("Description Blurb"))

        if rt == "PDF" and link:
            entries.append({
                "row": index,
                "category": "document",
                "source_field": "PDF | Image Link",
                "type": "PDF",
                "target": "",
                "url": link,
                "title": title, "agency": agency,
                "release_date": rel_date,
                "incident_date": inc_date, "incident_location": inc_loc,
                "description": desc,
                "remote_only": True,
            })
            doc_count += 1
        elif rt == "IMG" and link:
            entries.append({
                "row": index,
                "category": "image",
                "source_field": "PDF | Image Link",
                "type": "IMG",
                "target": "",
                "url": link,
                "title": title, "agency": agency,
                "release_date": rel_date,
                "incident_date": inc_date, "incident_location": inc_loc,
                "description": desc,
                "remote_only": True,
            })
            image_count += 1
        # VID/AUD rows: no document manifest entry needed; the video manifest
        # carries the playable URL, and `documents.source_url` already gets the
        # DVIDS page URL from the patched CSV link above.

        if modal:
            entries.append({
                "row": index,
                "category": "thumbnail",
                "source_field": "Modal Image",
                "type": "Image",
                "target": "",
                "url": modal,
                "title": title,
                "remote_only": True,
            })
            thumb_count += 1

    download_manifest = {
        "source_page": "https://www.war.gov/UFO/",
        "csv": "uap-csv.cdp.csv",
        "rows": len(rows),
        "release": "release_03",
        "remote_only": True,
        "asset_url_pattern": payload.get("asset_url_pattern"),
        "entries": entries,
    }
    OUT_DOWNLOAD_MANIFEST.write_text(
        json.dumps(download_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Download manifest: {len(entries)} entries "
        f"(documents={doc_count}, images={image_count}, thumbnails={thumb_count}) "
        f"-> {OUT_DOWNLOAD_MANIFEST.relative_to(REPO_ROOT)}"
    )

    # --- Build the DVIDS video manifest (a JSON list) ---
    # The indexer reads description, dvids_title, date, and best_mp4 from each
    # object; common.video_by_id keys on top-level video_id.
    video_objects: List[Dict] = []
    # Map row by dvids_video_id for the reshape's metadata cross-link
    row_by_vid: Dict[str, Dict] = {}
    for row in rows:
        vid = clean(row.get("DVIDS Video ID"))
        if vid:
            row_by_vid[vid] = row
    for vid, dvids in dvids_by_id.items():
        if not vid:
            continue
        video_objects.append(reshape_dvids(vid, dvids, row_by_vid.get(vid)))
    OUT_VIDEO_MANIFEST.write_text(
        json.dumps(video_objects, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        f"Video manifest: {len(video_objects)} objects "
        f"-> {OUT_VIDEO_MANIFEST.relative_to(REPO_ROOT)}"
    )

    print("\n=== Release 03 (metadata-only) source build summary ===")
    print(f"  source root      : {SRC.relative_to(REPO_ROOT)}")
    print(f"  csv rows         : {len(rows)}")
    print(f"  download entries : {len(entries)}")
    print(f"  video objects    : {len(video_objects)}")
    print(f"  local binaries   : 0 (intentional, remote-only ingest)")
    print("\nIndex with:")
    print(
        "  python -m ufo_indexer.index "
        f"--source-root {SRC} --db indexes/uap_release.sqlite"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
