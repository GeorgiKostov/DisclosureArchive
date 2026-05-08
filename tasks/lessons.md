# Lessons

## 2026-05-08

- Direct terminal requests to `war.gov` assets returned 403, while normal browser/CDP access worked.
- The original PDF extractor could use the CSV shape but direct `requests` downloads were blocked by Akamai.
- Many legacy FBI/NARA-style PDFs are scan-only; `pdfplumber` extracts zero text from them until OCR is run.
- SQLite in WAL mode needs a clean `.backup` for portable transfer; do not treat `-wal`/`-shm` as the canonical DB.
- macOS system `rsync` is old and does not support `--info=progress2`; use `--progress --stats` or install newer rsync.
- The raw release folder once contained a macOS `.venv`; exclude/remove that from transfer packages.
- Hybrid search works well for case discovery; vector search is useful for similar descriptions such as orb formations.

