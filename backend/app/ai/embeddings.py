import hashlib
import math


def embed_text(text: str) -> list[float]:
    """
    Lightweight deterministic embedding.

    Temporary deployment version.
    Replace with SentenceTransformer in production.
    """
    digest = hashlib.sha256(text.encode()).digest()

    return [x / 255.0 for x in digest]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))

    if na == 0 or nb == 0:
        return 0.0

    return dot / (na * nb)