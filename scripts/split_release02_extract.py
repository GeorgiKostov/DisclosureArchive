"""Split the browser-captured Release 02 extract into the staging files the
source-root builder expects. One-off bridge step.

Reads:  DisclosureArchivePackage/release02_src/_staging/release02_extract.json
Writes: release02.csv, dvids_raw.json, captions/{dvids}.srt
"""
from __future__ import annotations

import json
from pathlib import Path

STAGING = Path(__file__).resolve().parent.parent / "DisclosureArchivePackage" / "release02_src" / "_staging"


def main() -> None:
    extract = json.loads((STAGING / "release02_extract.json").read_text(encoding="utf-8"))

    csv_text = extract["csv"]
    (STAGING / "release02.csv").write_text(csv_text, encoding="utf-8", newline="")

    dvids = extract["dvids"]
    captions_dir = STAGING / "captions"
    captions_dir.mkdir(exist_ok=True)

    caption_count = 0
    cleaned = []
    for rec in dvids:
        caption = rec.pop("caption", "") or ""
        if caption.strip():
            (captions_dir / f"{rec['dvids']}.srt").write_text(caption, encoding="utf-8")
            caption_count += 1
        cleaned.append(rec)

    (STAGING / "dvids_raw.json").write_text(json.dumps(cleaned, indent=2), encoding="utf-8")

    print(f"csv rows (excl header): {csv_text.count(chr(10).join([]))}")
    print(f"release02.csv bytes: {(STAGING / 'release02.csv').stat().st_size}")
    print(f"dvids records: {len(cleaned)}")
    print(f"captions written: {caption_count}")


if __name__ == "__main__":
    main()
