"""
Commit 1 - the shape of memory.

Two functions, the whole idea:

    remember(text)  -> store a fact
    recall(query)   -> find facts that answer the query

Everything else is a placeholder we replace as we go.

    commit 1  fake list, keyword search      <- you are here
    commit 2  save to disk so it survives a restart
    commit 3  let the LLM pull facts out of a conversation
    commit 4  embed memories, search by meaning
    commit 5  plug both into a chat loop

Two things are deliberately dumb in this file. Do not fix them yet -
they are the thing commit 4 exists to fix.

    1. Storage is a hardcoded list. Gone on restart.
    2. recall() matches words, not meaning.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Memory:
    """One fact about the user.

    Atomic means self-contained: 'User is VP of Product' is fine,
    '...and then she mentioned the title thing...' is not. Day 1 only
    needs id/text/created, but adding them now means commits 2-4 are
    additions instead of a rewrite.
    """

    id: int
    text: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# --------------------------------------------------------------------------
# storage - FAKE. commit 2 makes this real.
# --------------------------------------------------------------------------

_SEED = [
    "User's name is Sarah",
    "User works at Acme as VP of Product",
    "User prefers TypeScript",
    "User is learning Portuguese",
]

_MEMORIES: list[Memory] = []


def remember(text: str) -> Memory:
    """Store one fact. Returns the stored memory."""
    clean = text.strip()
    if not clean:
        raise ValueError("cannot remember nothing")

    m = Memory(id=len(_MEMORIES) + 1, text=clean)
    _MEMORIES.append(m)
    return m


def recall(query: str, limit: int = 3) -> list[Memory]:
    """Return the memories most likely to answer `query`.

    NAIVE: scores by counting shared words. So 'what do they do' finds
    nothing, even though 'works at Acme' is sitting right there. That gap
    is the whole reason commit 4 exists.
    """
    wanted = set(query.lower().split())

    scored: list[tuple[int, Memory]] = []
    for m in _MEMORIES:
        overlap = wanted & set(m.text.lower().split())
        if overlap:
            scored.append((len(overlap), m))

    # sort by score only - ties keep insertion order, so ids stay stable
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored[:limit]]


def list_all() -> list[Memory]:
    """Every memory we hold. For looking at."""
    return list(_MEMORIES)


# --------------------------------------------------------------------------
# demo
# --------------------------------------------------------------------------


def main() -> None:
    for m in _SEED:
        remember(m)
    remember("User dislikes the gym near their office")

    print(f"stored {len(list_all())} memories\n")

    print("--- recall('what is her name') ---")
    for m in recall("what is her name"):
        print(f"  [{m.id}] {m.text}")
    print("  ^ ranked #2 is noise: 'is' is a common word, so 'User is")
    print("    learning Portuguese' scored 1 hit. No stopwords, no ranking.")

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
        print("  ^ WRONG ANSWER. 'works at Acme' is in the store,")
        print("    but the query shares no words with it.")

    print("\n--- recall('portuguese') ---")
    for m in recall("portuguese"):
        print(f"  [{m.id}] {m.text}")


if __name__ == "__main__":
    main()