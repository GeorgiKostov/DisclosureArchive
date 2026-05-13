# TODO

- Keep `DisclosureArchivePackage/` local-only and out of Git.
- Decide whether to move raw archive data from `DisclosureArchivePackage/ufo_war_release/` to a longer-term external/local data path outside the repo.
- Review the 35 OCR status candidates, especially photo-only FBI PDFs and low-text DOW mixed PDFs, before trying OCRmyPDF or PaddleOCR comparisons.
- Run a small second-pass benchmark on a few genuine OCR failures using OCRmyPDF and/or PaddleOCR, comparing against the Tesseract retry output.
- Add more curated retrieval eval queries and preserve the current 15/15 hybrid baseline before tuning ranking further.
- Review cases where the expected result is present but not rank 1, such as `new_haven_flying_saucers`, to decide whether reranking is useful.
- Use the local search UI for a manual research pass and note which result-card fields, filters, or suggestion types are missing.
- Add a saved-search or note-taking workflow if the local UI proves useful for repeated research passes.
- Review extracted `locations` rows for coordinate false positives and decide whether to add a larger offline gazetteer or a reviewed manual location override file.
- Consider replacing the simple no-tile result map with Leaflet/OpenStreetMap or a bundled offline map if richer geographic exploration becomes important.
- Decide whether to add optional real LLM summaries behind an explicit API-key setting after the local extractive summaries have been tested on noisy OCR results.
- Review the static public site manually as a publishing candidate and decide whether to add per-document routable pages, Pagefind-style indexing, or richer map browsing.
- Enable GitHub Pages in repository settings for the `gh-pages` branch root after the first static publish, then verify the public URL.
- Consider optional reranking after evidence-pack review exposes where hybrid ranking is insufficient.
