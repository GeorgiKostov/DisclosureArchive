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

Install the OCR engine on macOS:

```bash
brew install tesseract
```

Then run OCR over text-poor pages:

```bash
make ocr SOURCE_ROOT=/absolute/path/to/ufo_war_release
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
git. When OCR text changes, the indexer detects it and adds `ocr_text` chunks.

## Search

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

Or:

```bash
make search-hybrid Q="lunar surface flash Grimaldi"
make search-vector Q="helicopter crew saw hot orbs split and flare in formation"
```

## Design

- `documents`: one row per release CSV item plus useful DVIDS metadata.
- `assets`: local paths for PDFs, images, thumbnails, videos, and captions.
- `chunks`: stable, citable text chunks with document metadata.
- `chunks_fts`: SQLite FTS5 index for exact term search.
- `embeddings`: local embedding vectors stored as normalized float32 blobs.

The indexer is safe to rerun. Stable IDs and content hashes let it update new
or changed files without changing the raw archive.

## OCR Note

Many historical PDFs are scans. This project indexes their release metadata now,
but full text requires a later OCR pass. Add OCR-derived text files under
`derived/text/ocr/` or extend `index.py` with an OCR extractor when ready.
