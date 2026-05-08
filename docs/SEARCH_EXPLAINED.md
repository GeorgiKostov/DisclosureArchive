# DisclosureArchive Search Explained

This document explains, in plain English, how the local archive search works.

## 1. The Raw Archive

The original files live here on this Windows machine:

```text
DisclosureArchivePackage\ufo_war_release
```

That folder contains the actual PDFs, images, videos, captions, thumbnails, and
release metadata. The search tools do not edit those raw files. They read them
and build searchable outputs elsewhere.

## 2. Text Extraction

Search needs text. The archive has several kinds of source material:

- PDFs that already contain selectable text.
- Scanned PDFs that are really page images.
- Metadata from the release CSV.
- Video metadata and captions.

For normal PDFs, the indexer extracts native PDF text directly.

For scanned PDFs, OCR is needed. OCR means optical character recognition: the
computer looks at an image of a page and tries to turn the visible letters into
machine-readable text. This project uses local Tesseract OCR.

OCR text is useful, but it can contain errors. That is why OCR-derived results
are labeled as `ocr_text` in the search UI and evidence packs.

## 3. Chunks

The indexer splits extracted text into smaller pieces called chunks.

A chunk is a searchable unit with provenance. For example:

```text
Title: NASA-UAP-D2, Apollo 17 Transcript, 1972
Source kind: pdf_text
Page: 16
Text: ...I just saw a flash on the lunar surface...
```

Chunks make search practical because the system can return the exact page-sized
or paragraph-sized piece that matched, instead of only saying "this PDF matched."

Current verified index size:

```text
Documents: 162
Chunks: 7610
OCR chunks: 6388
Embeddings: 7610
```

## 4. The SQLite Index

The main search database is:

```text
indexes\uap_release.sqlite
```

It stores:

- `documents`: one row per release item.
- `assets`: local file paths for PDFs, images, videos, and captions.
- `chunks`: searchable text pieces with title, agency, page, and source kind.
- `chunks_fts`: SQLite full-text search index for keyword search.
- `embeddings`: vector embeddings for semantic search.

The app searches this database. It does not reread every PDF each time you type
a query.

## 5. Keyword Search

Keyword search is like Ctrl+F across the whole archive.

Example:

```text
Grimaldi flash lunar surface
```

Keyword search is best for:

- exact names
- places
- dates
- document titles
- phrases from a source

It can struggle when OCR misspells a word or when you describe an idea using
different words than the document used.

To help with noisy OCR, keyword search first tries strict full-text matching. If
that returns nothing for a multi-word query, it falls back to a broader OR-style
search. This improves recall without changing exact matches that already work.

## 6. Semantic Vector Search And Embeddings

Semantic search is meaning-based search.

An embedding is a list of numbers that represents the meaning of a text chunk.
The individual numbers are not meaningful to humans by themselves. Their value is
that similar text ends up near similar text in vector space.

For example, these two phrases are different words but similar meaning:

```text
pilots saw orange lights flare in formation
aircrew observed lights splitting apart in a line
```

Vector search can find related chunks even when the exact words do not match.

Vector search is best for:

- natural-language descriptions
- fuzzy ideas
- "find things like this"
- cases where witnesses used different words for similar events

It can return conceptually related results that are not exact hits, so it is best
when combined with keyword search.

## 7. Hybrid Search

Hybrid search combines keyword search and vector search.

That is the default search mode in the local web UI because it usually gives the
best balance:

- keyword search catches exact names, dates, and phrases
- vector search catches meaning and related descriptions

The current retrieval evaluation passes all curated hybrid checks:

```text
Hybrid retrieval eval: 15/15
```

## 8. Source Kinds

Search results are labeled by source kind:

```text
metadata
pdf_text
ocr_text
caption
video_metadata
```

These labels matter.

- `metadata` means the result came from release metadata.
- `pdf_text` means it came from native text inside a PDF.
- `ocr_text` means it came from OCR applied to a scanned page.
- `caption` means it came from video caption text.
- `video_metadata` means it came from video title/description metadata.

Do not treat all source kinds as equally reliable. OCR text is especially useful
for discovery, but it should be checked against the original PDF before making a
strong claim.

## 9. What Happens When You Search In The UI

When you type a search into the local browser UI:

1. The page sends your query to the local server.
2. The server searches `indexes\uap_release.sqlite`.
3. Hybrid mode runs both keyword and vector search.
4. Results are ranked.
5. The UI displays result cards with title, agency, date, source kind, page,
   chunk ID, snippet, and local file path.
6. If a result has a local file, the UI shows an `Open source` link.
7. The UI generates a short extractive summary from the top results.
8. The UI suggests follow-up searches based on titles, agencies, locations,
   source kinds, and repeated terms.

Everything is local. The search UI runs at:

```text
http://127.0.0.1:8765
```

## 10. Opening Original Sources

The UI includes `Open source` links for indexed local files.

These links use a guarded local `/file` endpoint. The server only opens files
that are referenced by the index. It is not a general file browser.

This lets you click from a result to the actual PDF, image, or video source.

## 11. Evidence Packs

Evidence packs are LLM-ready exports from search results.

They include:

- query
- rank and score
- title
- agency
- incident date and location
- source kind
- page number
- chunk ID
- local path
- snippet or full chunk text
- provenance guidance

Evidence packs are useful when you want to ask an LLM to summarize or compare
results while preserving citations and source context.

## 12. How To Start The UI

On Windows, double-click:

```text
Start-DisclosureArchive-Search.cmd
```

That launcher starts the local server and opens the browser page.

Keep the launcher window open while searching. Close it to stop the server.

## 13. The Short Version

The project turns a pile of PDFs and media into a searchable local archive:

1. Read release metadata.
2. Extract native PDF text.
3. OCR scanned PDFs.
4. Split text into chunks.
5. Build keyword and vector indexes.
6. Search both with hybrid search.
7. Show ranked evidence with references.
8. Let the user open the original source.
9. Export evidence packs for LLM-assisted research.

The goal is not to prove claims automatically. The goal is to make the archive
searchable, citeable, and easier to investigate without losing provenance.
