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
```

These are ignored by git. Rebuild them from source data.

## SQLite Tables

- `documents`: one row per CSV release record.
- `assets`: local file paths and hashes for PDFs, images, videos, captions.
- `chunks`: citable text chunks from metadata, PDFs, video metadata, and captions.
- `chunks_fts`: SQLite FTS5 full-text index.
- `embeddings`: normalized local embeddings for semantic search.

## Incremental Behavior

The indexer hashes document metadata plus associated asset hashes. If a record is
unchanged and already has chunks, it updates asset rows but skips chunk extraction
and embedding regeneration.

When new release files arrive:

1. Add or update the raw release folder.
2. Run `make index SOURCE_ROOT=/path/to/ufo_war_release`.
3. Changed/new records are processed; unchanged records are skipped.

Use `make rebuild` when changing chunking, extraction, or embedding settings.

## OCR Extension Point

Many historical PDFs are scan-only. Add OCR text under `derived/text/ocr/` or
extend `src/ufo_indexer/index.py` to run an OCR tool before chunking. Good future
options:

- `python -m ufo_indexer.ocr` for the built-in Tesseract page OCR pipeline.
- `ocrmypdf` for searchable PDF derivatives.
- A separate OCR table with confidence and page-image references.

The built-in OCR pipeline renders selected pages with `pypdfium2`, sends them to
the local `tesseract` binary, and writes per-page JSON to `derived/text/ocr/`.
The main indexer then adds those pages as `ocr_text` chunks.
