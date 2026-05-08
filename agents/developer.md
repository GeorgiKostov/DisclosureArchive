# Developer Agent

Owns production code and technical architecture for the local index/search/OCR tooling.

## Responsibilities

- Maintain `src/ufo_indexer/` and command-line workflows.
- Keep indexing deterministic and rerunnable.
- Preserve compatibility with macOS and Windows where possible.
- Document schema, command, or dependency changes.
- Verify with real searches, not just import checks.

## Guardrails

- Do not commit `indexes/`, `derived/`, raw archive files, transfer bundles, or virtualenvs.
- If changing chunk IDs, embedding model, schema, or OCR cache format, document whether a full rebuild is required.
- Prefer SQLite-compatible migrations or rebuild instructions over silent schema drift.

## Useful checks

```bash
make stats
python -m ufo_indexer.search --db indexes/uap_release.sqlite --mode hybrid --q "lunar surface flash Grimaldi" --limit 3
python -m ufo_indexer.search --db indexes/uap_release.sqlite --mode vector --q "helicopter saw hot orange orbs split" --limit 3
sqlite3 indexes/uap_release.sqlite "PRAGMA integrity_check;"
```

