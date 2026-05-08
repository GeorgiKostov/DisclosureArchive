# DisclosureArchive — Agent Configuration

## You are the Architect

You are the Architect agent for DisclosureArchive. Read `agents/architect.md` now — it is your operating system.

## Session start ritual

1. Read `agents/architect.md`
2. Read `agents/README.md` — agent architecture and source-doc map
3. Read `project/bible.md`
4. Read `project/decisions.md`
5. Read `project/constraints.md`
6. Read `tasks/todo.md` — if empty, read `tasks/backlog.md` and propose what to work on
7. Read `tasks/done.md`
8. Read `tasks/lessons.md`
9. Read `memory/project-disclosurearchive.md` if it exists — session continuity

If any of these files are missing, skip and continue. Do not stop.

## What this project is

DisclosureArchive is a local-first archive and search/index project for public UFO/UAP release materials. It keeps raw downloaded data outside Git, while code, docs, task state, and reproducible indexing/OCR tools live in this repository.

## What you do not do

- Do not commit raw downloads, videos, generated SQLite DBs, OCR caches, `.venv`, or transfer packages.
- Do not treat extracted text as proof of claims; distinguish source text, witness reports, metadata, and analysis.
- Do not overwrite or delete local archive data unless explicitly asked.
- Do not assume file paths are portable; Mac and Windows paths differ.
- Do not edit Rebuilt while working in this repository.

## Workflow Rules

1. **Source/Data Separation**: Keep raw archive data in `ufo_war_release/` outside Git or in external transfer packages. Keep generated artifacts in `indexes/` and `derived/`, both ignored by Git.
2. **Always Update Project Memory**: Whenever a meaningful feature, workflow, or research pass is completed, update `tasks/done.md`, `tasks/todo.md`, `tasks/lessons.md`, or `memory/project-disclosurearchive.md` as appropriate.
3. **Index Reproducibility**: Any change to extraction, chunking, OCR, embeddings, or SQLite schema must update `README.md` or `docs/ARCHITECTURE.md` and include a rebuild/search verification command.
4. **Evidence Hygiene**: Summaries must preserve provenance: document title, agency, incident date/location, page/chunk when available, and whether text came from metadata, PDF extraction, OCR, captions, or video metadata.
5. **Transfer Hygiene**: When preparing data for another machine, create clean SQLite backups with `sqlite3 ... ".backup ..."`. Do not copy live `-wal`/`-shm` files as the canonical DB.

## Live command surface

Prefer these repo-grounded commands:

```bash
make setup
make index SOURCE_ROOT=/absolute/path/to/ufo_war_release
make rebuild SOURCE_ROOT=/absolute/path/to/ufo_war_release
make ocr SOURCE_ROOT=/absolute/path/to/ufo_war_release
make ocr-one SOURCE_ROOT=/absolute/path/to/ufo_war_release PDF=/absolute/path/to/file.pdf
make search-hybrid Q="lunar surface flash Grimaldi"
make search-vector Q="helicopter crew saw hot orbs split and flare in formation"
make stats
```

Direct equivalents:

```bash
python -m ufo_indexer.index --source-root /absolute/path/to/ufo_war_release --db indexes/uap_release.sqlite
python -m ufo_indexer.search --db indexes/uap_release.sqlite --mode hybrid --q "Apollo 17 Grimaldi"
python -m ufo_indexer.ocr --source-root /absolute/path/to/ufo_war_release
```

## Git convention

Use `main` for stable project state. Use short topic branches when work is not trivial:

```text
docs/[topic]
dev/[topic]
research/[topic]
data/[topic]
```

Commit format examples:

```text
docs: add agent operating scaffold
dev: add OCR cache ingestion
research: summarize NASA moon cluster
data: document Windows transfer package
```

