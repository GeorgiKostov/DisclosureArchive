# UFO Release Index

Standalone local search/index project for the WAR UFO release downloaded to:

`/Users/georgikostov/Desktop/ufo_war_release`

This project does not modify the Rebuilt repository. Raw downloads stay in the
release directory; this project creates derived text, metadata, SQLite FTS, and
embedding artifacts under `indexes/` and `derived/`.

## Setup

```bash
cd /Users/georgikostov/Desktop/ufo_release_index
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Or:

```bash
make setup
```

## Build Or Update The Index

```bash
python -m ufo_indexer.index \
  --source-root /Users/georgikostov/Desktop/ufo_war_release \
  --db indexes/uap_release.sqlite
```

Use `--rebuild` to delete and recreate the index from scratch.

```bash
python -m ufo_indexer.index \
  --source-root /Users/georgikostov/Desktop/ufo_war_release \
  --db indexes/uap_release.sqlite \
  --rebuild
```

Equivalent Make targets:

```bash
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
make rebuild SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

## OCR Scanned PDFs

OCR means optical character recognition: the computer looks at a scanned page image
and turns the visible letters into text. It is needed for the older FBI/NARA-style
PDFs where `pdfplumber` sees pages but extracts little or no text.

Classify PDFs first so OCR work is targeted:

```bash
python -m ufo_indexer.classify \
  --source-root /absolute/path/to/ufo_war_release \
  --derived-root derived \
  --out reports/pdf_classification.json
```

This also writes `reports/pdf_classification.md`, grouped by `scan_only`,
`low_text`, `mixed`, and `text_native`.

Install the OCR engine on macOS:

```bash
brew install tesseract
```

On Windows:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Then run OCR over classified scan/low-text/mixed PDFs:

```bash
python -m ufo_indexer.ocr \
  --source-root /absolute/path/to/ufo_war_release \
  --from-classification reports/pdf_classification.json \
  --classes scan_only low_text mixed \
  --workers 4
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

Audit OCR coverage and review candidates without rerunning OCR:

```bash
python -m ufo_indexer.ocr_status \
  --source-root /absolute/path/to/ufo_war_release \
  --classification reports/pdf_classification.json \
  --out reports/ocr_status.json
```

This also writes `reports/ocr_status.md`, including cached/expected page counts,
zero-text OCR pages, OCR errors, low-average-character outputs, and retry/review
candidates.

Retry only candidates from the OCR status report:

```bash
python -m ufo_indexer.ocr \
  --source-root /absolute/path/to/ufo_war_release \
  --from-status reports/ocr_status.json \
  --review-reasons zero_text_pages low_avg_chars \
  --dpi 300 \
  --psm 11
```

Status-driven retries rerun only the flagged pages when page numbers are known
and merge the new text back into the existing per-PDF OCR cache. Rebuild the
index afterward if the retry improves OCR text:

```bash
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

Use `--workers` for PDF-level parallelism. A value near half the machine's
logical CPUs is a good starting point for broad OCR; the Windows workstation
completed the classified weak-PDF pass with `--workers 12`. Tesseract can be
passed explicitly if it is installed but not on `PATH`:

```powershell
.\.venv\Scripts\python -m ufo_indexer.ocr `
  --source-root DisclosureArchivePackage\ufo_war_release `
  --from-classification reports\pdf_classification.json `
  --classes scan_only low_text mixed `
  --workers 12 `
  --tesseract-bin "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Or run OCR over all candidate text-poor pages:

```bash
make ocr SOURCE_ROOT=/absolute/path/to/ufo_war_release OCR_WORKERS=4
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

OCR one specific PDF first:

```bash
make ocr-one \
  SOURCE_ROOT=/absolute/path/to/ufo_war_release \
  PDF=/absolute/path/to/ufo_war_release/documents/65_hs1-834228961_62-hq-83894_section_1.pdf
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

OCR output is stored as generated JSON under `derived/text/ocr/` and is ignored by
git. Cache names are keyed from each file path relative to `SOURCE_ROOT`, so they
survive Mac/Windows transfers. Older absolute-path cache names are still detected
by file hash and migrated on the next index/OCR run. When OCR text changes, the
indexer detects it and adds `ocr_text` chunks.

## Search

For a plain-English explanation of the whole search stack, read
`docs/SEARCH_EXPLAINED.md`.

Keyword search:

```bash
python -m ufo_indexer.search --db indexes/uap_release.sqlite --q "Apollo 17 flash lunar surface"
```

Semantic search:

```bash
python -m ufo_indexer.search --db indexes/uap_release.sqlite --mode vector --q "military observers saw orange orbs split into multiple lights"
```

Hybrid search:

```bash
python -m ufo_indexer.search --db indexes/uap_release.sqlite --mode hybrid --q "diamond shaped object SWIR Greece 434 knots"
```

Keyword search uses strict full-text matching first, then falls back to a broader
OR-style full-text query only when strict matching returns nothing. This keeps
exact searches stable while helping longer natural-language queries over noisy
OCR text.

Or:

```bash
make search-hybrid Q="lunar surface flash Grimaldi"
make search-vector Q="helicopter crew saw hot orbs split and flare in formation"
```

## Evaluate Retrieval

Run the curated retrieval evaluation after OCR, chunking, embedding, or ranking
changes:

```bash
python -m ufo_indexer.eval_search \
  --db indexes/uap_release.sqlite \
  --queries eval/retrieval_queries.json \
  --out reports/retrieval_eval.json
```

This writes `reports/retrieval_eval.json` and `reports/retrieval_eval.md`.
The eval compares keyword, vector, and hybrid search, then marks whether
expected evidence appears in the top five results. `hybrid` is the user-facing
default; keyword and vector are included to explain failures.

## Export Evidence Packs

Export LLM-ready evidence bundles from search results:

```bash
python -m ufo_indexer.evidence_pack \
  --db indexes/uap_release.sqlite \
  --q "flying discs flight service regulation 1949" \
  --mode hybrid \
  --out reports/evidence_pack.json
```

This also writes `reports/evidence_pack.md`. Each result includes rank, score,
title, agency, incident date/location, source kind, page number, chunk id, local
path, snippet, and provenance guidance. Use `--include-text` when the downstream
LLM needs full chunk text instead of snippets.

## Local Search UI

On Windows, double-click this repo-root launcher:

```text
Start-DisclosureArchive-Search.cmd
```

It starts the local server and opens the browser. Keep the launcher window open
while searching; close it to stop the server. If the server is already running,
the launcher simply opens the existing page.

Run the browser interface on localhost:

```bash
python -m ufo_indexer.web \
  --db indexes/uap_release.sqlite \
  --host 127.0.0.1 \
  --port 8765
```

Then open `http://127.0.0.1:8765`. The UI uses the same keyword, vector, hybrid,
and evidence-pack code as the CLI. It shows ranked result cards, provenance
references, extractive summaries, OCR labels, and clickable follow-up
suggestions without requiring an LLM API key. Results include a small map of
indexed locations when coordinates or geocoded incident locations are available.
Local thumbnails/images and videos are previewed directly from the indexed asset
paths. The primary action link is the `Government source` button, which opens
the original WAR/DVIDS source URL recorded during download instead of exposing a
local PDF path as the main UI action.
Each result also includes a local readable summary and a cleaned source excerpt.
These are extractive helpers over indexed text/OCR, not proof of the underlying
claim and not a substitute for checking the source PDF/video.
Use `Summarize source` on a result card to generate a fuller local summary for
the whole indexed source document/PDF. The server reads the document's indexed
native PDF text, OCR text, captions, and video metadata when available, then
returns a quick summary, the likely mysterious/UAP element, a more detailed
contents breakdown, page/chunk references, and a source-mix note.

## Static Public Site Export

Generate an online-ready static search page from the current SQLite index:

```bash
python -m ufo_indexer.export_site \
  --db indexes/uap_release.sqlite \
  --out public_site
```

or:

```bash
make export-site DB=indexes/uap_release.sqlite
```

The export writes `public_site/index.html` and
`public_site/data/documents.json`. The JSON contains one precomputed,
deterministic summary per document, public government source/thumbnail/video
URLs, tags, locations, related-document references, and page/chunk references.
It intentionally excludes raw downloads, generated SQLite databases, local file
paths, derived OCR caches, and full OCR text. The static page uses a dark
terminal-style template, performs client-side search over titles, metadata,
tags, summaries, and cited snippets, and links readers back to the government
source files for verification.

To publish the generated site to GitHub Pages:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish_github_pages.ps1
```

The script regenerates `public_site/`, validates that the public JSON does not
contain local/private path markers, copies only the static files to a temporary
checkout, adds `.nojekyll`, and pushes a `gh-pages` branch. In GitHub repository
settings, configure Pages to deploy from the `gh-pages` branch root if it is not
already enabled.

## Transfer To Another Machine

Use the tracked handoff workflow instead of copying generated DB files by hand:

```bash
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make export-package
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make verify-package
```

The export script copies the raw archive and derived text/OCR cache, creates a
clean SQLite backup with `sqlite3 .backup`, copies the summary JSON, and writes a
manifest/checksum file for the transfer package. Full Windows import instructions
and the Codex pickup prompt live in `README_WINDOWS_IMPORT.txt`.

## Design

- `documents`: one row per release CSV item plus useful DVIDS metadata.
- `assets`: local paths for PDFs, images, thumbnails, videos, and captions.
- `chunks`: stable, citable text chunks with document metadata.
- `chunks_fts`: SQLite FTS5 index for exact term search.
- `embeddings`: local embedding vectors stored as normalized float32 blobs.
- `locations`: provenance-preserving latitude/longitude records from explicit
  coordinate text or conservative incident-location geocoding.

The indexer is safe to rerun. Stable IDs and content hashes let it update new
or changed files without changing the raw archive.

After changing extraction, OCR, cache naming, chunking, or embeddings, verify
with:

```bash
make rebuild SOURCE_ROOT=/absolute/path/to/ufo_war_release
make search-hybrid Q="lunar surface flash Grimaldi"
```

## OCR Note

Many historical PDFs are scans. The recommended workflow is to classify first,
OCR `scan_only`, `low_text`, and `mixed` PDFs, then reindex so OCR pages become
`ocr_text` chunks. For this archive, the broad classified OCR pass added 6,386
OCR chunks while preserving the raw source PDFs.
