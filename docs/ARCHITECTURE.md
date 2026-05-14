# Architecture

This repo indexes a local UFO/UAP release library without owning the raw archive.

## Inputs

Expected source directory layout:

```text
ufo_war_release/
  uap-csv.cdp.csv
  uap_download_manifest.json
  dvids_video_manifest.cdp.json
  documents/
  thumbnails/
  evidence_carousel/
  videos/
```

The indexer accepts the source directory via `--source-root` or `make SOURCE_ROOT=...`.

## Generated Outputs

```text
indexes/uap_release.sqlite
indexes/uap_release.summary.json
derived/text/*.json
reports/pdf_classification.json
reports/pdf_classification.md
reports/ocr_status.json
reports/ocr_status.md
reports/retrieval_eval.json
reports/retrieval_eval.md
reports/evidence_pack*.json
reports/evidence_pack*.md
```

These are ignored by git. Rebuild them from source data.

## Transfer Package

The other-machine handoff package is generated outside Git:

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

Create it with:

```bash
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make export-package
```

The package DB must be made with `sqlite3 .backup`; do not treat live
`uap_release.sqlite-wal` or `uap_release.sqlite-shm` files as portable state.

## SQLite Tables

- `documents`: one row per CSV release record.
- `assets`: local file paths and hashes for PDFs, images, videos, captions.
- `chunks`: citable text chunks from metadata, PDFs, video metadata, and captions.
- `chunks_fts`: SQLite FTS5 full-text index.
- `embeddings`: normalized local embeddings for semantic search.
- `locations`: mappable latitude/longitude records with source kind, confidence,
  precision, method, and optional chunk provenance.

## Incremental Behavior

The indexer hashes document metadata plus associated asset hashes. If a record is
unchanged and already has chunks, it updates asset rows but skips chunk extraction
and embedding regeneration.

Location extraction is also safe on incremental runs. The indexer refreshes each
document's `locations` rows, geocodes known `incident_location` strings at
country/region/city precision, and extracts explicit decimal or DMS coordinates
from existing chunks. Coordinates from text are labeled as regex-derived and
should still be checked against the source page.

When new release files arrive:

1. Add or update the raw release folder.
2. Run `make index SOURCE_ROOT=/path/to/ufo_war_release`.
3. Changed/new records are processed; unchanged records are skipped.

Use `make rebuild` when changing chunking, extraction, OCR cache naming, or
embedding settings.

## OCR Extension Point

Many historical PDFs are scan-only. Use `python -m ufo_indexer.classify` to
produce `reports/pdf_classification.json` and `.md`, grouped as `scan_only`,
`low_text`, `mixed`, and `text_native`. The OCR command can consume that report:

```bash
python -m ufo_indexer.ocr \
  --source-root /path/to/ufo_war_release \
  --from-classification reports/pdf_classification.json \
  --classes scan_only low_text mixed \
  --workers 4
```

The built-in OCR pipeline renders selected pages with `pypdfium2`, sends them to
the local `tesseract` binary, and writes per-page JSON to `derived/text/ocr/`.
`--workers` parallelizes at the PDF level, preserving existing OCR caches while
letting broad classified passes use multiple CPU cores. The main indexer then
adds those pages as `ocr_text` chunks. Source PDFs are never modified.

Use `python -m ufo_indexer.ocr_status` after OCR to audit cache coverage and
quality signals. The report compares expected OCR pages from
`reports/pdf_classification.json` with cached OCR pages, then flags missing,
partial, zero-text, error, and very-low-character outputs for review.

The OCR command can consume `reports/ocr_status.json` with `--from-status` to
retry only review candidates. When retrying selected pages, the OCR cache writer
merges replacement page text into the existing per-PDF cache instead of
discarding pages that were not rerun.

PDF extraction and OCR cache filenames are keyed from the source file path
relative to `SOURCE_ROOT` when possible, for example `documents/example.pdf`.
This keeps generated cache names portable across Mac and Windows checkouts. The
indexer and OCR command also fall back to older absolute-path cache files by
matching `file_hash`, then write a portable cache copy on the next run.

After changing extraction, OCR, cache naming, or embeddings, verify with:

```bash
make rebuild SOURCE_ROOT=/absolute/path/to/ufo_war_release
make search-hybrid Q="lunar surface flash Grimaldi"
```

## Retrieval Evaluation

`python -m ufo_indexer.eval_search` runs curated queries from
`eval/retrieval_queries.json` through keyword, vector, and hybrid search. The
generated report records top results, pass/fail status, best matching rank, and
whether expected OCR/PDF/metadata evidence surfaced. Use it before tuning
hybrid scoring, changing embeddings, or adding reranking.

Keyword retrieval first uses strict SQLite FTS matching. If strict matching
returns no rows for a multi-term query, it retries with an OR-style FTS query so
longer natural-language searches can still surface noisy OCR chunks. Hybrid
search benefits from this fallback while preserving exact-match behavior when
strict FTS succeeds.

## Evidence Packs

`python -m ufo_indexer.evidence_pack` exports ranked search results as
LLM-ready JSON and Markdown. Evidence items preserve provenance fields including
title, agency, incident date/location, source kind, page number, local path, and
chunk id. OCR-derived text is labeled as `ocr_text` so downstream summaries can
distinguish OCR text from native PDF text and metadata.

## Local Search UI

`python -m ufo_indexer.web` runs a local-only HTTP server on `127.0.0.1`.
The server uses standard-library HTTP handling and reuses the existing search
and evidence-pack modules. It exposes `/api/health`, `/api/search`, and
`/api/evidence-pack`, plus a guarded `/file` endpoint for index-referenced local
files. The single-page browser UI includes extractive summaries, ranked result
cards, provenance references, OCR labels, follow-up suggestions, media previews,
government source links, labeled summary controls, local readable summaries,
cleaned source excerpts, and a simple result-location map. The readable
summaries are deterministic extractive helpers over the indexed chunk text; they
normalize common OCR/mojibake artifacts, reject low-quality OCR sentences, and
fall back to document metadata when indexed text is too noisy, while preserving
source provenance.

`/api/source-summary` accepts a `doc_id` and returns a fuller local source
summary for that document. It reads indexed native PDF text, OCR text, captions,
and video metadata from `chunks`, selects readable source sentences, and returns
a quick summary, the likely mysterious/UAP element, a detailed contents
breakdown, page/chunk references, and a source-mix note.

## Static Public Site Export

`python -m ufo_indexer.export_site` builds a dependency-free static site under
`public_site/` from the SQLite index. The command exports
`public_site/index.html` plus `public_site/data/documents.json`, with one public
payload per document. Each payload includes document/release metadata,
government source URLs, public asset URLs, locations, tags, related-document
links, deterministic summary sections, and structured references back to
chunk/page/source-kind provenance. The payload also includes a small curated
`featured_documents` list for the public landing `HIGHLIGHTS` section; each item
is selected from indexed records and links back into the client-side index view.
The static HTML presents two top-level client-side views: a landing/highlights
view with a compact search box, and a search workbench with filters, result
cards, and an on-demand location globe. Search keeps the complete matching
document set in memory but renders cards in 20-result batches, loading more on
scroll with a manual fallback button.
The exporter also emits `robots.txt`, `sitemap.xml`, root and well-known
`security.txt`, canonical/social/structured-data metadata, a referrer policy,
and a static-host `_headers` template. The HTML footer exposes copyright,
contact, Legal / Impressum, privacy, security, sitemap, and source-code links;
the contact email is configurable at export time and is also written into
`security.txt`. On GitHub Pages, browser-enforced meta policies apply, but
`_headers` is only useful if the site later moves to a host that supports custom
static headers.

The public export is intentionally summary-focused. It does not copy raw PDFs,
videos, local thumbnails, generated SQLite databases, derived OCR caches, or full
OCR text. It also validates that common local path markers such as Windows drive
paths, `DisclosureArchivePackage`, `derived/`, and the local DB path do not leak
into the JSON payload. The static HTML uses a responsive dark terminal-style
template, performs client-side search over the precomputed dataset, exposes a
clear `Summary` button for detailed summary sections, and links verification
actions back to the original WAR/DVIDS government URLs. Summary references stay
in the payload for provenance and search, but duplicate page/chunk reference
link rows are not rendered on public result cards.

Analytics are optional and build-time only. Passing `--analytics-domain` or
setting `DISCLOSURE_ANALYTICS_DOMAIN` injects a Plausible-compatible script and
client-side event hooks for page views, search submissions, filter changes,
summary toggles, outbound source/video clicks, globe opens, and checkpoint
selection. Search events report query length rather than query text. Exports
without an analytics domain emit no analytics script.

`scripts/publish_github_pages.ps1` is the publish wrapper for GitHub Pages. It
regenerates the static export, validates the JSON for local/private path
markers, copies only the generated static files into a temporary checkout, adds
`.nojekyll`, and pushes the result to the `gh-pages` branch. That keeps the
generated publish artifact separate from `main`, where raw data, generated DBs,
and generated static output remain ignored.

Because the SQLite index and generated site are intentionally local-only, Pages
publishing is automated locally rather than in GitHub Actions. Running
`scripts/install_auto_pages_publish.ps1` configures Git to use the tracked
`.githooks/pre-push` hook. The hook watches pushes to `origin/main` and runs
`scripts/publish_github_pages.ps1` from the same machine before the main push
completes, skipping cleanly if the local index is absent or if
`DISCLOSURE_SKIP_PAGES_PUBLISH=1` is set.
