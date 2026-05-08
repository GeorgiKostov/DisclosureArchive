# TODO

- Keep `DisclosureArchivePackage/` local-only and out of Git.
- Decide whether to move raw archive data from `DisclosureArchivePackage/ufo_war_release/` to a longer-term external/local data path outside the repo.
- Review the 35 OCR status candidates, especially photo-only FBI PDFs and low-text DOW mixed PDFs, before trying OCRmyPDF or PaddleOCR comparisons.
- Run a small second-pass benchmark on a few genuine OCR failures using OCRmyPDF and/or PaddleOCR, comparing against the Tesseract retry output.
- Add more curated retrieval eval queries and preserve the current 15/15 hybrid baseline before tuning ranking further.
- Review cases where the expected result is present but not rank 1, such as `new_haven_flying_saucers`, to decide whether reranking is useful.
- Add a small evidence-pack review workflow that can save selected result sets for manual research notes.
- Consider optional reranking after evidence-pack review exposes where hybrid ranking is insufficient.
