# Disclosure Archive

Local-first archive, OCR, indexing, search, and static-publication tooling for
public UFO/UAP release materials.

Disclosure Archive keeps raw government/source downloads out of Git, then builds
reproducible derived artifacts: extracted text, OCR text, SQLite FTS search,
local vector embeddings, local research UI data, and a static public website.

Current public site:

```text
https://disclosurearchive.org/
```

## What This Repo Contains

- Python package: `src/ufo_indexer/`
- Local SQLite index/search tooling
- PDF classification and Tesseract OCR pipeline
- Local browser search UI
- Static public site exporter
- Transfer and publish scripts
- Project docs, eval queries, task memory, and release workflow notes

## What This Repo Does Not Contain

Do not commit:

- Raw PDFs, images, videos, captions, thumbnails, or transfer packages
- Generated SQLite DBs under `indexes/`
- Extracted/OCR text caches under `derived/`
- Generated reports under `reports/`
- Generated static site output under `public_site/`
- `.venv`

Raw release data should live outside Git, for example:

```text
DisclosureArchivePackage/ufo_war_release/
```

## Key Docs

- [Release workflow](docs/RELEASE_WORKFLOW.md): end-to-end checklist for adding
  the next document release.
- [Architecture](docs/ARCHITECTURE.md): data flow, generated artifacts, SQLite
  tables, OCR, public export, publishing.
- [Search explained](docs/SEARCH_EXPLAINED.md): plain-English explanation of
  metadata, chunks, OCR, FTS, embeddings, hybrid search, and provenance.
- [Windows import](README_WINDOWS_IMPORT.txt): other-machine handoff and smoke
  tests.

## Setup

```bash
make setup
```

Equivalent:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
pip install -e .
```

On Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e .
```

## Common Paths

Set `SOURCE_ROOT` to the raw archive folder before indexing or OCR.

```powershell
$env:SOURCE_ROOT="C:\path\to\ufo_war_release"
```

The default DB path is:

```text
indexes/uap_release.sqlite
```

## Build Or Update The Index

Incremental index:

```bash
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

Full rebuild:

```bash
make rebuild SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

Direct equivalent:

```bash
python -m ufo_indexer.index \
  --source-root /absolute/path/to/ufo_war_release \
  --db indexes/uap_release.sqlite
```

The indexer reads release metadata and manifests, attaches assets, extracts
native PDF text, imports OCR/caption/video metadata when available, creates text
chunks, extracts/geocodes locations, and stores FTS plus local vector embeddings.

## OCR

Install Tesseract first.

macOS:

```bash
brew install tesseract
```

Windows:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Classify PDFs:

```bash
make classify SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

Run OCR over classified scan/low-text/mixed PDFs:

```bash
make ocr-classified \
  SOURCE_ROOT=/absolute/path/to/ufo_war_release \
  OCR_WORKERS=4
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

On Windows, pass Tesseract explicitly if needed:

```powershell
make ocr-classified `
  SOURCE_ROOT="$env:SOURCE_ROOT" `
  OCR_WORKERS=12 `
  TESSERACT_BIN="C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Audit OCR coverage:

```bash
make ocr-status SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

Retry weak OCR pages from the status report:

```bash
make ocr-retry \
  SOURCE_ROOT=/absolute/path/to/ufo_war_release \
  OCR_WORKERS=4 \
  OCR_DPI=300 \
  OCR_PSM=11
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
```

OCR caches are generated under `derived/text/ocr/` and ignored by Git. They are
keyed from paths relative to `SOURCE_ROOT` so they survive Mac/Windows transfer.

## Search

Hybrid search is the default user-facing mode:

```bash
make search-hybrid Q="lunar surface flash Grimaldi"
```

Vector search:

```bash
make search-vector Q="helicopter crew saw hot orbs split and flare in formation"
```

Direct CLI:

```bash
python -m ufo_indexer.search \
  --db indexes/uap_release.sqlite \
  --mode hybrid \
  --q "diamond shaped object SWIR Greece 434 knots"
```

Keyword search uses strict SQLite FTS first, then a broader OR-style fallback
only when strict matching returns nothing. Hybrid search combines keyword and
local vector retrieval.

## Retrieval Evaluation

Run this after OCR, chunking, embedding, or ranking changes:

```bash
make eval-search DB=indexes/uap_release.sqlite
```

The eval reads `eval/retrieval_queries.json` and writes ignored reports under
`reports/`. Add new release-specific queries before tuning ranking.

## Evidence Packs

Export citation/provenance-preserving search bundles:

```bash
make evidence-pack Q="flying discs flight service regulation 1949"
```

Direct CLI:

```bash
python -m ufo_indexer.evidence_pack \
  --db indexes/uap_release.sqlite \
  --q "flying discs flight service regulation 1949" \
  --mode hybrid \
  --out reports/evidence_pack.json
```

Each result includes title, agency, incident date/location, source kind, page,
chunk id, score, snippet, local path, and provenance guidance.

## Local Search UI

Windows launcher:

```text
Start-DisclosureArchive-Search.cmd
```

Manual server:

```bash
make web DB=indexes/uap_release.sqlite
```

Then open:

```text
http://127.0.0.1:8765
```

The local UI supports hybrid/vector/keyword search, result cards, media
previews, map hints, source links, provenance labels, and local generated
summaries. Summaries are finding aids over metadata/native PDF text/OCR/captions
and are not proof of claims.

## Static Public Site

Generate `public_site/`:

```bash
make export-site DB=indexes/uap_release.sqlite
```

Direct CLI:

```bash
python -m ufo_indexer.export_site \
  --db indexes/uap_release.sqlite \
  --out public_site \
  --ga-measurement-id G-NNXB9F00V6
```

The export writes:

- `public_site/index.html`
- `public_site/data/documents.json`
- `public_site/social-card.png`
- `robots.txt`, `sitemap.xml`, `security.txt`, `/.well-known/security.txt`
- `_headers`, `favicon.svg`, `site.webmanifest`, `humans.txt`, `llms.txt`
- Contact, legal, privacy, and security pages

The public JSON includes metadata, summaries, public source/media URLs, tags,
locations, related documents, and structured page/chunk references. It excludes
raw files, generated DBs, OCR caches, local paths, and full OCR text.

Serve locally for review:

```bash
python -m http.server 8788 -d public_site
```

Then open:

```text
http://127.0.0.1:8788/
```

## Publish

GitHub Pages:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish_github_pages.ps1
```

The publisher regenerates `public_site/`, validates the public JSON for
private/local path leaks, copies only static files to a temporary checkout, and
pushes `gh-pages`.

Cloudflare Pages, if real HTTP `_headers` are required:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish_cloudflare_pages.ps1
```

Verify live headers:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_public_security_headers.ps1 -Url https://disclosurearchive.org/
```

## Transfer Package

Create and verify a portable handoff package:

```bash
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make export-package
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make verify-package
```

The package uses a clean SQLite `.backup`. Do not copy live `-wal` or `-shm`
files as canonical DB state.

## Next Release Checklist

Use [docs/RELEASE_WORKFLOW.md](docs/RELEASE_WORKFLOW.md) when a new document
batch arrives. The short version:

1. Stage raw data and manifests outside Git.
2. Run index, classification, OCR, OCR status, and reindex.
3. Run retrieval evals and manual smoke searches.
4. Review the local UI.
5. Update tags, highlights, and release groups in `export_site.py`.
6. Regenerate and inspect `public_site/`.
7. Publish and verify live pages/assets.
8. Update task memory.

## Useful Commands

```bash
make setup
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
make rebuild SOURCE_ROOT=/absolute/path/to/ufo_war_release
make classify SOURCE_ROOT=/absolute/path/to/ufo_war_release
make ocr-classified SOURCE_ROOT=/absolute/path/to/ufo_war_release OCR_WORKERS=4
make ocr-status SOURCE_ROOT=/absolute/path/to/ufo_war_release
make eval-search
make stats
make web
make export-site
```
