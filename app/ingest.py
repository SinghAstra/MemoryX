import hashlib
import re
import uuid
from datetime import datetime, timezone

from app import db, settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _split_long(text: str, max_chars: int, overlap: int) -> list[str]:
    pieces: list[str] = []
    current = ""
    for word in text.split():
        if current and len(current) + len(word) + 1 > max_chars:
            pieces.append(current)
            current = f"{current[-overlap:]} {word}".strip() if overlap else word
        else:
            current = f"{current} {word}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_text(
    text: str,
    max_chars: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    max_chars = max_chars or settings.CHUNK_CHARS
    overlap = settings.CHUNK_OVERLAP if overlap is None else overlap
    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    current = ""
    parts = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]

    for part in parts:
        if len(part) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long(part, max_chars, overlap))
        elif not current:
            current = part
        elif len(current) + 2 + len(part) <= max_chars:
            current = f"{current}\n\n{part}"
        else:
            chunks.append(current)
            current = f"{current[-overlap:]}\n\n{part}".strip() if overlap else part

    if current:
        chunks.append(current)
    return chunks


def _chunk_count(doc_id: str) -> int:
    row = db.get().execute(
        "SELECT COUNT(*) FROM chunks WHERE document_id = ?", (doc_id,)
    ).fetchone()
    return int(row[0])


def add_document(
    container_tag: str,
    content: str,
    custom_id: str | None = None,
) -> dict:
    container_tag = container_tag.strip()
    content = content.strip()
    if not container_tag or not content:
        raise ValueError("container_tag and content are required")

    conn = db.get()
    digest = _digest(content)
    existing = None
    if custom_id:
        existing = conn.execute(
            "SELECT * FROM documents WHERE container_tag = ? AND custom_id = ?",
            (container_tag, custom_id),
        ).fetchone()

    if existing and existing["content_hash"] == digest:
        return {
            "id": existing["id"],
            "status": existing["status"],
            "chunks": _chunk_count(existing["id"]),
            "created": False,
        }

    now = _now()
    if existing:
        doc_id = existing["id"]
        with conn:
            conn.execute("DELETE FROM chunks_fts WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
            conn.execute(
                "UPDATE documents SET content = ?, content_hash = ?, status = ?, updated_at = ? WHERE id = ?",
                (content, digest, "queued", now, doc_id),
            )
    else:
        doc_id = uuid.uuid4().hex
        with conn:
            conn.execute(
                "INSERT INTO documents (id, container_tag, custom_id, content, content_hash, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (doc_id, container_tag, custom_id, content, digest, "queued", now, now),
            )

    chunks = chunk_text(content)
    with conn:
        for position, chunk in enumerate(chunks):
            chunk_id = uuid.uuid4().hex
            conn.execute(
                "INSERT INTO chunks (id, document_id, container_tag, position, content, token_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (chunk_id, doc_id, container_tag, position, chunk, _tokens(chunk), now),
            )
            conn.execute(
                "INSERT INTO chunks_fts (content, chunk_id, document_id, container_tag) VALUES (?, ?, ?, ?)",
                (chunk, chunk_id, doc_id, container_tag),
            )
        conn.execute(
            "UPDATE documents SET status = ?, updated_at = ? WHERE id = ?",
            ("done", now, doc_id),
        )

    return {"id": doc_id, "status": "done", "chunks": len(chunks), "created": existing is None}
