# DisclosureArchive Memory

## Current state

Repo:

```text
/Users/georgikostov/Desktop/ufo_release_index
https://github.com/GeorgiKostov/DisclosureArchive
Z:\Projects\Repositories\Disclosure\DisclosureArchive
```

Raw archive:

```text
/Users/georgikostov/Desktop/ufo_war_release
```

Transfer package:

```text
/Users/georgikostov/Desktop/DisclosureArchivePackage
Z:\Projects\Repositories\Disclosure\DisclosureArchive\DisclosureArchivePackage
```

## What has been built

- Python package `ufo_indexer`.
- SQLite schema for documents, assets, chunks, FTS, and embeddings.
- PDF extraction cache.
- OCR pipeline with Tesseract.
- Parallel classified OCR with PDF-level `--workers`.
- Portable PDF/OCR cache lookup keyed from `SOURCE_ROOT`-relative paths with old absolute-path cache fallback by `file_hash`.
- PDF classification CLI and reports for OCR readiness.
- OCR status CLI and reports for cache coverage and review candidates.
- Status-driven OCR retries for selected weak pages with safe cache merging.
- Hybrid, keyword, and vector search CLI.
- Retrieval evaluation CLI and curated query set for keyword/vector/hybrid quality checks.
- Evidence-pack export CLI for LLM-ready JSON/Markdown search bundles.
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

Windows rebuilt DB:

- DB path: `indexes/uap_release.sqlite`
- Source root: `Z:\Projects\Repositories\Disclosure\DisclosureArchive\DisclosureArchivePackage\ufo_war_release`
- `PRAGMA integrity_check`: ok
- Documents: 162
- Assets: 305
- Chunks: 1229
- Embeddings: 1229
- Asset paths now use Windows `Z:\...` paths; no `/Users/...` asset paths remain.
- Smoke searches verified for `lunar surface flash Grimaldi` and `helicopter crew saw hot orange orbs split and flare in formation`.
- PDF/OCR cache summary is back to the known baseline after portability migration: 4156 cached PDF pages and 3 cached OCR pages.
- Classification report generated on Windows: 117 PDFs, 65 scan-only, 10 mixed, 2 low-text, 40 text-native.
- Tesseract is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` but is not on PATH in the current shell.
- OCR smoke sample completed after fixing Windows temp-file handling.
- Current DB after OCR smoke: 162 documents, 305 assets, 1244 chunks, 22 `ocr_text` chunks, 1244 embeddings.
- OCR cache summary after filtering failed temp-lock caches: 13 successful OCR pages and 14,341 OCR chars.
- New OCR search checks verified Gemini 7 “bogey” transcript and FBI September 2023 302 records.

## Next best moves

Broad OCR update:

- Broad classified OCR completed on Windows with 12 workers and the explicit Tesseract path.
- Current DB after broad OCR: 162 documents, 305 assets, 7608 chunks, 6386 `ocr_text` chunks, 7608 embeddings.
- OCR cache summary after broad OCR: 3633 successful OCR pages and 4,428,817 OCR chars.
- Additional post-OCR searches verified legacy flying-disc records from OCR text.
- OCR status report: 3633/3633 expected OCR pages cached, 0 OCR error pages, 62 zero-text pages, and 35 PDFs needing review.
- Retry smoke test with 300 DPI and PSM 11 on `dow-uap-d4-mission-report-arabian-gulf-2020.pdf` reduced zero-text pages from 62 to 60 and reindexed the DB to 7610 chunks, 6388 `ocr_text` chunks, and 7610 embeddings.
- Retrieval eval report after FTS fallback: 15 curated queries; hybrid passed 15, vector passed 14, keyword passed 14. Hybrid best matches included 6 metadata, 6 OCR text, and 3 PDF text hits. `new_haven_flying_saucers` now passes in top five, though not at rank 1.
- Evidence-pack smoke test generated for `flying discs flight service regulation 1949`; the pack contains 8 ranked results with provenance, source labels, snippets/full text, page numbers, local paths, and OCR/source-use guidance.

1. Review the 35 OCR status candidates and separate true image/photo-only pages from OCR failures.
2. Add more curated retrieval eval queries before tuning hybrid scoring or adding reranking.
3. Use evidence packs for a small manual research pass and note what provenance fields or ranking changes are missing.
4. Decide whether a small OCRmyPDF or PaddleOCR comparison is warranted for genuinely weak OCR pages.
