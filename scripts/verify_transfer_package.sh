#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Verify a DisclosureArchive transfer package.

Usage:
  ./scripts/verify_transfer_package.sh [--checksums] /path/to/DisclosureArchivePackage

Checks:
  - expected directories/files exist
  - clean SQLite DB passes PRAGMA integrity_check
  - raw/derived file counts are visible
  - optional CHECKSUMS.sha256 verification
EOF
}

VERIFY_CHECKSUMS=0
PACKAGE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --checksums)
      VERIFY_CHECKSUMS=1
      shift
      ;;
    *)
      if [ -n "$PACKAGE" ]; then
        echo "Unexpected extra argument: $1" >&2
        usage >&2
        exit 2
      fi
      PACKAGE="$1"
      shift
      ;;
  esac
done

PACKAGE="${PACKAGE:-${EXPORT:-/Volumes/DisclosureTransfer/DisclosureArchivePackage}}"
DB="$PACKAGE/indexes/uap_release.sqlite"
SUMMARY="$PACKAGE/indexes/uap_release.summary.json"
CHECKSUMS="$PACKAGE/CHECKSUMS.sha256"

if ! command -v sqlite3 >/dev/null 2>&1; then
  echo "Missing required command: sqlite3" >&2
  exit 1
fi

for path in "$PACKAGE/ufo_war_release" "$PACKAGE/indexes" "$PACKAGE/derived" "$DB"; do
  if [ ! -e "$path" ]; then
    echo "Missing expected package path: $path" >&2
    exit 1
  fi
done

RAW_FILES="$(find "$PACKAGE/ufo_war_release" -type f | wc -l | tr -d ' ')"
DERIVED_FILES="$(find "$PACKAGE/derived" -type f | wc -l | tr -d ' ')"
DB_INTEGRITY="$(sqlite3 "$DB" 'PRAGMA integrity_check;')"
DOCUMENTS="$(sqlite3 "$DB" 'select count(*) from documents;')"
ASSETS="$(sqlite3 "$DB" 'select count(*) from assets;')"
CHUNKS="$(sqlite3 "$DB" 'select count(*) from chunks;')"
EMBEDDINGS="$(sqlite3 "$DB" 'select count(*) from embeddings;')"

if [ "$DB_INTEGRITY" != "ok" ]; then
  echo "SQLite integrity check failed: $DB_INTEGRITY" >&2
  exit 1
fi

if [ "$VERIFY_CHECKSUMS" = "1" ]; then
  if [ ! -f "$CHECKSUMS" ]; then
    echo "Checksum file not found: $CHECKSUMS" >&2
    exit 1
  fi

  (
    cd "$PACKAGE"
    shasum -a 256 -c "$CHECKSUMS"
  )
fi

cat <<EOF
Transfer package OK:
  Package: $PACKAGE
  Summary JSON: $(if [ -f "$SUMMARY" ]; then echo present; else echo missing; fi)
  SQLite integrity: $DB_INTEGRITY
  Documents: $DOCUMENTS
  Assets: $ASSETS
  Chunks: $CHUNKS
  Embeddings: $EMBEDDINGS
  Raw files: $RAW_FILES
  Derived files: $DERIVED_FILES
EOF
