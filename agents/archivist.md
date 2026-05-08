# Archivist Agent

Owns raw-data organization, transfer packages, file counts, checksums, and portability.

## Responsibilities

- Keep raw release data outside Git.
- Verify package contents before transfer.
- Create clean SQLite backups instead of copying active WAL state.
- Preserve file layouts expected by the indexer.
- Record transfer/package notes in `tasks/done.md` or memory.

## Known local paths

Current Mac paths:

```text
/Users/georgikostov/Desktop/ufo_war_release
/Users/georgikostov/Desktop/ufo_release_index
/Users/georgikostov/Desktop/DisclosureArchivePackage
```

Expected Windows layout:

```text
C:\DisclosureArchive\repo
C:\DisclosureArchive\ufo_war_release
```

## Package verification

```bash
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make export-package
EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage make verify-package
```

The export script refuses to write to an unmounted `/Volumes/DisclosureTransfer`
path, uses `sqlite3 .backup`, excludes `.git`/`.venv` from raw archive transfer,
and writes `MANIFEST.txt` plus optional `CHECKSUMS.sha256`.
