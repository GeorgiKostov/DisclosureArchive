# TODO

- Mount the external drive and run `EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make export-package`.
- Verify the external-drive package with `EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make verify-package`.
- On Windows, clone `https://github.com/GeorgiKostov/DisclosureArchive` and import the package following `README_WINDOWS_IMPORT.txt` or `scripts/windows_import_smoke.ps1`.
- On Windows, run a search smoke test for `lunar surface flash Grimaldi`.
- Decide whether to rebuild the DB on Windows to rewrite local file paths.
- Run broader OCR over the FBI/legacy scan-only PDFs when compute time is available.
- Plan the next MVP implementation around PDF classification, full resumable OCR, evidence-pack export, and optional reranking.
