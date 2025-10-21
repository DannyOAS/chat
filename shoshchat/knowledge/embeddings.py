"""Embedding utilities with deterministic fallback for offline usage."""
from __future__ import annotations

import hashlib
import math
from typing import List, Sequence

from nlp.models import LLMConfig

EMBEDDING_DIMENSION = 256


def _normalized_hash_vector(text: str) -> List[float]:
    """Return a deterministic embedding vector derived from a hash digest."""

    digest = hashlib.sha256(text.encode("utf-8")).digest()
    required_bytes = EMBEDDING_DIMENSION
    repeats = required_bytes // len(digest) + 1
    data = (digest * repeats)[:required_bytes]
    vector = [((byte / 255.0) * 2.0 - 1.0) for byte in data]
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def embed_text(text: str, tenant, *, model_name: str | None = None) -> tuple[Sequence[float], str]:
    """Generate an embedding for the given text using tenant config or fallback."""

    config = None
    if model_name is None:
        config = LLMConfig.objects.filter(tenant=tenant).first()
        model_name = getattr(config, "model_name", "hash-fallback")

    vector = _normalized_hash_vector(f"{model_name}:{text}")
    return vector, model_name or "hash-fallback"


def embed_query(text: str, tenant) -> List[float]:
    vector, _ = embed_text(text, tenant)
    return list(vector)


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    numerator = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)
