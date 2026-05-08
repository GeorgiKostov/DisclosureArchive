# DisclosureArchive Other-Machine Handoff

This file is the portable handoff for continuing DisclosureArchive on a Windows
PC or another workstation.

## Copy In Two Parts

1. Clone code from GitHub:

```text
https://github.com/GeorgiKostov/DisclosureArchive.git
```

2. Move data/index artifacts through an external-drive package:

```text
DisclosureArchivePackage/
  ufo_war_release/
  indexes/
    uap_release.sqlite
    uap_release.summary.json
  derived/
  MANIFEST.txt
  CHECKSUMS.sha256
```

Do not put raw PDFs/images/videos, generated SQLite DBs, OCR caches, `.venv`, or
transfer packages into Git.

## Mac Export

Mount the external drive, then run from the repo:

```bash
cd /Users/georgikostov/Desktop/ufo_release_index

EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage \
  ./scripts/export_transfer_package.sh
```

If you want a faster local package refresh without checksums:

```bash
EXPORT=/Users/georgikostov/Desktop/DisclosureArchivePackage \
  CREATE_CHECKSUMS=0 \
  ./scripts/export_transfer_package.sh
```

Verify the package:

```bash
./scripts/verify_transfer_package.sh /Volumes/DisclosureTransfer/DisclosureArchivePackage
```

The export script uses `sqlite3 .backup` to create a clean DB, so Windows does
not need SQLite `-wal` or `-shm` sidecar files.

## Windows Import

Assuming the package is on drive `E:`:

```powershell
mkdir C:\DisclosureArchive

git clone https://github.com/GeorgiKostov/DisclosureArchive.git C:\DisclosureArchive\repo

robocopy E:\DisclosureArchivePackage\ufo_war_release C:\DisclosureArchive\ufo_war_release /E
robocopy E:\DisclosureArchivePackage\indexes C:\DisclosureArchive\repo\indexes /E
robocopy E:\DisclosureArchivePackage\derived C:\DisclosureArchive\repo\derived /E

cd C:\DisclosureArchive\repo

py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e .
```

Or run the helper script from the cloned repo:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\scripts\windows_import_smoke.ps1 `
  -Repo C:\DisclosureArchive\repo `
  -Package E:\DisclosureArchivePackage `
  -RawTarget C:\DisclosureArchive\ufo_war_release
```

## Smoke Tests

```powershell
python -m ufo_indexer.search `
  --db indexes\uap_release.sqlite `
  --mode hybrid `
  --q "lunar surface flash Grimaldi"
```

Expected: Apollo 17 / lunar material near the top.

```powershell
python -m ufo_indexer.search `
  --db indexes\uap_release.sqlite `
  --mode hybrid `
  --q "nasa moon"
```

```powershell
python -m ufo_indexer.search `
  --db indexes\uap_release.sqlite `
  --mode vector `
  --q "helicopter crew saw hot orange orbs split and flare in formation"
```

If result paths still point to the Mac, rebuild on Windows:

```powershell
python -m ufo_indexer.index `
  --source-root C:\DisclosureArchive\ufo_war_release `
  --db indexes\uap_release.sqlite `
  --rebuild
```

## Pickup Prompt For Codex On The Other Machine

```text
We are continuing DisclosureArchive.

Goal:
Build a local-first evidence-first UFO/UAP public-records archive MVP. Do not build the full graph platform yet. First priority is processing all PDFs as well as possible, making them searchable, and preparing citation-backed evidence packs an LLM can use later for names, locations, timelines, events, and source-chain maps.

Repo:
https://github.com/GeorgiKostov/DisclosureArchive.git

Local expected layout:
- Repo: C:\DisclosureArchive\repo or ~/DisclosureArchive/repo
- Raw archive: C:\DisclosureArchive\ufo_war_release or ~/DisclosureArchive/ufo_war_release
- SQLite DB: repo/indexes/uap_release.sqlite
- Summary JSON: repo/indexes/uap_release.summary.json
- Derived text/OCR cache: repo/derived

Important constraints:
- Do not commit raw PDFs/images/videos.
- Do not commit generated SQLite DBs.
- Do not commit OCR/extracted-text caches.
- Preserve originals; never mutate downloaded source files.
- Keep every search/extraction result tied to document, page, path, and source metadata.
- Treat sources as evidence, not truth. Do not infer beyond the text.

Current known baseline:
- Existing index has around 162 documents, 305 assets, 1229 chunks, 1229 embeddings.
- Known smoke query: "lunar surface flash Grimaldi" should return Apollo 17.
- Existing package has CLI modules under ufo_indexer for index, OCR, search, and stats.

Next plan:
1. Inspect AGENTS.md and project docs first.
2. Verify the transferred DB and archive paths.
3. Run smoke searches.
4. If paths are Mac-local, rebuild the DB against the local raw archive path.
5. Do not implement the future graph yet.
6. Plan the next implementation around:
   - PDF classification: text-native, scanned, mixed, low-text.
   - Full resumable OCR over text-poor PDFs.
   - Reindexing OCR/native text into SQLite FTS + vector search.
   - Evidence-pack export for LLM use.
   - Optional reranking after hybrid search.
7. Keep project docs/tasks updated before coding.

Please start by reading AGENTS.md and the project docs, then report the current repo/data state and the exact next safe step.
```
