import sys
from .llm import answer, extract_facts
from .search import semantic
from .store import Store


def _write_safely() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run(store: Store) -> None:
    _write_safely()

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