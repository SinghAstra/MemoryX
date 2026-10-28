from .models import Memory
from .settings import QUERY_PREFIX
from .vectors import dot, embed


def semantic(memories: list[Memory], query: str, limit: int = 3) -> list[Memory]:
    query_vector = embed([QUERY_PREFIX + query])[0]
    scored: list[tuple[float, Memory]] = []
    for memory in memories:
        if memory.vector:
            scored.append((dot(query_vector, memory.vector), memory))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored[:limit]]


def keywords(memories: list[Memory], query: str, limit: int = 3) -> list[Memory]:
    query_words = set(query.lower().split())
    scored: list[tuple[int, Memory]] = []
    for memory in memories:
        memory_words = set(memory.text.lower().split())
        overlap = query_words & memory_words
        if overlap:
            scored.append((len(overlap), memory))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [m for _, m in scored[:limit]]