#!/usr/bin/env python3
"""Merge the Release 04 metadata-only export into the live (gh-pages) site.

We don't have R1/R2 raw data on this Mac, so we can't index R1+R2+R4 into a
single SQLite DB and run the normal export. Instead this script:

  1. Starts from a checkout of the live gh-pages site (R1+R2).
  2. Loads its data/documents.json (R1+R2 records + featured highlights).
  3. Loads the R4-only export's data/documents.json (R4 records + R4 featured).
  4. Writes a merged data/documents.json with all docs and the new
     RELEASE_GROUPS (release-4, -2, -1).
  5. Drops every R4 records/<slug>-<id>.html into the live records/ directory.
  6. Appends R4 record URLs to sitemap.xml.
  7. Rewrites the JSON-LD itemListElement in index.html to add R4 highlights
     ALONGSIDE the existing R1/R2 ones, and updates the variableMeasured count.

Inputs (positional):
  live_dir       path to the live gh-pages checkout (read)
  r4_only_dir    path to public_site_r4only/ (read)
  out_dir        path where the merged site is written (created/cleared)
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List
from html import escape as html_escape
from urllib.parse import quote


def load(p: Path) -> Dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main(live_dir: Path, r4_dir: Path, out_dir: Path) -> int:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(live_dir, out_dir, symlinks=False)
    print(f"copied live tree to {out_dir}")

    # --- merge documents.json ------------------------------------------------ #
    live = load(out_dir / "data" / "documents.json")
    r4 = load(r4_dir / "data" / "documents.json")

    # Use the new RELEASE_GROUPS from the R4 export (already has release-4, -2, -1).
    merged_groups = r4["release_groups"]
    print(f"release_groups: {[g['key'] for g in merged_groups]}")

    # Documents: union by doc_id (R4 wins on conflict, though there shouldn't be any).
    by_id = {d["doc_id"]: d for d in live["documents"]}
    r4_only_added = 0
    for d in r4["documents"]:
        if d["doc_id"] not in by_id:
            r4_only_added += 1
        by_id[d["doc_id"]] = d
    merged_docs = list(by_id.values())
    print(f"documents: live={len(live['documents'])} + R4-new={r4_only_added} = merged={len(merged_docs)}")

    # Featured: keep the live order, then append release-4 entries from R4 export.
    # Filter R4 featured to release-4 only so the accidental "Sary Shagan" R2
    # match in the R4-only export doesn't double-add an R2 highlight.
    live_featured = live.get("featured_documents", [])
    r4_featured = [f for f in r4.get("featured_documents", []) if f.get("release") == "release-4"]
    # Avoid duplicates by doc_id.
    seen = {f["doc_id"] for f in live_featured}
    merged_featured = list(live_featured) + [f for f in r4_featured if f["doc_id"] not in seen]
    print(f"featured: live={len(live_featured)} + R4-new={sum(1 for f in r4_featured if f['doc_id'] not in seen)} = merged={len(merged_featured)}")

    merged = {
        "schema": r4.get("schema") or live.get("schema"),
        "generated_at": r4.get("generated_at") or live.get("generated_at"),
        "document_count": len(merged_docs),
        "release_groups": merged_groups,
        "featured_documents": merged_featured,
        "documents": merged_docs,
    }
    (out_dir / "data" / "documents.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote merged documents.json ({len(merged_docs)} docs, {len(merged_featured)} featured)")

    # --- copy R4 per-record HTML pages -------------------------------------- #
    r4_records = r4_dir / "records"
    live_records = out_dir / "records"
    r4_record_paths: List[str] = []
    copied = 0
    for src in sorted(r4_records.iterdir()):
        if not src.is_file() or not src.name.endswith(".html"):
            continue
        # Skip the records/ hub index file from the r4-only export; the live
        # site's own hub already exists and is wider.
        if src.name == "index.html":
            continue
        dst = live_records / src.name
        if dst.exists():
            # Same slug already on live site (e.g. CIA-UAP-011 "Sary Shagan"
            # exists in both). Prefer the live one; skip overwriting.
            continue
        shutil.copy2(src, dst)
        r4_record_paths.append(f"records/{src.name}")
        copied += 1
    print(f"copied {copied} R4 record HTML pages to {live_records.relative_to(out_dir.parent)}")

    # Regenerate the records/ hub from the R4 export so it covers all 298 docs,
    # not just the live R1+R2 set. The hub is small, deterministic, and built
    # from the merged JSON at runtime anyway; we just copy the R4-export hub.
    r4_hub = r4_records / "index.html"
    if r4_hub.exists():
        # The R4-only hub only lists 72 docs. We'd rather keep the live hub
        # which lists 226 docs and will be re-rendered next full export. So
        # leave the live hub in place. (Per-record SEO still works via the
        # records/<slug>.html pages, which is what matters for crawlers.)
        pass

    # --- merge sitemap.xml -------------------------------------------------- #
    sitemap_path = out_dir / "sitemap.xml"
    if sitemap_path.exists() and r4_record_paths:
        sitemap = sitemap_path.read_text(encoding="utf-8")
        # Build new <url> blocks matching the live shape. Live uses:
        #   <url><loc>https://disclosurearchive.org/records/<file></loc>
        #        <lastmod>YYYY-MM-DD</lastmod></url>
        last_mod_match = re.search(r"<lastmod>([^<]+)</lastmod>", sitemap)
        lastmod = last_mod_match.group(1) if last_mod_match else "2026-06-12"
        new_blocks = []
        for rel in r4_record_paths:
            new_blocks.append(
                f"  <url>\n    <loc>https://disclosurearchive.org/{rel}</loc>\n"
                f"    <lastmod>{lastmod}</lastmod>\n  </url>"
            )
        new_block = "\n".join(new_blocks) + "\n"
        sitemap = sitemap.replace("</urlset>", new_block + "</urlset>")
        sitemap_path.write_text(sitemap, encoding="utf-8")
        print(f"appended {len(r4_record_paths)} URLs to sitemap.xml")

    # --- patch index.html: variableMeasured count + JSON-LD highlights ------ #
    index_path = out_dir / "index.html"
    if index_path.exists():
        index_html = index_path.read_text(encoding="utf-8")
        # 1. variableMeasured "<n> public records"
        index_html = re.sub(
            r'"variableMeasured":"\d+ public records"',
            f'"variableMeasured":"{len(merged_docs)} public records"',
            index_html,
        )
        # 2. JSON-LD ItemList: append the R4 featured items to the highlights
        #    array. We do a targeted text patch rather than full JSON-parse to
        #    avoid disturbing the rest of the JSON-LD graph.
        def jsonld_item(position: int, name: str, description: str) -> str:
            return json.dumps(
                {
                    "@type": "ListItem",
                    "position": position,
                    "url": f"https://disclosurearchive.org/#search?q={quote(name, safe='')}",
                    "name": name,
                    "description": description,
                },
                ensure_ascii=False,
            )

        # Find the highlights itemListElement and inject R4 entries before its
        # closing bracket. The live JSON-LD uses a single-line dump.
        marker = '"@id":"https://disclosurearchive.org/#highlights"'
        if marker in index_html:
            start = index_html.find(marker)
            arr_open = index_html.find('"itemListElement":[', start)
            if arr_open != -1:
                # Find the matching ] for this array
                depth = 0
                i = arr_open + len('"itemListElement":')
                close_idx = -1
                while i < len(index_html):
                    ch = index_html[i]
                    if ch == "[":
                        depth += 1
                    elif ch == "]":
                        depth -= 1
                        if depth == 0:
                            close_idx = i
                            break
                    elif ch == '"':
                        # skip strings (with escapes)
                        i += 1
                        while i < len(index_html) and index_html[i] != '"':
                            if index_html[i] == "\\":
                                i += 1
                            i += 1
                    i += 1
                if close_idx != -1:
                    # Count existing items to choose starting position.
                    existing_count = index_html.count('"@type":"ListItem"', arr_open, close_idx)
                    new_items = []
                    for offset, f in enumerate(r4_featured, start=1):
                        snippet = (f.get("summary") or "")[:500]
                        new_items.append(
                            jsonld_item(existing_count + offset, f.get("title") or "", snippet)
                        )
                    addition = "," + ",".join(new_items)
                    index_html = index_html[:close_idx] + addition + index_html[close_idx:]
                    print(f"injected {len(r4_featured)} R4 highlights into JSON-LD")
        index_path.write_text(index_html, encoding="utf-8")

    # --- guardrail: no path leaks ------------------------------------------- #
    leaks = []
    txt = (out_dir / "data" / "documents.json").read_text(encoding="utf-8")
    for token in ("DisclosureArchivePackage", "derived/", "indexes/"):
        if token in txt:
            leaks.append(token)
    if leaks:
        print(f"WARNING: leak tokens in merged documents.json: {leaks}", file=sys.stderr)

    print("\n=== merge complete ===")
    print(f"output: {out_dir}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("usage: merge_release04_into_live.py <live_dir> <r4_only_dir> <out_dir>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])))
