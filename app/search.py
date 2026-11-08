import re

from app import db


def _match(query: str) -> str:
    words = re.findall(r"\w+", query.lower())
    return " OR ".join(f'"{word}"' for word in words)


def keyword_chunks(container_tag: str, query: str, limit: int = 5) -> list[dict]:
    match = _match(query)
    if not match:
        return []

    rows = db.get().execute(
        """
        SELECT c.id, c.document_id, c.content, bm25(chunks_fts) AS score
        FROM chunks_fts
        JOIN chunks c ON c.id = chunks_fts.chunk_id
        WHERE chunks_fts MATCH ? AND c.container_tag = ?
        ORDER BY score
        LIMIT ?
        """,
        (match, container_tag, limit),
    ).fetchall()
    return [dict(row) for row in rows]
