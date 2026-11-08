import sqlite3
from pathlib import Path

from app import settings
from app.models import Document

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id            TEXT PRIMARY KEY,
    container_tag TEXT NOT NULL,
    custom_id     TEXT,
    content       TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'queued',
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL,
    UNIQUE (container_tag, custom_id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id            TEXT PRIMARY KEY,
    document_id   TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    container_tag TEXT NOT NULL,
    position      INTEGER NOT NULL,
    content       TEXT NOT NULL,
    token_count   INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    chunk_id UNINDEXED,
    document_id UNINDEXED,
    container_tag UNINDEXED,
    tokenize = 'porter unicode61'
);

CREATE INDEX IF NOT EXISTS idx_documents_container ON documents(container_tag);
CREATE INDEX IF NOT EXISTS idx_chunks_container ON chunks(container_tag);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
"""

_conn: sqlite3.Connection | None = None


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    global _conn
    if _conn is not None:
        _conn.close()
    _conn = sqlite3.connect(str(path or settings.DB_PATH))
    _conn.row_factory = sqlite3.Row
    _conn.execute("PRAGMA foreign_keys = ON")
    _conn.execute("PRAGMA journal_mode = WAL")
    _conn.executescript(SCHEMA)
    return _conn


def get() -> sqlite3.Connection:
    if _conn is None:
        return connect()
    return _conn


def close() -> None:
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def _document(row: sqlite3.Row) -> Document:
    return Document(
        id=row["id"],
        container_tag=row["container_tag"],
        content=row["content"],
        content_hash=row["content_hash"],
        custom_id=row["custom_id"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_document(doc_id: str) -> Document | None:
    row = get().execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    return _document(row) if row else None


def list_documents(container_tag: str) -> list[Document]:
    rows = get().execute(
        "SELECT * FROM documents WHERE container_tag = ? ORDER BY created_at",
        (container_tag,),
    ).fetchall()
    return [_document(row) for row in rows]


def reset_container(container_tag: str) -> None:
    conn = get()
    with conn:
        conn.execute("DELETE FROM chunks_fts WHERE container_tag = ?", (container_tag,))
        conn.execute("DELETE FROM documents WHERE container_tag = ?", (container_tag,))
