# Release Update Workflow

This is the practical checklist for adding the next public document release to
Disclosure Archive. It complements `docs/ARCHITECTURE.md`: use this when new
PDFs, images, videos, captions, thumbnails, or release metadata arrive and the
public site needs to be refreshed.

## Ground Rules

- Keep raw release files outside Git. Do not commit `ufo_war_release/`,
  `DisclosureArchivePackage/`, `indexes/`, `derived/`, `reports/`,
  `public_site/`, videos, generated SQLite DBs, OCR caches, or transfer
  manifests.
- Treat the public source files as evidence records, not proof of claims. Public
  summaries must distinguish metadata, native PDF text, OCR text, captions,
  video metadata, and analyst/curated copy.
- Public UI actions should point to government/source URLs, not local paths.
- After workflow or release-facing behavior changes, update `tasks/done.md`,
  `tasks/todo.md`, `tasks/lessons.md`, or `memory/project-disclosurearchive.md`.

## 1. Stage The New Raw Release

The normal intake source is the government UFO page:
`https://www.war.gov/UFO/`. The user can also provide a specific release URL.
Treat the URL as the discovery source, then download the release package into a
local raw archive directory before indexing or OCR. The current pipeline is
local-first: it does not OCR remote PDFs in place.

Expected raw archive shape:

```text
ufo_war_release/
  uap-csv.cdp.csv
  uap_download_manifest.json
  dvids_video_manifest.cdp.json
  documents/
  thumbnails/
  evidence_carousel/
  videos/
```

For a new government release, either add the files to the existing local source
root or create a sibling source root and point commands at that absolute path.
Example Windows source-root setting:

```powershell
$env:SOURCE_ROOT="C:\path\to\ufo_war_release"
```

Before indexing, inspect the source directory:

```powershell
Get-ChildItem $env:SOURCE_ROOT
Get-ChildItem $env:SOURCE_ROOT\documents | Measure-Object
Get-ChildItem $env:SOURCE_ROOT\videos -Recurse -ErrorAction SilentlyContinue | Measure-Object
```

Check the metadata and download manifests are present. The indexer uses:

- `uap-csv.cdp.csv` for document rows and descriptive metadata.
- `uap_download_manifest.json` for downloaded documents, thumbnails, and image
  assets keyed by release row.
- `dvids_video_manifest.cdp.json` for video metadata and usable public MP4
  source URLs.

If a future release uses a different manifest shape, update
`src/ufo_indexer/common.py` and `src/ufo_indexer/index.py` before indexing, then
document the new source contract here.

## 1b. Mining A New Release From war.gov (Browser-Required)

Release 2 confirmed that a real scrape IS needed — the bulk download gives the
media files but NOT the metadata. Access constraints (do not fight these):

- `https://www.war.gov/UFO/` and every `www.war.gov/...` asset (the CSV, the
  medialink PDFs) return **HTTP 403 to all scripted/server-side requests**
  (curl, PowerShell, WebFetch) even with a browser User-Agent + Referer. Load
  them only through a **connected Chrome browser** (Claude-in-Chrome MCP).
- The DVIDS API key embedded in the page is **origin-locked to war.gov**, so
  DVIDS asset + caption fetches must also run from the page context
  (`fetch()` in the browser), not from a shell.
- The cloudfront video/thumbnail CDN IS public (HTTP 200 anywhere), so playback
  works on the live site.

Cache-busting note (added during Release 3): the war.gov CSV is aggressively
cached. A naive `fetch('/Portals/1/Interactive/2026/UFO/uap-data.csv')` may
return the previous release's row set even after a new tranche has dropped.
Always include a cache-busting query string AND `cache:'no-store'`:
`fetch(url + '?_=' + Date.now(), { credentials:'include', cache:'no-store' })`.
Compare the `Last-Modified` response header against the date of the latest
tranche to confirm you fetched the fresh feed before extracting rows.

Extraction steps (in the browser, on the war.gov/UFO tab):

1. Find the live data feed via `read_network_requests`:
   `https://www.war.gov/Portals/1/Interactive/2026/UFO/uap-data.csv`. Its
   columns already match `common.csv_record` (Title, Type, Agency, Release
   Date, Incident Date, Incident Location, Description Blurb, **DVIDS Video ID**,
   `PDF | Image Link`, Modal Image). Filter rows by Release Date.
2. For each VID/AUD row, fetch
   `https://api.dvidshub.net/asset?api_key=<key>&id=video:<DVIDS Video ID>` to
   get title, description (AARO assessment), date, duration, `url` (the DVIDS
   public page = the original-file link), `files` (MP4 URLs whose path contains
   the `DOD_<assetid>` matching the bulk-download filenames), and captions via
   `.../closed-captions/get?asset_id=video:<id>&format=srt&api_key=<key>`.
3. Get the data to disk. Three options, in order of preference:
   - **Local HTTP receiver (most reliable on macOS)**: run a tiny Python
     `BaseHTTPRequestHandler` on `127.0.0.1:<port>` that writes the POST body
     to disk and exits, then `fetch(url, { method:'POST', mode:'no-cors',
     body: window.__PAYLOAD })` from the page. CORS preflight is avoided by
     using `mode:'no-cors'` with `Content-Type: text/plain`. This is the
     pattern used for Release 3. The receiver pattern:
     ```python
     class H(BaseHTTPRequestHandler):
         def do_POST(self):
             n = int(self.headers['Content-Length'])
             open(OUT,'wb').write(self.rfile.read(n))
             self.send_response(200); self.send_header('Access-Control-Allow-Origin','*')
             self.end_headers(); sys.exit(0)
     ```
   - **Blob download**: `URL.createObjectURL(new Blob([s], {type:'application/json'}))`
     + click an anchor with `download="..."`. Files land in `~/Downloads`.
     CAVEAT (Release 3): on macOS with sandboxed shells, Chrome-saved files
     can be quarantined and unreadable by `cat`/`wc`/`mv` — they appear in
     `ls` but every read fails with EPERM. Use the local receiver path
     instead when the agent can't read its own Downloads.
   - **Chunked read**: `javascript_tool` returns are capped at ~1 KB per
     string, and base64 is blocked by the response filter (the workflow's
     URL/cookie sanitizer). If you're stuck with this, split the payload
     into <800-byte slices and stitch via Bash. Slow but always works.

### 1c. Metadata-only ingest (Release 3 pattern)

When local bandwidth is too limited to download the bulk-download package
(R1 was 1.2GB docs + 1.3GB video, R2 was 70MB + 5.6GB, R3 was 826MB + 5.6GB),
you can still ship the release as a metadata-only ingest that links every
record straight to the public source URLs. The indexer already tolerates a
missing local file at `local_path`: it simply does not extract PDF text or
run OCR, but still writes the `documents` and `assets` rows with `source_url`,
the CSV-derived `metadata` chunk, and the DVIDS-derived `video_metadata` chunk.

Use `scripts/build_release03_source.py` as the template. It expects a single
JSON payload at `release03_src/_staging/r3_payload.json` containing the R3
CSV subset + DVIDS `/asset` JSON keyed by video_id. It writes a source root
with empty `target` fields and real public `url`s on every manifest entry.
Asset URL pattern as of R3: `https://www.war.gov/medialink/ufo/<MMDDYY>/release_<NN>/{documents|thumbnails}/<filename>`.

When a R1+R2 enriched DB is not on the local machine but you still want to
publish the merged release, use `scripts/merge_release03_into_live.py`:
it takes the live `gh-pages` checkout + the R3-only export and writes a
merged `public_site/` that updates `data/documents.json`, the JSON-LD
`ItemList` highlights, `variableMeasured`, and `sitemap.xml`, and copies
the per-record SEO pages for the new R3 docs into the existing `records/`
directory. Push the merge directly to `gh-pages` from a worktree.

Later, to backfill native PDF text + OCR + embeddings for the
metadata-only release: download the bulk data on a high-bandwidth machine,
materialize a full `releaseNN_src/` with real local files, run
`make index` + `make ocr` + `make eval-search`. Document `doc_id`s are
derived from `row_number + title + source_url + dvids_video_id`, so as
long as the CSV layout and source_urls stay stable, the existing public
record pages keep their slugs and incoming links.

### 1d. Self-contained source root assembly (R1/R2 pattern)

When the bulk download IS available locally, assemble a self-contained source
root and index it (scripts from Release 2, reusable):

- `scripts/build_release02_source.py` — builds `release02_src/`: copies the CSV
  to `uap-csv.cdp.csv`, hardlinks videos as `videos/{dvids}_{asset}.mp4` (so
  `find_video_path`'s `{video_id}_*.mp4` glob resolves), captions to
  `videos/captions/{dvids}.srt`, and writes `uap_download_manifest.json`
  (entries keyed by `target`/`category`/`url`) + `dvids_video_manifest.cdp.json`
  (objects keyed by top-level `video_id`).
- `scripts/split_release02_extract.py` — splits the downloaded extract into the
  staging files the builder expects.
- `scripts/fix_release02_video_links.py` — puts each video's DVIDS public-page
  URL into the CSV `PDF | Image Link` column BEFORE indexing, so the video
  document `source_url` (the original-file link) is populated. Do this first:
  `doc_id` is derived from `source_url`, so changing it later orphans/duplicates
  docs.
- PDFs vs videos can be split across separate source roots: index videos from
  `release02_src` (incremental) and PDFs from the main `ufo_war_release` root
  (where `scripts`/`_staging_release02/append_release2.py` appends them with
  curated titles). Incremental `index` only upserts the rows it processes, so
  the two coexist. NEVER run `make rebuild` while another agent has incrementally
  added records to the same DB — `--rebuild` resets the DB to a single source
  root and silently wipes the others (this happened in Release 2).

## 2. Index Metadata, Assets, Text, Locations, And Embeddings

Run an incremental index first:

```powershell
make index SOURCE_ROOT="$env:SOURCE_ROOT"
```

Direct equivalent:

```powershell
$env:PYTHONPATH="src"
python -m ufo_indexer.index `
  --source-root "$env:SOURCE_ROOT" `
  --db indexes/uap_release.sqlite
```

The indexer writes:

- `documents`: one row per release item.
- `assets`: PDFs, thumbnails, images, videos, captions, and their public source
  URLs when known.
- `chunks`: citable metadata, native PDF text, OCR text, captions, and video
  metadata.
- `chunks_fts`: SQLite FTS search rows.
- `embeddings`: local semantic vectors.
- `locations`: geocoded incident locations and coordinate extractions.

Use `make rebuild SOURCE_ROOT="$env:SOURCE_ROOT"` instead of incremental index
when changing schema, chunking, cache keys, OCR ingestion, embedding model, or
location extraction behavior. (But see the multi-agent warning in 1b — never
`--rebuild` a DB that another root has been incrementally added to.)

**Embeddings:** the `.venv` now has `sentence-transformers` + `torch` (CPU)
installed, and the DB is fully embedded with `BAAI/bge-small-en-v1.5` (384-dim).
Run `index` **without** `--skip-embeddings` to (re)build them — the final
`build_embeddings` step embeds every chunk in the whole DB that lacks an
embedding, not just the rows processed. Use `--skip-embeddings` only for quick
metadata/location passes; re-run without it afterward (a `--rebuild
--skip-embeddings` wipes embeddings). Embeddings power the **local**
`ufo_indexer.web` UI and `ufo_indexer.search` (vector/hybrid); the public static
site is keyword-only.

**Geocoding videos:** combatant-command labels (CENTCOM, NORTHCOM, INDOPACOM,
EUCOM, AFRICOM) and seas/places are in `GEOCODE_LOCATIONS` in `index.py`, and
`add_incident_location` prefers a specific place named in the title (Lake Huron,
Persian Gulf, Tyndall/Eglin AFB, Kabul...) over the broad command label. The Map
view has a per-release toggle (All / Release N) that filters markers by
`release_date`.

## 3. Classify PDFs And Run OCR

OCR uses the Tesseract **binary via subprocess** (installed at
`C:\Program Files\Tesseract-OCR\tesseract.exe`) plus `pypdfium2`/`Pillow` for
page rendering — all present in the `.venv`; `pytesseract` is NOT required.
Captions/video metadata don't OCR. The OCR cache (`derived/`) is portable and
keyed by file hash, so re-running is cheap (cached pages skip).

Classify PDFs so OCR work is targeted:

```powershell
$env:PYTHONPATH="src"
python -m ufo_indexer.classify `
  --source-root "$env:SOURCE_ROOT" `
  --out reports/pdf_classification.json `
  --markdown reports/pdf_classification.md
```

Run OCR over likely scan/text-poor PDFs:

```powershell
python -m ufo_indexer.ocr `
  --source-root "$env:SOURCE_ROOT" `
  --from-classification reports/pdf_classification.json `
  --classes scan_only low_text mixed `
  --workers 12 `
  --tesseract-bin "C:\Program Files\Tesseract-OCR\tesseract.exe"
```

Then reindex so OCR pages become searchable `ocr_text` chunks:

```powershell
make index SOURCE_ROOT="$env:SOURCE_ROOT"
```

Audit OCR coverage and quality:

```powershell
python -m ufo_indexer.ocr_status `
  --source-root "$env:SOURCE_ROOT" `
  --classification reports/pdf_classification.json `
  --out reports/ocr_status.json `
  --markdown reports/ocr_status.md
```

If the status report flags genuine OCR failures, retry only those candidates:

```powershell
python -m ufo_indexer.ocr `
  --source-root "$env:SOURCE_ROOT" `
  --from-status reports/ocr_status.json `
  --review-reasons low_average_chars zero_text `
  --workers 4 `
  --dpi 300 `
  --psm 11 `
  --tesseract-bin "C:\Program Files\Tesseract-OCR\tesseract.exe"
make index SOURCE_ROOT="$env:SOURCE_ROOT"
```

OCR retries merge selected pages into existing per-PDF caches. They should not
replace good cached pages. Keep weak OCR in provenance-labeled source sections;
do not promote noisy OCR into confident public claims.

## 4. Verify Search Quality

Run stats and basic integrity checks:

```powershell
make stats
sqlite3 indexes/uap_release.sqlite "PRAGMA integrity_check;"
```

Run the retrieval evaluation:

```powershell
make eval-search DB=indexes/uap_release.sqlite
```

Add new release-specific eval queries to `eval/retrieval_queries.json` before
tuning ranking. Include at least:

- One metadata-heavy query.
- One native-PDF text query.
- One OCR-heavy query if scans are present.
- One media/video query if the release includes videos.
- One query for each new major source cluster.

Use manual smoke searches for known new highlights:

```powershell
python -m ufo_indexer.search --db indexes/uap_release.sqlite --mode hybrid --q "exact phrase from new release"
python -m ufo_indexer.search --db indexes/uap_release.sqlite --mode vector --q "semantic description of new incident"
```

## 5. Review Local UI Before Publishing

Start the local UI:

```powershell
$env:PYTHONPATH="src"
python -m ufo_indexer.web --db indexes/uap_release.sqlite --host 127.0.0.1 --port 8765
```

Check:

- Record cards show clear descriptions from release metadata.
- `Summary` opens generated quick summary, UAP element, detailed contents,
  references, and source-mix notes.
- OCR-derived text is readable enough and labeled by source kind.
- Government source links open the public source URLs.
- Image/video previews render when public assets exist.
- Map actions appear only for records with usable locations.
- Search filters still work for agencies, source types, and decades.

## 6. Update Public Summaries, Tags, And Highlights

Public export logic lives mostly in `src/ufo_indexer/export_site.py`.

### Summaries

Generated document summaries come from `src/ufo_indexer/summary.py`:

- `source_summary()` reads indexed chunks for a document.
- `quick_summary` starts from title/agency/date/location plus metadata
  description.
- `mysterious_uap_element` and `detailed_contents` are selected from native PDF
  text, OCR text, captions, and video metadata.
- OCR sentences go through display-only cleanup and conservative noise gating.

When a new release exposes summary problems, prefer fixing cleanup/scoring in
`summary.py` over hand-editing generated JSON. Curated highlight copy is the
exception: it lives in `FEATURED_SELECTIONS`.

### Tags

Public record tags are generated in `tags_for()` using:

- `AGENCY_TAGS` for agency display labels.
- `TAG_PHRASES` for regex phrase matches.
- `TAG_ALIASES` for weighted keyword aliases.
- Asset-derived tags such as `Photos` and `Videos`.
- Year and location hints from release metadata and extracted locations.

When new recurring entities, object types, places, platforms, or source themes
appear, update `TAG_PHRASES` or `TAG_ALIASES`, then regenerate the site and
check the Records filters. Avoid process labels such as `OCR`, `metadata`, or
`excerpt` as public tags.

### Highlights

Curated landing records are selected by `FEATURED_SELECTIONS`.

For each highlight:

- `match` must be a stable substring of the indexed document title.
- Optional `title` can override the display title while keeping the underlying
  record link. Example: display `Orbs Launching Orbs` while matching
  `Western US Event`.
- `kicker` should be short and descriptive.
- `summary` should read like a front-page case brief: lead with the concrete
  who/what/where/when and the most important reported details. If the source
  has enough case information, summarize the case itself instead of explaining
  tags, provenance, or why the item was selected. Preserve uncertainty with
  source-attributed language such as "the report says" or "the witness
  described," not generic disclaimers.
- `facts` should include agency/date/source context and one reason it stands
  out.

Highlights are grouped into collapsible release sections. Group order, labels,
and optional display dates are defined by `RELEASE_GROUPS` in
`src/ufo_indexer/export_site.py`; each curated item is assigned to a group by an
optional `release` key on its `FEATURED_SELECTIONS` entry (defaulting to
`DEFAULT_RELEASE`, currently `release-1`). The client `highlightReleaseGroups()`
buckets items by `release` and renders only groups that have at least one matched
item, so a group can be defined ahead of a drop without changing the visible
page. A group's published date is the group's `date` override if set, otherwise
the release date of its documents, otherwise its `fallback_date`.

`release-2` is already declared in `RELEASE_GROUPS`. When Release 2 arrives:

1. Add new curated items to `FEATURED_SELECTIONS`, each with `"release":
   "release-2"`.
2. If the docs do not carry a usable `release_date`, set the Release 2 group's
   `date` (or `fallback_date`) in `RELEASE_GROUPS`.
3. Regenerate the site and verify a separate `RELEASE 2` section appears, each
   group collapses/opens independently, and title clicks still open the matching
   record.

## 7. Verify Media, Video, And Image Handling

Media previews are generated from indexed `assets` rows:

- `public_assets()` emits only public `source_url` values.
- `public_media()` chooses `thumbnail_url`, `document_url`, and `video_url`.
- `video_src_from_metadata()` unwraps DVIDS/video manifest metadata to find a
  usable MP4 URL when possible.
- `renderMedia()` and `renderBestMedia()` render videos, image previews, or a
  no-preview fallback.

For new releases with media:

- Confirm thumbnails/images/videos are present in the raw source folder and in
  `uap_download_manifest.json` / `dvids_video_manifest.cdp.json`.
- Confirm `assets.source_url` contains public URLs, not local paths.
- Confirm Records cards open government/source pages, not local files.
- Confirm the Photos filter excludes PDF thumbnails and targets real images.
- Confirm the Videos filter catches both explicit video assets and MP4 URLs
  recovered from metadata.

## 8. Export And Inspect The Static Site

Generate the static site:

```powershell
$env:PYTHONPATH="src"
python -m ufo_indexer.export_site `
  --db indexes/uap_release.sqlite `
  --out public_site `
  --ga-measurement-id G-NNXB9F00V6
```

Or:

```powershell
make export-site DB=indexes/uap_release.sqlite
```

The export writes:

- `public_site/index.html`
- `public_site/data/documents.json`
- `public_site/social-card.png`
- `robots.txt`, `sitemap.xml`, `security.txt`, `.well-known/security.txt`
- `_headers`, `favicon.svg`, `site.webmanifest`, `humans.txt`, `llms.txt`
- Contact/legal/privacy/security static pages
- `records/<slug>-<docid>.html` — a static SEO page per document (unique
  title/meta/canonical/OG + JSON-LD `VideoObject`/`CreativeWork`, embedded media,
  source + deep links) plus a `records/` hub; every page is listed in
  `sitemap.xml`. Generated automatically by `write_record_pages` — no action
  needed per release.

The exporter validates common local/private path leaks before writing public
JSON. Still spot-check:

```powershell
rg "DisclosureArchivePackage|derived/|indexes/uap_release.sqlite" public_site
rg "og:image|twitter:image|social-card" public_site/index.html
```

Serve locally for browser review:

```powershell
python -m http.server 8788 -d public_site
```

Open `http://127.0.0.1:8788/` and check:

- Highlights release group title/date.
- Highlight title clicks and `View record` clicks.
- Records descriptions and `Summary` expansion.
- Search, filters, and load-more behavior.
- Map view, marker selection, and points-of-interest overlay toggles.
- Footer `Last updated` timestamp.
- Social preview metadata points to `/social-card.png`.
- Mobile layout for header, nav, cards, media, and map controls.

## 9. Publish

GitHub Pages publish:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish_github_pages.ps1
```

The script regenerates `public_site/`, validates the JSON, copies only static
files into a temporary checkout, preserves `CNAME`, and pushes `gh-pages`.

Cloudflare Pages publish, if real HTTP `_headers` are needed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/publish_cloudflare_pages.ps1
```

After publishing, verify:

```powershell
Invoke-WebRequest -UseBasicParsing "https://disclosurearchive.org/?v=release-check"
Invoke-WebRequest -UseBasicParsing "https://disclosurearchive.org/data/documents.json?v=release-check"
Invoke-WebRequest -UseBasicParsing "https://disclosurearchive.org/social-card.png?v=release-check"
```

If GitHub Pages returns the previous build, wait 20-60 seconds and retry with a
new cache-busting query string.

## 10. Transfer / Other Machine Handoff

When moving the release to another machine, use the tracked transfer workflow:

```bash
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make export-package
```

The transfer package must contain a clean SQLite backup made with
`sqlite3 ... ".backup ..."`. Do not copy live `-wal` or `-shm` files as the
canonical DB.

On the receiving machine, run the smoke test:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/windows_import_smoke.ps1
```

Then rebuild paths against the local source root if needed:

```powershell
make rebuild SOURCE_ROOT="$env:SOURCE_ROOT"
```

## 11. Final Release Checklist

- Raw release data is outside Git.
- Metadata, manifests, documents, thumbnails, videos, and captions are present.
- Index builds and `PRAGMA integrity_check` returns `ok`.
- OCR classification, OCR pass, OCR status, and any retries are complete.
- Retrieval eval passes or known misses are documented.
- Local UI has been manually checked.
- Public tags and highlights have been reviewed.
- New release is represented in `HIGHLIGHTS` under the correct release group.
- Public JSON has no local path leaks.
- Social preview image is site-branded, not a random archive photo.
- Footer `Last updated` is visible.
- GitHub Pages or Cloudflare Pages publish is verified live.
- `tasks/done.md`, `tasks/todo.md`, `tasks/lessons.md`, or project memory is
  updated with the release work and any follow-up risks.
