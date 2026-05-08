# Constraints

## Data and Git

- Do not commit raw archive data.
- Do not commit generated SQLite databases.
- Do not commit `derived/` extraction/OCR caches.
- Do not commit `.venv`, local package metadata, or transfer packages.
- Keep `.gitignore` aligned with these constraints.

## Evidence and interpretation

- Treat source documents as evidence records, not as proof of claims.
- Distinguish official metadata from transcript text, OCR text, video metadata, and analyst summaries.
- Mention uncertainty and mundane/prosaic context when present in the source.
- Avoid sensational conclusions without source support.

## Portability

- Mac paths are not portable to Windows.
- Copied DBs search immediately, but local file paths may need a Windows rebuild.
- Use clean SQLite backups for transfer.

## Dependencies

- Embeddings use `BAAI/bge-small-en-v1.5` through `fastembed`.
- OCR uses local `tesseract`.
- Windows Tesseract install recommendation: `winget install UB-Mannheim.TesseractOCR`.

