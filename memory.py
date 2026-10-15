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

from fastembed import TextEmbedding


@dataclass
class Memory:
    id: int
    text: str
    vector: list[float] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "vector": self.vector,
            "created_at": self.created_at.isoformat(),
        }


API_KEY = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
API_BASE = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "memory-demo/1.0",
}

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

_EMBEDDER = None


def embed(texts: list[str]) -> list[list[float]]:
    global _EMBEDDER
    if _EMBEDDER is None:
        _EMBEDDER = TextEmbedding(EMBED_MODEL)
    return [[float(x) for x in v] for v in _EMBEDDER.embed(texts)]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _load() -> list[Memory]:
    if not STORE_PATH.exists():
        return []

    out: list[Memory] = []
    for row in json.loads(STORE_PATH.read_text()):
        out.append(
            Memory(
                id=row["id"],
                text=row["text"],
                vector=row.get("vector", []),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
        )
    return out


_MEMORIES: list[Memory] = _load()


def _save() -> None:
    STORE_PATH.write_text(json.dumps([m.to_dict() for m in _MEMORIES], indent=2))


def _ensure_vectors() -> None:
    missing = [m for m in _MEMORIES if not m.vector]
    if not missing:
        return
    for m, vector in zip(missing, embed([m.text for m in missing])):
        m.vector = vector
    _save()


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

    m = Memory(id=len(_MEMORIES) + 1, text=clean, vector=embed([clean])[0])
    _MEMORIES.append(m)
    _save()
    return m


def reset() -> None:
    _MEMORIES.clear()
    _save()


def recall(query: str, limit: int = 3) -> list[Memory]:
    query_vector = embed([QUERY_PREFIX + query])[0]

    scored: list[tuple[float, Memory]] = []
    for memory in _MEMORIES:
        if not memory.vector:
            continue
        scored.append((_dot(query_vector, memory.vector), memory))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored[:limit]]


def recall_keywords(query: str, limit: int = 3) -> list[Memory]:
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


def _compare(query: str, limit: int = 3) -> None:
    print(f"--- {query!r} ---")
    for label, fn in (("semantic", recall), ("keywords", recall_keywords)):
        hits = fn(query, limit)
        if not hits:
            print(f"  {label:<9} (nothing)")
        for m in hits:
            print(f"  {label:<9} [{m.id}] {m.text}")


def main() -> None:
    if not _MEMORIES:
        for m in _SEED:
            remember(m)
        remember("User dislikes the gym near their office")

    _ensure_vectors()

    print(f"store: {STORE_PATH}\n")

    if API_KEY:
        facts = extract_facts(_SAMPLE_CHAT)
        print(f"--- extracted {len(facts)} facts ---")
        for fact in facts:
            print(f"  {fact}")
        for fact in facts:
            remember(fact)
        _ensure_vectors()
        print()
    else:
        print("no GROQ_API_KEY set (config.py or env) - skipping extraction\n")

    print(f"stored {len(list_all())} memories\n")

    for q in (
        "what is her name",
        "where do they live",
        "what does she do at work",
        "what programming language",
    ):
        _compare(q)
        print()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "models":
        if not API_KEY:
            raise SystemExit("set GROQ_API_KEY in config.py first")
        for name in list_models():
            print(name)
    else:
        main()