from __future__ import annotations

from fastembed import TextEmbedding

from .settings import EMBED_MODEL

_embedder = None


def embed(texts: list[str]) -> list[list[float]]:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(EMBED_MODEL)
    return [[float(x) for x in v] for v in _embedder.embed(texts)]


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))