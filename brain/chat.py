from __future__ import annotations

from .llm import answer, extract_facts
from .search import semantic
from .store import Store


def run(store: Store) -> None:
    while True:
        try:
            line = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if line in ("exit", "quit"):
            break
        if not line:
            continue

        hits = semantic(store.all(), line)
        reply = answer(line, hits)
        print(f"     [{len(hits)} memories recalled]\nai:  {reply}\n")

        transcript = f"user: {line}\nassistant: {reply}"
        for fact in extract_facts(transcript):
            store.remember(fact)