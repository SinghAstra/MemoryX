from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Memory:
    id: int
    text: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


_SEED = [
    "User's name is Sarah",
    "User works at Acme as VP of Product",
    "User prefers TypeScript",
    "User is learning Portuguese",
]

STORE_PATH = Path(__file__).parent / "memories.json"


def _load() -> list[Memory]:
    if not STORE_PATH.exists():
        return []

    out: list[Memory] = []
    for row in json.loads(STORE_PATH.read_text()):
        out.append(
            Memory(
                id=row["id"],
                text=row["text"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        )
    return out


_MEMORIES: list[Memory] = _load()


def _save() -> None:
    rows = [
        {
            "id": m.id,
            "text": m.text,
            "created_at": m.created_at.isoformat(),
        }
        for m in _MEMORIES
    ]
    STORE_PATH.write_text(json.dumps(rows, indent=2))


def remember(text: str) -> Memory:
    clean = text.strip()
    if not clean:
        raise ValueError("cannot remember nothing")

    m = Memory(id=len(_MEMORIES) + 1, text=clean)
    _MEMORIES.append(m)
    _save()
    return m


def reset() -> None:
    _MEMORIES.clear()
    _save()


def recall(query: str, limit: int = 3) -> list[Memory]:
    query_words = set(query.lower().split())

    scored: list[tuple[int, Memory]] = []
    for memory in _MEMORIES:
        memory_words = set(memory.text.lower().split())
        overlap = query_words & memory_words
        if overlap:
            scored.append((len(overlap), memory))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored[:limit]]


def list_all() -> list[Memory]:
    return list(_MEMORIES)


def main() -> None:
    print(f"store: {STORE_PATH}")

    if not _MEMORIES:
        for m in _SEED:
            remember(m)
        remember("User dislikes the gym near their office")
        print(f"seeded {len(_MEMORIES)} memories\n")
    else:
        print(f"loaded {len(_MEMORIES)} memories from disk\n")

    print("--- recall('what is her name') ---")
    for m in recall("what is her name"):
        print(f"  [{m.id}] {m.text}")

    print("\n--- recall('typescript') ---")
    for m in recall("typescript"):
        print(f"  [{m.id}] {m.text}")

    print("\n--- recall('what do they do for work') ---")
    hits = recall("what do they do for work")
    if hits:
        for m in hits:
            print(f"  [{m.id}] {m.text}")
    else:
        print("  (nothing)")

    print("\n--- recall('portuguese') ---")
    for m in recall("portuguese"):
        print(f"  [{m.id}] {m.text}")


if __name__ == "__main__":
    main()