#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Export a DisclosureArchive data package for another machine.

Default paths:
  SOURCE_ROOT=<repo>/../ufo_war_release
  EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage
  DB=<repo>/indexes/uap_release.sqlite
  SUMMARY=<repo>/indexes/uap_release.summary.json
  DERIVED=<repo>/derived

Usage:
  ./scripts/export_transfer_package.sh [--no-checksums]

Examples:
  EXPORT=/Volumes/DisclosureTransfer/DisclosureArchivePackage \
    ./scripts/export_transfer_package.sh

  EXPORT=/path/to/DisclosureArchivePackage \
    CREATE_CHECKSUMS=0 ./scripts/export_transfer_package.sh

Environment:
  SOURCE_ROOT       Raw archive directory to copy.
  EXPORT            Package directory to create/update.
  DB                Source SQLite DB. Copied via sqlite3 .backup.
  SUMMARY           Source summary JSON.
  DERIVED           Derived extraction/OCR cache directory.
  CREATE_CHECKSUMS  1 to write CHECKSUMS.sha256, 0 to skip.
EOF
}

CREATE_CHECKSUMS="${CREATE_CHECKSUMS:-1}"

while [ "$#" -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --no-checksums)
      CREATE_CHECKSUMS=0
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_ROOT="${SOURCE_ROOT:-$REPO_ROOT/../ufo_war_release}"
EXPORT="${EXPORT:-/Volumes/DisclosureTransfer/DisclosureArchivePackage}"
DB="${DB:-$REPO_ROOT/indexes/uap_release.sqlite}"
SUMMARY="${SUMMARY:-$REPO_ROOT/indexes/uap_release.summary.json}"
DERIVED="${DERIVED:-$REPO_ROOT/derived}"

require_path() {
  local label="$1"
  local path="$2"

  if [ ! -e "$path" ]; then
    echo "Missing $label: $path" >&2
    exit 1
  fi
}

require_command() {
  local cmd="$1"

  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

mounted_volume_for_export() {
  case "$EXPORT" in
    /Volumes/*)
      local rest="${EXPORT#/Volumes/}"
      printf '/Volumes/%s\n' "${rest%%/*}"
      ;;
  esac
}

require_command rsync
require_command sqlite3
require_command shasum

require_path "raw archive" "$SOURCE_ROOT"
require_path "SQLite DB" "$DB"
require_path "derived cache directory" "$DERIVED"

case "$EXPORT" in
  "$REPO_ROOT"|"$REPO_ROOT"/*)
    echo "Refusing to place transfer package inside the Git repo: $EXPORT" >&2
    exit 1
    ;;
  "$SOURCE_ROOT"|"$SOURCE_ROOT"/*)
    echo "Refusing to place transfer package inside the raw archive: $EXPORT" >&2
    exit 1
    ;;
esac

VOLUME="$(mounted_volume_for_export || true)"
if [ -n "${VOLUME:-}" ]; then
  if [ ! -d "$VOLUME" ] || ! mount | grep -F " on $VOLUME " >/dev/null 2>&1; then
    cat >&2 <<EOF
External volume does not appear to be mounted: $VOLUME

Mount the drive first, or set EXPORT to a local path explicitly:
  EXPORT=/path/to/DisclosureArchivePackage ./scripts/export_transfer_package.sh
EOF
    exit 1
  fi
fi

case "$EXPORT" in
  *"'"*)
    echo "EXPORT path cannot contain a single quote because sqlite3 .backup needs quoting: $EXPORT" >&2
    exit 1
    ;;
esac

RAW_DEST="$EXPORT/ufo_war_release"
INDEX_DEST="$EXPORT/indexes"
DERIVED_DEST="$EXPORT/derived"
EXPORT_DB="$INDEX_DEST/uap_release.sqlite"
MANIFEST="$EXPORT/MANIFEST.txt"
CHECKSUMS="$EXPORT/CHECKSUMS.sha256"

mkdir -p "$RAW_DEST" "$INDEX_DEST" "$DERIVED_DEST"

echo "Exporting raw archive..."
rsync -a --delete --progress \
  --exclude '.git/' \
  --exclude '.venv/' \
  --exclude '.DS_Store' \
  "$SOURCE_ROOT/" \
  "$RAW_DEST/"

echo "Exporting derived text/OCR cache..."
rsync -a --delete --progress \
  --exclude '.DS_Store' \
  "$DERIVED/" \
  "$DERIVED_DEST/"

echo "Creating clean SQLite backup..."
sqlite3 "$DB" ".backup '$EXPORT_DB'"

if [ -f "$SUMMARY" ]; then
  cp "$SUMMARY" "$INDEX_DEST/uap_release.summary.json"
else
  echo "Warning: summary JSON not found, skipping: $SUMMARY" >&2
fi

if find "$RAW_DEST" \( -name '.git' -o -name '.venv' \) -print -quit | grep -q .; then
  echo "Export contains a .git or .venv directory under raw archive; refusing to finish." >&2
  exit 1
fi

DB_INTEGRITY="$(sqlite3 "$EXPORT_DB" 'PRAGMA integrity_check;')"
DOCUMENTS="$(sqlite3 "$EXPORT_DB" 'select count(*) from documents;')"
ASSETS="$(sqlite3 "$EXPORT_DB" 'select count(*) from assets;')"
CHUNKS="$(sqlite3 "$EXPORT_DB" 'select count(*) from chunks;')"
EMBEDDINGS="$(sqlite3 "$EXPORT_DB" 'select count(*) from embeddings;')"
RAW_FILES="$(find "$RAW_DEST" -type f | wc -l | tr -d ' ')"
DERIVED_FILES="$(find "$DERIVED_DEST" -type f | wc -l | tr -d ' ')"
PACKAGE_SIZE="$(du -sh "$EXPORT" | awk '{print $1}')"

{
  echo "DisclosureArchive transfer package"
  echo "created_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "source_root=$SOURCE_ROOT"
  echo "repo_root=$REPO_ROOT"
  echo "export=$EXPORT"
  echo "raw_files=$RAW_FILES"
  echo "derived_files=$DERIVED_FILES"
  echo "package_size=$PACKAGE_SIZE"
  echo "db_integrity=$DB_INTEGRITY"
  echo "documents=$DOCUMENTS"
  echo "assets=$ASSETS"
  echo "chunks=$CHUNKS"
  echo "embeddings=$EMBEDDINGS"
} > "$MANIFEST"

if [ "$CREATE_CHECKSUMS" = "1" ]; then
  echo "Writing checksum manifest..."
  (
    cd "$EXPORT"
    : > "$CHECKSUMS"
    find ufo_war_release indexes derived -type f -print | LC_ALL=C sort | while IFS= read -r file; do
      shasum -a 256 "$file"
    done > "$CHECKSUMS"
  )
else
  echo "Skipping checksum manifest because CREATE_CHECKSUMS=0."
fi

cat <<EOF

Export complete:
  $EXPORT

Verification:
  SQLite integrity: $DB_INTEGRITY
  Documents: $DOCUMENTS
  Assets: $ASSETS
  Chunks: $CHUNKS
  Embeddings: $EMBEDDINGS
  Raw files: $RAW_FILES
  Derived files: $DERIVED_FILES
  Package size: $PACKAGE_SIZE

Next:
  scripts/verify_transfer_package.sh "$EXPORT"
EOF
