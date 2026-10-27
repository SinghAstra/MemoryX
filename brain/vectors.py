from fastembed import TextEmbedding
from .settings import EMBED_MODEL
_embedder: TextEmbedding | None = None


def embed(texts: list[str]) -> list[list[float]]:
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedding(EMBED_MODEL)
    raw_vectors = _embedder.embed(texts)
    result: list[list[float]] = []
    for v in raw_vectors:
        clean: list[float] = []
        for x in v:
            clean.append(float(x))
        result.append(clean)
    return result


def dot(a: list[float], b: list[float]) -> float:
    total = 0.0
    for x, y in zip(a, b):
        total += x * y
    return total