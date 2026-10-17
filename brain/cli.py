from __future__ import annotations
import sys
from .chat import _write_safely, run
from .llm import answer, extract_facts, list_models
from .models import Memory
from .search import keywords, semantic
from .settings import API_KEY, SAMPLE_CHAT, SEED, STORE_PATH
from .store import Store


def _compare(items: list[Memory], query: str, limit: int = 3) -> None:
    print(f"--- {query!r} ---")
    for label, fn in (("semantic", semantic), ("keywords", keywords)):
        hits = fn(items, query, limit)
        if not hits:
            print(f"  {label:<9} (nothing)")
        for m in hits:
            print(f"  {label:<9} [{m.id}] {m.text}")


def _seed(store: Store) -> None:
    for text in SEED:
        store.remember(text)


def demo(store: Store) -> None:
    if not store.all():
        _seed(store)
    store.ensure_vectors()

    print(f"store: {STORE_PATH}\n")

    if API_KEY:
        facts = extract_facts(SAMPLE_CHAT)
        print(f"--- extracted {len(facts)} facts ---")
        for fact in facts:
            print(f"  {fact}")
        for fact in facts:
            store.remember(fact)
        store.ensure_vectors()
        print()
    else:
        print("no GROQ_API_KEY set (config.py or env) - skipping extraction\n")

    print(f"stored {len(store.all())} memories\n")

    items = store.all()
    for q in (
        "what is her name",
        "where do they live",
        "what does she do at work",
        "what programming language",
    ):
        _compare(items, q)
        print()


def main(argv: list[str] | None = None) -> None:
    _write_safely()

    args = sys.argv[1:] if argv is None else argv
    store = Store(STORE_PATH)

    if args and args[0] == "models":
        if not API_KEY:
            raise SystemExit("set GROQ_API_KEY in config.py first")
        for name in list_models():
            print(name)
        return

    if args and args[0] == "chat":
        if not API_KEY:
            raise SystemExit("set GROQ_API_KEY in config.py first")
        if not store.all():
            _seed(store)
        store.ensure_vectors()
        run(store)
        return

    demo(store)