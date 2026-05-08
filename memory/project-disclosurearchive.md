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
- Mac export and package verification scripts.
- Windows import smoke-test script.
- Agent scaffold for future continuity.

## Current verification

Packaged DB:

- `PRAGMA integrity_check`: ok
- Documents: 162
- Chunks: 1229
- Embeddings: 1229
- Search `lunar surface flash Grimaldi` returns Apollo 17 as top result.

## Next best moves

1. Mount external drive and run `EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make export-package`.
2. Verify with `EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make verify-package`.
3. Set up Windows clone and import package using `README_WINDOWS_IMPORT.txt` or `scripts/windows_import_smoke.ps1`.
4. Run Windows search smoke tests.
5. Decide whether to rebuild the DB on Windows for native local paths.
6. Run OCR on the large FBI/legacy scans.
