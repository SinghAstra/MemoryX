from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from config import GROQ_API_KEY
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Memory:
    id: int
    text: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


API_KEY = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
API_BASE = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

EXTRACT_SYSTEM = (
    "You extract durable facts about a user from conversations.\n"
    "Rules:\n"
    "- Each fact must stand alone with no context needed.\n"
    "- Start every fact with 'User'.\n"
    "- Skip anything temporary, uncertain, or about the assistant.\n"
    "- One fact per line, nothing else."
)

_SAMPLE_CHAT = """user: hi, i'm sarah. i work at acme as vp of product
assistant: nice to meet you sarah
user: i've been going to the ts meetup on thursdays lately
user: also i just moved to san francisco, been here about a month
assistant: congrats on the move
user: any good ramen places near soma?"""

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


HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "memory-demo/1.0",
}


def list_models() -> list[str]:
    request = urllib.request.Request(
        f"{API_BASE}/models",
        headers={**HEADERS, "Authorization": f"Bearer {API_KEY}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return [m["id"] for m in json.loads(response.read())["data"]]
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"could not list models: {e.code} {e.read().decode()[:300]}")


def _complete(system: str, user: str) -> str:
    payload = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
    ).encode()
    request = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=payload,
        headers={**HEADERS, "Authorization": f"Bearer {API_KEY}"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Groq {e.code}: {e.read().decode()[:400]}\n"
            f"model = {MODEL!r} - run 'python memory.py models' to see what is live"
        )
    return body["choices"][0]["message"]["content"]


def extract_facts(transcript: str) -> list[str]:
    raw = _complete(EXTRACT_SYSTEM, transcript)
    return [line.strip("-* ").strip() for line in raw.splitlines() if line.strip()]


def remember(text: str) -> Memory:
    clean = text.strip()
    if not clean:
        raise ValueError("cannot remember nothing")

    for m in _MEMORIES:
        if m.text.lower() == clean.lower():
            return m

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
    if not _MEMORIES:
        for m in _SEED:
            remember(m)
        remember("User dislikes the gym near their office")

    print(f"store: {STORE_PATH}\n")

    if API_KEY:
        facts = extract_facts(_SAMPLE_CHAT)
        print(f"--- extracted {len(facts)} facts ---")
        for fact in facts:
            print(f"  {fact}")
        for fact in facts:
            remember(fact)
        print()
    else:
        print("no GROQ_API_KEY set (config.py or env) - skipping extraction\n")

    print(f"stored {len(list_all())} memories\n")

    print("--- recall('what is her name') ---")
    for m in recall("what is her name"):
        print(f"  [{m.id}] {m.text}")

    print("\n--- recall('where do they live') ---")
    for m in recall("where do they live"):
        print(f"  [{m.id}] {m.text}")

    print("\n--- recall('what do they do for work') ---")
    hits = recall("what do they do for work")
    if hits:
        for m in hits:
            print(f"  [{m.id}] {m.text}")
    else:
        print("  (nothing)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "models":
        if not API_KEY:
            raise SystemExit("set GROQ_API_KEY in config.py first")
        for name in list_models():
            print(name)
    else:
        main()