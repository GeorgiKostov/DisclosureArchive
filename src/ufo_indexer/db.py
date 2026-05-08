from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS documents (
  doc_id TEXT PRIMARY KEY,
  row_number INTEGER,
  title TEXT,
  release_type TEXT,
  agency TEXT,
  release_date TEXT,
  incident_date TEXT,
  incident_location TEXT,
  description TEXT,
  source_url TEXT,
  dvids_video_id TEXT,
  content_hash TEXT,
  indexed_at TEXT
);

CREATE TABLE IF NOT EXISTS assets (
  asset_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  local_path TEXT,
  source_url TEXT,
  content_hash TEXT,
  bytes INTEGER,
  metadata_json TEXT,
  FOREIGN KEY(doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chunks (
  rowid INTEGER PRIMARY KEY,
  chunk_id TEXT UNIQUE NOT NULL,
  doc_id TEXT NOT NULL,
  source_kind TEXT NOT NULL,
  page_number INTEGER,
  chunk_index INTEGER NOT NULL,
  title TEXT,
  agency TEXT,
  incident_date TEXT,
  incident_location TEXT,
  text TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  metadata_json TEXT,
  FOREIGN KEY(doc_id) REFERENCES documents(doc_id) ON DELETE CASCADE
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  chunk_id UNINDEXED,
  doc_id UNINDEXED,
  title,
  agency,
  incident_location,
  text
);

CREATE TABLE IF NOT EXISTS embeddings (
  chunk_id TEXT NOT NULL,
  model TEXT NOT NULL,
  dim INTEGER NOT NULL,
  vector BLOB NOT NULL,
  PRIMARY KEY(chunk_id, model),
  FOREIGN KEY(chunk_id) REFERENCES chunks(chunk_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_chunks_hash ON chunks(text_hash);
CREATE INDEX IF NOT EXISTS idx_documents_title ON documents(title);
CREATE INDEX IF NOT EXISTS idx_documents_agency ON documents(agency);
"""


def connect(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    conn.commit()


def reset_db(path: Path) -> None:
    for suffix in ["", "-wal", "-shm"]:
        candidate = Path(str(path) + suffix)
        if candidate.exists():
            candidate.unlink()
