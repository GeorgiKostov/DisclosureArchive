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
- Local browser search UI with health, search, and evidence-pack API endpoints.
- Windows transfer package instructions.
- Mac export and package verification scripts.
- Windows import smoke-test script.
- Agent scaffold for future continuity.
- Search-result media enrichment: the web API now attaches related indexed assets to each result so the UI can preview thumbnails/images/videos and link related PDFs.
- Location enrichment: `locations` table stores map-ready latitude/longitude rows from conservative incident-location geocoding and explicit decimal/DMS coordinate extraction with precision/confidence/method labels.
- Search-result readability layer: web results include deterministic local readable summaries and cleaned source excerpts over indexed chunk text/OCR, with no external LLM call required.
- Source-summary UI action: each result card has `Summarize source`, backed by `/api/source-summary`, which summarizes the whole indexed source document/PDF from chunks with key points, page/chunk references, and source-mix notes.

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
- Local search UI added via `python -m ufo_indexer.web --db indexes/uap_release.sqlite --host 127.0.0.1 --port 8765`; it reuses existing search/evidence-pack code and shows summaries, references, suggestions, OCR labels, evidence-pack previews, and guarded `Open source` links for indexed local files.
- Current location-enriched DB after a skip-embedding index pass: 105 `locations` rows, 305 assets, 7,610 chunks, and 7,610 embeddings.
- Local search UI now includes a simple result map, inline media previews, related PDF links, and a `Government source` button backed by stored WAR/DVIDS URLs.
- Local search UI now shows a `Readable summary` and collapsible `Cleaned source excerpt` on each result card to reduce OCR noise while keeping the raw provenance nearby.
- Browser verification passed for the `Summarize source` flow: search results showed buttons, clicking one produced a summary containing references and source-mix/verification notes.
- Source-summary UI now shows staged progress text while the browser waits for `/api/source-summary`; a short minimum display time keeps the feedback visible even when summaries return quickly.
- `/api/source-summary` now returns three explicit sections for the selected source: quick summary, mysterious/UAP element, and detailed contents, plus page/chunk references and source-mix notes.
- Native PDF read test artifact created for `NASA-UAP-D3, Gemini 7 Transcript, 1965`: `reports/native_pdf_read_nasa_uap_d3_gemini_7_transcript_1965.md`. It used `pdfplumber` only, no OCR, and found native text on 1/3 pages with 2,421 extracted characters.
- Search UI cards are now document-centered: thumbnail/media preview, cleaned document-level OCR/PDF summary as the main card text, topic tags, references, government source link, local PDF link, and `Expand detailed summary`.
- The sidebar map, suggestions, evidence-pack preview, raw local paths, chunk IDs, and default cleaned-excerpt block are hidden from the primary UI to keep the surface focused.
- The visible metadata chip row (`release metadata`, agency, date, location, page) was removed from cards because tags and summaries carry the useful context more cleanly.
- Result card actions now use compact accessible SVG icon buttons: government link, local PDF, and detailed summary.
- Result card media previews are locked into a fixed right-side rail; expanded summaries grow only the left text column.
- Static public export is now available via `python -m ufo_indexer.export_site --db indexes/uap_release.sqlite --out public_site` or `make export-site`. It writes `public_site/index.html` plus `public_site/data/documents.json` with 162 precomputed deterministic document summaries, public government/media URLs, tags, locations, and structured references.
- The public export deliberately excludes local file paths, raw downloads, full OCR text, generated SQLite databases, and derived OCR caches; the exporter validates common private/local path markers before writing publishable JSON.
- Release UI cleanup: result actions now emphasize public government/web links only, detailed summaries use a labeled `Summary` button, and the static public page has a dark terminal-style visual treatment.
- GitHub Pages publishing can use `powershell -ExecutionPolicy Bypass -File scripts/publish_github_pages.ps1`; it pushes only generated static files to `gh-pages` and leaves generated artifacts ignored on `main`.
- First `gh-pages` publish succeeded to origin at commit `43e0adaa608e6e91ea1de5b9830acd61590964c3`; `https://georgikostov.github.io/DisclosureArchive/` returned 404 right after publish, so enable Pages from `gh-pages` branch root or wait for provisioning before public smoke testing.
- Public globe update: the generated static viewer now overlays country outlines on the interactive globe, and checkpoint clicks open a compact document overview with summary text, source link, and a `View result` action.
- Public globe controls update: the globe no longer auto-spins, drag is user-controlled rotation, scroll-wheel zoom moves the camera in/out, and selected checkpoints/list items are highlighted blue.
- Public header update: the site is now named `Disclosure Archive`, and clicking the title resets search, filters, open summaries, and globe checkpoint selection.
- Public analytics support: `python -m ufo_indexer.export_site --analytics-domain <domain>` or `DISCLOSURE_ANALYTICS_DOMAIN=<domain>` injects a Plausible-compatible analytics script and coarse UI event hooks; exports without a domain remain analytics-free.
- Custom-domain publish support: `scripts/publish_github_pages.ps1` now writes a `CNAME` file for `disclosurearchive.org` by default, or the value from `DISCLOSURE_CUSTOM_DOMAIN` / `-CustomDomain`; the `gh-pages` branch was republished at `f272268bb5efe8cd4a7ba106d382d0eb8b260d92`.
- Public custom-domain verification: `https://disclosurearchive.org/` serves the generated static site over GitHub Pages, and `https://www.disclosurearchive.org/` redirects to the apex domain.
- Public tag update: static export tags now avoid process/source labels such as OCR, excerpt, metadata, and location; tags are generated from curated phrases/entities, agency/year/location hints, media type, object descriptors, and recurring UAP themes.
- Public media layout update: real image/video records render with a larger media preview area, while ordinary document/PDF thumbnails remain compact; the Photos filter/tag now targets actual image assets, not generated PDF thumbnails.
- Public globe layout update: the globe is visible by default, the checkpoint side list/toggle is removed, marker clicks only update the popup/selected marker, and result-opening actions no longer force `scrollIntoView`.
- Public mobile globe fix: the canvas now uses explicit touch handling for one-finger drag rotation, and selected location popups include a top-right `x` close control that clears the selected marker.
- Summary readability update: `src/ufo_indexer/summary.py` now normalizes common mojibake/OCR glyphs, strips divider noise, scores sentences for OCR artifacts, rejects weak OCR sentences, and falls back to document metadata when passages are too noisy.
- Responsive UI update: `src/ufo_indexer/export_site.py` and `src/ufo_indexer/web.py` now use narrower mobile wraps, full-width mobile filter/action controls, stacked media previews, safer long-text wrapping, and mobile-sized globe popups.
- Globe zoom update: the public static globe no longer shows navigation tips; desktop wheel zoom remains, and mobile/touch zoom now uses two active pointers to pinch the camera in and out.
- Public best-of update: `src/ufo_indexer/export_site.py` now exports `featured_documents` with curated summaries for Western US Event, FBI September 2023 Composite Sketch, Papua New Guinea cable, Apollo 17 transcript, Gemini VII audio, and the wartime foo-fighter file. Each card links back into the searchable index result.
- Public layout follow-up: the generated site initially opened with a curated `Best Of` section, then the search/filter/results workbench. The globe was hidden by default behind an `Open location globe` control and still used native touch events for one-finger rotation and two-finger pinch zoom.
- Auto Pages publish: `scripts/install_auto_pages_publish.ps1` configures `core.hooksPath=.githooks`; `.githooks/pre-push` watches pushes to `origin/main` and runs `scripts/publish_github_pages.ps1` from the local machine before the main push completes so ignored DB/static artifacts still stay out of Git. Set `DISCLOSURE_SKIP_PAGES_PUBLISH=1` to skip once.
- Public UX rework: `src/ufo_indexer/export_site.py` now renders a two-view static app with a `HIGHLIGHTS` landing page and a separate search/globe workbench. Highlights are expanded to 18 records, result cards no longer show duplicate `Refs:` rows, and the desktop globe height is capped to fit in the viewport.
- Public SEO/security update: the static export now writes canonical/social/JSON-LD metadata, `robots.txt`, `sitemap.xml`, root and well-known `security.txt`, a CSP/referrer meta policy, and a `_headers` template for hosts that support static response headers. GitHub Pages still cannot apply custom `_headers`.
- Public footer/legal notice update: the static export initially rendered copyright, contact, Legal / Impressum, privacy, security, sitemap, and source-code sections in the page footer. The contact email defaults to `contact@rebuilt.cards` and can be overridden with `DISCLOSURE_CONTACT_EMAIL` / `--contact-email`.
- Public footer cleanup update: the static export now keeps the homepage footer compact and writes separate minimal `contact.html`, `legal.html`, `privacy.html`, and `security.html` pages. The generated public pages no longer render the raw contact email or raw `mailto:` link; the contact page opens the configured address only after a click, and `security.txt` points to the contact page plus GitHub issues.
- Public summary cleanup update: highlight cards now use longer curated summaries with `Read more` / `Show less` expansion, while public and local quick document summaries stay on metadata/description text instead of appending noisy OCR/native source snippets to the visible card surface.
- User preference: after finishing public static site changes, run `scripts/publish_github_pages.ps1` and push the regenerated `gh-pages` site unless explicitly told not to.
- Public Map view update: `src/ufo_indexer/export_site.py` now has separate `Highlights`, `Search`, and `Map` navigation. The globe is active only in `Map`; archive marker clicks render the selected document below the globe, and the old in-globe popup surface was removed.
- Public Map overlay update: the Map legend has bottom-right toggles for selected public military-base and nuclear-site reference points. Nuclear overlay points include public missile-wing bases plus nuclear power/research sites; the overlay is intentionally a comparison aid, not an exhaustive infrastructure dataset.
- Public analytics update: the static exporter and Pages publisher now support optional Google Analytics 4 / Google tag injection via `--ga-measurement-id` or `DISCLOSURE_GA_MEASUREMENT_ID`. Existing coarse UI events go to both Plausible and GA when configured, and search text is still not sent, only query length.
- Live analytics configuration: Disclosure Archive uses Google Analytics Measurement ID `G-NNXB9F00V6`. `Makefile` and `scripts/publish_github_pages.ps1` default to that ID so future generated Pages publishes keep GA enabled unless explicitly overridden.
- Public launch polish update: the Map overlay legend is collapsible, the military/nuclear overlay catalog now includes selected public sites across the Middle East, Japan, Korea, Guam, Europe, Pakistan/India, and other plotted regions, and overlay markers are filtered to facilities within 500 km of archive map points. The static export also writes `favicon.svg`, `site.webmanifest`, `humans.txt`, and `llms.txt`.

1. Review the 35 OCR status candidates and separate true image/photo-only pages from OCR failures.
2. Add more curated retrieval eval queries before tuning hybrid scoring or adding reranking.
3. Use the local search UI for a small manual research pass and note what fields, filters, or saved-note workflows are missing.
4. Decide whether a small OCRmyPDF or PaddleOCR comparison is warranted for genuinely weak OCR pages.
5. Review `locations` rows for false positives and decide whether to add a larger offline gazetteer/manual override file.
6. Evaluate whether optional real LLM summaries are worth adding behind an explicit API-key/config setting.
7. Review the static public site as a publishing candidate and decide whether per-document routable pages or richer client-side search are needed.
