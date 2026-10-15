from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone


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

_MEMORIES: list[Memory] = []


def remember(text: str) -> Memory:
    clean = text.strip()
    if not clean:
        raise ValueError("cannot remember nothing")

    m = Memory(id=len(_MEMORIES) + 1, text=clean)
    _MEMORIES.append(m)
    return m


def recall(query: str, limit: int = 3) -> list[Memory]:
    query_words = set(query.lower().split())

    scored: list[tuple[int, Memory]] = []
    for m in _MEMORIES:
        memory_words = set(m.text.lower().split())
        overlap = query_words & memory_words
        if overlap:
            scored.append((len(overlap), m))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored[:limit]]


def list_all() -> list[Memory]:
    return list(_MEMORIES)


def main() -> None:
    for m in _SEED:
        remember(m)
    remember("User dislikes the gym near their office")

    print(f"stored {len(list_all())} memories\n")

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