#!/usr/bin/env python3
"""Assemble the self-contained "Release 02" source root for the UFO indexer.

This builds ``DisclosureArchivePackage/release02_src/`` so the existing indexer
(``src/ufo_indexer/index.py``) can index it incrementally with::

    python -m ufo_indexer.index \
        --source-root DisclosureArchivePackage/release02_src \
        --db indexes/uap_release.sqlite

What the script does (idempotent, std-lib only):
  * Copies the staging CSV verbatim to ``uap-csv.cdp.csv`` so the per-row
    ``_row_number`` the indexer assigns (1-based DictReader enumeration) is
    stable and matches the manifest ``row`` fields.
  * Hardlinks the 6 Release 2 PDFs into ``documents/`` (copy fallback).
  * Hardlinks each VID/AUD record's local mp4 into
    ``videos/{dvids}_{asset_id}.mp4`` (copy fallback) so the indexer's
    ``find_video_path`` glob ``videos/{video_id}_*.mp4`` resolves it.
  * Copies any staged ``.srt`` caption files into ``videos/captions/``.
  * Copies any staged thumbnail images into ``thumbnails/``.
  * Writes ``uap_download_manifest.json`` ({"entries": [...]}) with one entry
    per CSV row that has a local document/thumbnail/image asset, using the
    EXACT field names index.py reads.
  * Writes ``dvids_video_manifest.cdp.json`` (a JSON LIST) mirroring the
    Release 1 per-video object shape, keyed by a top-level ``video_id``.

It reads, but never writes, the staging inputs, and never touches a SQLite DB.

================================================================================
Manifest field-name contract (verified against src/ufo_indexer/index.py and the
existing Release 1 manifest -- NOT guessed):

  Download manifest -- index.py::index_record reads entries with these keys:
      entry.get("target")    -> path relative to source_root  (index.py L472)
      entry.get("category")  -> "document" | "thumbnail" | "image"  (L474, L509)
      entry.get("url")       -> source URL stored on the asset   (L509)
  The whole entry dict is also stored verbatim as the asset metadata_json
  (add_asset(..., metadata=entry), L509), so we mirror the Release 1 / project
  shape exactly: row, category, source_field, type, target, url, title, agency,
  release_date, incident_date, incident_location, description,
  corrected_from_malformed_csv.

  NOTE: the task brief named these fields "kind / local_path / source_url /
  bytes". Those names do NOT appear anywhere in index.py or the real manifest;
  index.py uses category / target / url. We follow the code + real manifest.

  Video manifest -- common.py::video_by_id keys on v.get("video_id"); index.py
  reads video.get("best_mp4") (a dict; add_asset stores best_mp4["src"] via
  clean()... actually clean(video.get("best_mp4")) -> str(dict)), and
  video.get("description") / dvids_title / date for chunk text. We replicate the
  Release 1 object shape: video_id, rows, titles, dvids_title, description,
  date, duration, hls_url, image, thumbnail{url,width,height},
  best_mp4{src,type,height,width,size,bitrate}, all_mp4s[...], plus a
  source/original-file URL field (``url``) carrying the DVIDS public page link.
================================================================================
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #

# scripts/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
PKG = REPO_ROOT / "DisclosureArchivePackage"

STAGING = PKG / "release02_src" / "_staging"
STAGING_CSV = STAGING / "release02.csv"
STAGING_DVIDS = STAGING / "dvids_raw.json"
STAGING_CAPTIONS = STAGING / "captions"
STAGING_THUMBS = STAGING / "thumbnails"

DOC_BUNDLE = PKG / "release_02_document_bundle"
VIDEO_BUNDLE = PKG / "uap052226"

OUT_ROOT = PKG / "release02_src"
OUT_CSV = OUT_ROOT / "uap-csv.cdp.csv"
OUT_DOCS = OUT_ROOT / "documents"
OUT_VIDEOS = OUT_ROOT / "videos"
OUT_CAPTIONS = OUT_VIDEOS / "captions"
OUT_THUMBS = OUT_ROOT / "thumbnails"
OUT_DOWNLOAD_MANIFEST = OUT_ROOT / "uap_download_manifest.json"
OUT_VIDEO_MANIFEST = OUT_ROOT / "dvids_video_manifest.cdp.json"

# The 6 Release 2 PDFs (filenames as they exist in release_02_document_bundle).
RELEASE2_PDFS = [
    "DOW-UAP-D017_General_Correspondence_Of_Sandia.pdf",
    "CIA-UAP-D001_Intelligence_Information_Report_USSR_1973.pdf",
    "DOE-UAP-D001_PANTEX_Image.pdf",
    "DOE-UAP-D002_JamesTuck_Correspondence.pdf",
    "DOE-UAP-D003_Pajarito_Astronomers.pdf",
    "ODNI-UAP-D001_USPER_Narrative_Senior_USIC.pdf",
]


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def fail(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    print(f"ERROR: {msg}", file=sys.stderr)
    raise SystemExit(2)


def clean(value: object) -> str:
    """Mirror common.clean enough for CSV value reads / comparisons."""
    if value is None:
        return ""
    return str(value).replace("\xa0", " ").strip()


def ensure_dirs() -> None:
    for d in (OUT_ROOT, OUT_DOCS, OUT_VIDEOS, OUT_CAPTIONS, OUT_THUMBS):
        d.mkdir(parents=True, exist_ok=True)


def hardlink(src: Path, dst: Path) -> str:
    """Create a fresh hardlink from src -> dst; copy fallback. Idempotent.

    Returns "hardlink" or "copy" to report which path was taken.
    """
    if dst.exists() or dst.is_symlink():
        try:
            dst.unlink()
        except OSError:
            # Last resort: overwrite via copy below.
            pass
    try:
        os.link(src, dst)
        return "hardlink"
    except OSError:
        shutil.copy2(src, dst)
        return "copy"


def copy_file(src: Path, dst: Path) -> None:
    """Plain idempotent copy (captions/thumbnails are small)."""
    if dst.exists() or dst.is_symlink():
        try:
            dst.unlink()
        except OSError:
            pass
    shutil.copy2(src, dst)


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    """Replicate common.read_csv_rows row numbering (1-based DictReader)."""
    import csv

    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for index, row in enumerate(rows, start=1):
        row["_row_number"] = str(index)
    return rows


def find_local_video(asset_id: str) -> Optional[Path]:
    """Find the local mp4 whose filename contains the asset_id.

    Files look like: video_2605_DOD_111719752_DOD_111719752.mp4
    """
    if not asset_id:
        return None
    matches = sorted(VIDEO_BUNDLE.glob(f"*{asset_id}*.mp4"))
    return matches[0] if matches else None


# --------------------------------------------------------------------------- #
# Main build
# --------------------------------------------------------------------------- #

def main() -> int:
    # --- validate inputs exist ---------------------------------------------- #
    missing = []
    if not STAGING_CSV.exists():
        missing.append(str(STAGING_CSV))
    if not STAGING_DVIDS.exists():
        missing.append(str(STAGING_DVIDS))
    if not DOC_BUNDLE.exists():
        missing.append(str(DOC_BUNDLE))
    if not VIDEO_BUNDLE.exists():
        missing.append(str(VIDEO_BUNDLE))
    if missing:
        fail(
            "required input(s) missing (produced by a prior process):\n  "
            + "\n  ".join(missing)
        )

    ensure_dirs()

    # --- 1. copy staging CSV verbatim --------------------------------------- #
    shutil.copy2(STAGING_CSV, OUT_CSV)
    csv_rows = read_csv_rows(OUT_CSV)
    print(f"CSV: copied {STAGING_CSV.name} -> {OUT_CSV.relative_to(REPO_ROOT)} "
          f"({len(csv_rows)} data rows)")

    # Build lookup: title -> row_number, and (Type, link basename) helpers.
    # We map PDF rows by matching the PDF filename against the CSV link cell.
    def row_link(row: Dict[str, str]) -> str:
        return clean(row.get("PDF | Image Link"))

    def row_modal(row: Dict[str, str]) -> str:
        return clean(row.get("Modal Image"))

    # --- 2. hardlink the 6 PDFs into documents/ ----------------------------- #
    doc_link_methods = {"hardlink": 0, "copy": 0}
    pdf_present: List[str] = []
    for fname in RELEASE2_PDFS:
        src = DOC_BUNDLE / fname
        if not src.exists():
            print(f"  WARN: document not found, skipping: {src}")
            continue
        method = hardlink(src, OUT_DOCS / fname)
        doc_link_methods[method] += 1
        pdf_present.append(fname)
    print(f"Documents: linked {len(pdf_present)}/{len(RELEASE2_PDFS)} PDFs "
          f"(hardlink={doc_link_methods['hardlink']}, copy={doc_link_methods['copy']})")

    # --- 3. load dvids_raw.json --------------------------------------------- #
    dvids_records = json.loads(STAGING_DVIDS.read_text(encoding="utf-8"))
    if not isinstance(dvids_records, list):
        fail("dvids_raw.json must be a JSON array of records")

    # --- 4. hardlink videos -> videos/{dvids}_{asset_id}.mp4 ---------------- #
    # De-duplicate by destination name so shared assets (e.g. two PR057 records
    # sharing DOD_111719752 / dvids 1007720) only link once.
    video_link_methods = {"hardlink": 0, "copy": 0}
    linked_video_dests: Dict[str, Path] = {}
    missing_videos: List[str] = []
    for rec in dvids_records:
        dvids = clean(rec.get("dvids"))
        asset_id = clean(rec.get("asset_id"))
        if not dvids or not asset_id:
            print(f"  WARN: record missing dvids/asset_id: "
                  f"war_id={rec.get('war_id')!r}")
            continue
        dest_name = f"{dvids}_{asset_id}.mp4"
        dest = OUT_VIDEOS / dest_name
        if dest_name in linked_video_dests:
            continue  # already linked (shared asset / duplicate record)
        src = find_local_video(asset_id)
        if not src:
            missing_videos.append(f"{rec.get('war_id')} (asset {asset_id})")
            continue
        method = hardlink(src, dest)
        video_link_methods[method] += 1
        linked_video_dests[dest_name] = dest
    print(f"Videos: linked {len(linked_video_dests)} unique mp4(s) "
          f"(hardlink={video_link_methods['hardlink']}, "
          f"copy={video_link_methods['copy']}); "
          f"missing={len(missing_videos)}")
    if missing_videos:
        for m in missing_videos:
            print(f"    WARN: no local mp4 for {m}")

    # --- 5. copy staged captions -> videos/captions/{dvids}.srt ------------- #
    captions_copied = 0
    if STAGING_CAPTIONS.exists():
        for src in sorted(STAGING_CAPTIONS.glob("*.srt")):
            copy_file(src, OUT_CAPTIONS / src.name)
            captions_copied += 1
    print(f"Captions: copied {captions_copied} .srt file(s)")

    # --- 6. copy staged thumbnails -> thumbnails/ --------------------------- #
    thumbs_copied = 0
    staged_thumb_names: List[str] = []
    if STAGING_THUMBS.exists():
        for src in sorted(STAGING_THUMBS.iterdir()):
            if not src.is_file():
                continue
            copy_file(src, OUT_THUMBS / src.name)
            staged_thumb_names.append(src.name)
            thumbs_copied += 1
    print(f"Thumbnails: copied {thumbs_copied} file(s)")

    # --- 7. build uap_download_manifest.json -------------------------------- #
    # One entry per CSV row that owns a local document/thumbnail/image.
    # Field names mirror index.py reads + the Release 1 / project manifest shape.
    entries: List[Dict] = []

    # Map each present PDF to its CSV row by matching the link cell basename.
    # CSV "PDF | Image Link" ends with the filename (per fix_release2_metadata.py
    # the link is .../documents/<fname>); fall back to substring match on fname.
    def find_row_for_pdf(fname: str) -> Optional[Dict[str, str]]:
        for row in csv_rows:
            link = row_link(row)
            if link.endswith(fname) or fname in link:
                return row
        # Fallback: match by stem appearing in Title.
        stem = fname[:-4]
        for row in csv_rows:
            if stem in clean(row.get("Title")):
                return row
        return None

    doc_entry_count = 0
    thumb_entry_count = 0
    unmatched_pdfs: List[str] = []
    for fname in pdf_present:
        row = find_row_for_pdf(fname)
        if row is None:
            unmatched_pdfs.append(fname)
            continue
        row_no = int(row.get("_row_number", "0") or 0)
        link = row_link(row)
        modal = row_modal(row)
        entries.append({
            "row": row_no,
            "category": "document",
            "source_field": "PDF | Image Link",
            "type": clean(row.get("Type")) or "PDF",
            "target": f"documents/{fname}",
            "url": link,
            "title": clean(row.get("Title")),
            "agency": clean(row.get("Agency")),
            "release_date": clean(row.get("Release Date")),
            "incident_date": clean(row.get("Incident Date")),
            "incident_location": clean(row.get("Incident Location")),
            "description": clean(row.get("Description Blurb")),
            "corrected_from_malformed_csv": False,
        })
        doc_entry_count += 1

        # Add a thumbnail entry when a staged thumbnail exists for this doc.
        stem = fname[:-4]
        thumb_match = None
        for tname in staged_thumb_names:
            if Path(tname).stem == stem or stem in tname:
                thumb_match = tname
                break
        if thumb_match:
            entries.append({
                "row": row_no,
                "category": "thumbnail",
                "source_field": "Modal Image",
                "type": "Image",
                "target": f"thumbnails/{thumb_match}",
                "url": modal,
                "title": stem,
                "corrected_from_malformed_csv": False,
            })
            thumb_entry_count += 1

    if unmatched_pdfs:
        for f in unmatched_pdfs:
            print(f"    WARN: no CSV row matched PDF, omitted from manifest: {f}")

    download_manifest = {
        "source_page": "https://www.war.gov/UFO/",
        "csv": "uap-csv.cdp.csv",
        "rows": len(csv_rows),
        "release": "release_02",
        "entries": entries,
    }
    OUT_DOWNLOAD_MANIFEST.write_text(
        json.dumps(download_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Download manifest: {len(entries)} entries "
          f"(documents={doc_entry_count}, thumbnails={thumb_entry_count}) "
          f"-> {OUT_DOWNLOAD_MANIFEST.relative_to(REPO_ROOT)}")

    # --- 8. build dvids_video_manifest.cdp.json (JSON LIST) ----------------- #
    # Mirror the Release 1 per-video object shape; key on top-level video_id.
    video_objects: List[Dict] = []
    for rec in dvids_records:
        dvids = clean(rec.get("dvids"))
        if not dvids:
            print(f"  WARN: dvids record missing 'dvids', skipped in video "
                  f"manifest: war_id={rec.get('war_id')!r}")
            continue

        # best_mp4: prefer the explicit mp4_src; enrich from all_mp4s when the
        # matching entry is found, else fall back to mp4_size.
        all_mp4s = rec.get("all_mp4s") or []
        best_src = clean(rec.get("mp4_src"))
        best_obj: Dict = {}
        for m in all_mp4s:
            if clean(m.get("src")) == best_src:
                best_obj = {
                    "src": clean(m.get("src")),
                    "type": clean(m.get("type")) or "video/mp4",
                    "height": m.get("height"),
                    "width": m.get("width"),
                    "size": m.get("size"),
                    "bitrate": m.get("bitrate", 0),
                }
                break
        if not best_obj:
            best_obj = {
                "src": best_src,
                "type": "video/mp4",
                "height": None,
                "width": None,
                "size": rec.get("mp4_size"),
                "bitrate": 0,
            }

        thumbnail_url = clean(rec.get("thumbnail"))
        video_objects.append({
            "video_id": dvids,
            "war_id": clean(rec.get("war_id")),
            "asset_id": clean(rec.get("asset_id")),
            "type": clean(rec.get("type")),
            "titles": [t for t in [clean(rec.get("war_title"))] if t],
            "dvids_title": clean(rec.get("dvids_title")),
            "description": rec.get("description") or "",
            "date": clean(rec.get("date")),
            "duration": rec.get("duration"),
            "agency": clean(rec.get("agency")),
            "incident_date": clean(rec.get("incident_date")),
            "incident_location": clean(rec.get("incident_location")),
            "unit_name": clean(rec.get("unit_name")),
            "branch": clean(rec.get("branch")),
            "virin": clean(rec.get("virin")),
            "hls_url": clean(rec.get("hls_url")),
            "image": clean(rec.get("image")),
            "thumbnail": {"url": thumbnail_url, "width": 720, "height": 0},
            "best_mp4": best_obj,
            "all_mp4s": all_mp4s,
            # Source / original-file public page (the DVIDS "original file" link).
            "url": clean(rec.get("url")),
            "source_url": clean(rec.get("url")),
        })

    OUT_VIDEO_MANIFEST.write_text(
        json.dumps(video_objects, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Video manifest: {len(video_objects)} objects "
          f"-> {OUT_VIDEO_MANIFEST.relative_to(REPO_ROOT)}")

    # --- summary ------------------------------------------------------------ #
    print("\n=== Release 02 source build summary ===")
    print(f"  source root      : {OUT_ROOT.relative_to(REPO_ROOT)}")
    print(f"  csv rows         : {len(csv_rows)}")
    print(f"  documents linked : {len(pdf_present)}")
    print(f"  videos linked    : {len(linked_video_dests)} "
          f"(missing {len(missing_videos)})")
    print(f"  captions copied  : {captions_copied}")
    print(f"  thumbnails copied: {thumbs_copied}")
    print(f"  download entries : {len(entries)} "
          f"(doc={doc_entry_count}, thumb={thumb_entry_count})")
    print(f"  video objects    : {len(video_objects)}")
    print("\nIndex with:")
    print("  python -m ufo_indexer.index "
          f"--source-root {OUT_ROOT} --db indexes/uap_release.sqlite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
