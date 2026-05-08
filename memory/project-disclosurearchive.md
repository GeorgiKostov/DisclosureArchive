# DisclosureArchive Memory

## Current state

Repo:

```text
/Users/georgikostov/Desktop/ufo_release_index
https://github.com/GeorgiKostov/DisclosureArchive
```

Raw archive:

```text
/Users/georgikostov/Desktop/ufo_war_release
```

Transfer package:

```text
/Users/georgikostov/Desktop/DisclosureArchivePackage
```

## What has been built

- Python package `ufo_indexer`.
- SQLite schema for documents, assets, chunks, FTS, and embeddings.
- PDF extraction cache.
- OCR pipeline with Tesseract.
- Hybrid, keyword, and vector search CLI.
- Windows transfer package instructions.
- Agent scaffold for future continuity.

## Current verification

Packaged DB:

- `PRAGMA integrity_check`: ok
- Documents: 162
- Chunks: 1229
- Embeddings: 1229
- Search `lunar surface flash Grimaldi` returns Apollo 17 as top result.

## Next best moves

1. Copy transfer package to external drive.
2. Set up Windows clone and import package.
3. Run Windows search smoke tests.
4. Decide whether to rebuild the DB on Windows for native local paths.
5. Run OCR on the large FBI/legacy scans.

