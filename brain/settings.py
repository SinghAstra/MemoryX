from __future__ import annotations

import os
from pathlib import Path

try:
    from config import GROQ_API_KEY
except ImportError:
    GROQ_API_KEY = ""

API_KEY = GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
API_BASE = "https://api.groq.com/openai/v1"
MODEL = "openai/gpt-oss-120b"

EMBED_MODEL = "BAAI/bge-small-en-v1.5"
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
MIN_FACT_CHARS = 12

STORE_PATH = Path(__file__).parent.parent / "memories.json"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "memory-demo/1.0",
}

ANSWER_SYSTEM = (
    "You are a helpful assistant with long-term memory of the user.\n"
    "Use the memories when they are relevant. Never mention them unless asked.\n"
    "If a memory contradicts the user right now, believe the user."
)

EXTRACT_SYSTEM = (
    "You extract durable facts about a user from conversations.\n"
    "Rules:\n"
    "- Each fact must stand alone with no context needed.\n"
    "- Start every fact with 'User'.\n"
    "- Skip anything temporary, uncertain, or about the assistant.\n"
    "- One fact per line, nothing else."
)

SEED = [
    "User's name is Sarah",
    "User works at Acme as VP of Product",
    "User prefers TypeScript",
    "User is learning Portuguese",
    "User dislikes the gym near their office",
]

SAMPLE_CHAT = """user: hi, i'm sarah. i work at acme as vp of product
assistant: nice to meet you sarah
user: i've been going to the ts meetup on thursdays lately
user: also i just moved to san francisco, been here about a month
assistant: congrats on the move
user: any good ramen places near soma?"""