#!/usr/bin/env python3
"""Assemble the Release 04 source root for the UFO indexer.

Unlike Release 03 (which shipped metadata-only), Release 04's raw PDFs, images,
and videos are already on disk, so this builder wires the local files in from the
start -- the indexer extracts native PDF text, OCR text, and video captions for
search -- while every public ``source_url`` still points at war.gov / DVIDS so
nothing is re-hosted.

  - PDFs / images:  local copy + https://www.war.gov/medialink/ufo/071026/release_04/...
  - Videos / audio: local mp4 + DVIDS public asset page (source_url) + cloudfront mp4
  - Thumbnails:     CSV "Modal Image" column (war.gov CDN), remote-only
  - Captions:       DVIDS SRT written to videos/captions/<video_id>.srt

Inputs (single payload produced by the browser scrape):
  DisclosureArchivePackage/release04_src/_staging/r4_payload.json
  DisclosureArchivePackage/release4/Documents/                 (14 PDFs + 3 JPGs)
  DisclosureArchivePackage/release4/uap_release04_videos_071026/ (23 DOD_<id>.mp4)

Outputs:
  DisclosureArchivePackage/release04_src/
    uap-csv.cdp.csv
    uap_download_manifest.json
    dvids_video_manifest.cdp.json
    documents/<file>.pdf|.jpg          (hardlinks; copy fallback)
    videos/{dvids}_{dod}.mp4           (hardlinks; copy fallback)
    videos/captions/{dvids}.srt

Stability: ``doc_id`` derives from row_number + title + release_type +
source_url + dvids_video_id (see common.CsvRecord.doc_id). Row order here is the
scrape order of the 7/10/26 tranche; keep it stable to keep record-page slugs.
"""
from __future__ import annotations

import csv
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
PKG = REPO_ROOT / "DisclosureArchivePackage"
SRC = PKG / "release04_src"
STAGING_PAYLOAD = SRC / "_staging" / "r4_payload.json"
RAW_DOCS = PKG / "release4" / "Documents"
RAW_VIDEOS = PKG / "release4" / "uap_release04_videos_071026"

OUT_CSV = SRC / "uap-csv.cdp.csv"
OUT_DOWNLOAD_MANIFEST = SRC / "uap_download_manifest.json"
OUT_VIDEO_MANIFEST = SRC / "dvids_video_manifest.cdp.json"
OUT_DOCS = SRC / "documents"
OUT_VIDEOS = SRC / "videos"
OUT_CAPTIONS = OUT_VIDEOS / "captions"


def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def clean(value: object) -> str:
    return "" if value is None else str(value).replace("\xa0", " ").strip()


def hardlink(src: Path, dst: Path) -> str:
    if dst.exists() or dst.is_symlink():
        try:
            dst.unlink()
        except OSError:
            pass
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def best_mp4_from_dvids(dvids: Dict) -> Dict:
    files = dvids.get("files") or []
    mp4s = [f for f in files if (f.get("type") or "").lower().startswith("video/")]
    if not mp4s:
        return {}

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
    for required in (STAGING_PAYLOAD, RAW_DOCS, RAW_VIDEOS):
        if not required.exists():
            fail(f"missing required input: {required}")

    payload = json.loads(STAGING_PAYLOAD.read_text(encoding="utf-8"))
    rows: List[Dict] = payload.get("rows") or []
    dvids_by_id: Dict[str, Dict] = payload.get("dvids") or {}
    captions_by_id: Dict[str, str] = payload.get("captions") or {}
    if not rows:
        fail("payload has no rows")

    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    OUT_VIDEOS.mkdir(parents=True, exist_ok=True)
    OUT_CAPTIONS.mkdir(parents=True, exist_ok=True)

    # --- Patch VID/AUD rows: source_url (PDF | Image Link) = DVIDS page URL --- #
    for row in rows:
        rt = (row.get("Type") or "").upper().strip()
        if rt in ("VID", "AUD"):
            vid = clean(row.get("DVIDS Video ID"))
            page = clean((dvids_by_id.get(vid) or {}).get("url"))
            if page and not clean(row.get("PDF | Image Link")):
                row["PDF | Image Link"] = page

    # --- Write CSV (17 named columns; indexer reads by name) ----------------- #
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

    raw_docs = {p.name: p for p in RAW_DOCS.iterdir() if p.is_file()}
    raw_vids = {p.name: p for p in RAW_VIDEOS.iterdir() if p.is_file() and p.suffix == ".mp4"}

    # --- Hardlink PDFs / images by basename of the CSV link ------------------ #
    link_methods = {"hardlink": 0, "copy": 0}
    doc_targets: Dict[int, str] = {}
    missing_docs: List[str] = []
    for index, row in enumerate(rows, start=1):
        rt = clean(row.get("Type")).upper()
        link = clean(row.get("PDF | Image Link"))
        if rt not in ("PDF", "IMG") or not link:
            continue
        fn = os.path.basename(link)
        src = raw_docs.get(fn)
        if not src:
            missing_docs.append(fn)
            continue
        method = hardlink(src, OUT_DOCS / fn)
        link_methods[method] += 1
        doc_targets[index] = f"documents/{fn}"
    print(
        f"Documents/images: linked {len(doc_targets)} "
        f"(hardlink={link_methods['hardlink']}, copy={link_methods['copy']}), "
        f"missing={len(missing_docs)}"
    )
    for m in missing_docs:
        print(f"    WARN: no local file for {m}")

    # --- Hardlink videos as videos/{dvids}_{dod}.mp4; write captions --------- #
    video_methods = {"hardlink": 0, "copy": 0}
    linked_videos = 0
    missing_videos: List[str] = []
    caption_count = 0
    for vid, dvids in dvids_by_id.items():
        if not vid:
            continue
        src_url = (best_mp4_from_dvids(dvids) or {}).get("src", "")
        m = re.search(r"(DOD_\d+)", src_url)
        dod = m.group(1) if m else ""
        if not dod:
            missing_videos.append(f"{vid} (no DOD id in mp4 src)")
        else:
            match = next((name for name in raw_vids if dod in name), None)
            if not match:
                missing_videos.append(f"{vid} ({dod})")
            else:
                method = hardlink(raw_vids[match], OUT_VIDEOS / f"{vid}_{dod}.mp4")
                video_methods[method] += 1
                linked_videos += 1
        srt = captions_by_id.get(vid)
        if srt and srt.strip():
            (OUT_CAPTIONS / f"{vid}.srt").write_text(srt, encoding="utf-8")
            caption_count += 1
    print(
        f"Videos: linked {linked_videos} "
        f"(hardlink={video_methods['hardlink']}, copy={video_methods['copy']}), "
        f"missing={len(missing_videos)}; captions written={caption_count}"
    )
    for m in missing_videos:
        print(f"    WARN: no local mp4 for {m}")

    # --- Download manifest (local target for docs/images; public url) -------- #
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
        target = doc_targets.get(index, "")

        if rt == "PDF" and link:
            entries.append({
                "row": index, "category": "document",
                "source_field": "PDF | Image Link", "type": "PDF",
                "target": target, "url": link,
                "title": title, "agency": agency, "release_date": rel_date,
                "incident_date": inc_date, "incident_location": inc_loc,
                "description": desc, "remote_only": not target,
            })
            doc_count += 1
        elif rt == "IMG" and link:
            entries.append({
                "row": index, "category": "image",
                "source_field": "PDF | Image Link", "type": "IMG",
                "target": target, "url": link,
                "title": title, "agency": agency, "release_date": rel_date,
                "incident_date": inc_date, "incident_location": inc_loc,
                "description": desc, "remote_only": not target,
            })
            image_count += 1

        if modal:
            entries.append({
                "row": index, "category": "thumbnail",
                "source_field": "Modal Image", "type": "Image",
                "target": "", "url": modal, "title": title, "remote_only": True,
            })
            thumb_count += 1

    download_manifest = {
        "source_page": "https://www.war.gov/UFO/release/04/",
        "csv": "uap-csv.cdp.csv",
        "rows": len(rows),
        "release": "release_04",
        "remote_only": False,
        "asset_url_pattern": payload.get("asset_url_pattern"),
        "entries": entries,
    }
    OUT_DOWNLOAD_MANIFEST.write_text(
        json.dumps(download_manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(
        f"Download manifest: {len(entries)} entries "
        f"(documents={doc_count}, images={image_count}, thumbnails={thumb_count}) "
        f"-> {OUT_DOWNLOAD_MANIFEST.relative_to(REPO_ROOT)}"
    )

    # --- DVIDS video manifest ----------------------------------------------- #
    row_by_vid: Dict[str, Dict] = {}
    for row in rows:
        vid = clean(row.get("DVIDS Video ID"))
        if vid:
            row_by_vid[vid] = row
    video_objects = [
        reshape_dvids(vid, dvids, row_by_vid.get(vid))
        for vid, dvids in dvids_by_id.items() if vid
    ]
    OUT_VIDEO_MANIFEST.write_text(
        json.dumps(video_objects, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"Video manifest: {len(video_objects)} objects -> {OUT_VIDEO_MANIFEST.relative_to(REPO_ROOT)}")

    print("\n=== Release 04 source build summary ===")
    print(f"  source root      : {SRC.relative_to(REPO_ROOT)}")
    print(f"  csv rows         : {len(rows)}")
    print(f"  local documents  : {len(list(OUT_DOCS.glob('*')))}")
    print(f"  local videos     : {len(list(OUT_VIDEOS.glob('*.mp4')))}")
    print(f"  captions         : {len(list(OUT_CAPTIONS.glob('*.srt')))}")
    print(f"  video objects    : {len(video_objects)}")
    print("\nIndex with:")
    print(f"  python -m ufo_indexer.index --source-root {SRC} --db indexes/uap_release_r4.sqlite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
