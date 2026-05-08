# Decisions

## 2026-05-08

- Keep DisclosureArchive as a standalone repo, separate from Rebuilt.
- Push code/docs to GitHub at `GeorgiKostov/DisclosureArchive`.
- Keep raw downloads and generated DB/cache artifacts out of Git.
- Use SQLite for durable local search state.
- Use SQLite FTS5 for keyword search.
- Use local `fastembed` embeddings for semantic/vector search.
- Use hybrid search as the recommended default.
- Store generated text caches under `derived/text/`.
- Store OCR caches under `derived/text/ocr/`.
- Use `sqlite3 .backup` for transfer-safe DB copies.
- Use external-drive transfer for the Windows PC data package.
- Keep the other-machine handoff as tracked docs/scripts so a fresh clone can reproduce package export/import.
- Generate transfer package manifests and checksums outside Git; never stage the package itself.
- Keep the MVP local-first on SQLite FTS plus local vectors until retrieval quality is trusted.
