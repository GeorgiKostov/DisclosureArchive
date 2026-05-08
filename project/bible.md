# Project Bible

## Project

DisclosureArchive is a local-first archive, OCR, and search system for public UFO/UAP release materials.

## Current purpose

The first release imported is the WAR UFO page release from May 8, 2026. The project provides:

- Local raw file archive
- PDF text extraction cache
- Classified parallel OCR for scan-only PDFs
- SQLite FTS search
- Local vector embeddings for semantic search
- Hybrid search CLI
- Transfer workflow for continuing work on Windows

The near-term MVP is evidence-first searchable archival infrastructure, not a
chatbot: process PDFs as completely as possible, preserve provenance, support
fast keyword/vector/hybrid retrieval, and prepare citation-backed evidence packs
for later entity, location, timeline, and incident extraction.

## Current canonical repo

```text
https://github.com/GeorgiKostov/DisclosureArchive
```

## Current local archive state

Mac source data:

```text
/Users/georgikostov/Desktop/ufo_war_release
```

Index repo:

```text
/Users/georgikostov/Desktop/ufo_release_index
```

Transfer package:

```text
/Users/georgikostov/Desktop/DisclosureArchivePackage
Z:\Projects\Repositories\Disclosure\DisclosureArchive\DisclosureArchivePackage
```

Canonical handoff instructions:

```text
README_WINDOWS_IMPORT.txt
scripts/export_transfer_package.sh
scripts/verify_transfer_package.sh
scripts/windows_import_smoke.ps1
```

## Current indexed stats

As of the latest verified Windows build after classified OCR:

- Documents: 162
- Assets: 305
- Chunks: 7608
- OCR chunks: 6386
- Embeddings: 7608
- Cached PDF pages: 4156
- Extracted PDF chars: 832,911
- OCR pages cached: 3633
- OCR chars cached: 4,428,817

## Important source clusters

- NASA/Moon: Apollo 12, Apollo 17, Gemini 7, Apollo 11, Skylab, Apollo image records.
- Modern military: Western US Event, USPER statement, Greece, Syria, INDOPACOM, Middle East clips.
- State Department: Kazakhstan 1994, Papua New Guinea 1985, Georgia 2001.
- FBI legacy: 62-HQ-83894 and related serials, now broadly OCR-indexed but still requiring quality review on noisy scans.
