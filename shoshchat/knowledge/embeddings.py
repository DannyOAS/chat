"""Real semantic embeddings using Sentence Transformers with hash fallback."""
from __future__ import annotations

import hashlib
import logging
import math
from typing import List, Sequence

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Standard dimension for all-MiniLM-L6-v2
EMBEDDING_DIMENSION = 384

# Model configuration
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_TTL = 3600 * 24  # 24 hours


def _get_embedding_model():
    """Get or create the embedding model singleton."""
    cache_key = "embedding_model_instance"
    model = cache.get(cache_key)

    if model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {DEFAULT_MODEL}")
            model = SentenceTransformer(DEFAULT_MODEL)
            cache.set(cache_key, model, timeout=None)  # Never expire
            logger.info("Embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None

    return model


def _normalized_hash_vector(text: str, dimension: int = EMBEDDING_DIMENSION) -> List[float]:
    """Return a deterministic embedding vector derived from a hash digest (fallback only)."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    required_bytes = dimension
    repeats = required_bytes // len(digest) + 1
    data = (digest * repeats)[:required_bytes]
    vector = [((byte / 255.0) * 2.0 - 1.0) for byte in data]
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def embed_text(
    text: str,
    tenant=None,
    *,
    model_name: str | None = None,
    use_cache: bool = True
) -> tuple[Sequence[float], str]:
    """
    Generate a semantic embedding for the given text.

    Uses Sentence Transformers (all-MiniLM-L6-v2) for real semantic embeddings.
    Falls back to hash-based embeddings if model fails to load.

    Args:
        text: Text to embed
        tenant: Tenant context (for future custom models)
        model_name: Override model name
        use_cache: Whether to cache embeddings

    Returns:
        Tuple of (embedding_vector, model_name_used)
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for embedding")
        return _normalized_hash_vector(""), "hash-fallback"

    # Check cache first
    if use_cache:
        cache_key = f"embedding:{hashlib.md5(text.encode()).hexdigest()}"
        cached = cache.get(cache_key)
        if cached:
            return cached

    # Try to use Sentence Transformer
    model = _get_embedding_model()

    if model is not None:
        try:
            # Generate embedding
            embedding = model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False
            )
            vector = embedding.tolist()
            result = (vector, DEFAULT_MODEL)

            # Cache the result
            if use_cache:
                cache.set(cache_key, result, timeout=CACHE_TTL)

            return result

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Fall through to hash fallback

    # Fallback to hash-based embeddings
    logger.warning("Using hash-based fallback embeddings (not semantic!)")
    effective_model = model_name or "hash-fallback"
    vector = _normalized_hash_vector(f"{effective_model}:{text}", EMBEDDING_DIMENSION)
    return vector, "hash-fallback"


def embed_query(text: str, tenant=None) -> List[float]:
    """
    Embed a search query.

    Args:
        text: Query text
        tenant: Tenant context

    Returns:
        Embedding vector as list of floats
    """
    vector, _ = embed_text(text, tenant, use_cache=False)  # Don't cache queries
    return list(vector)


def embed_batch(texts: List[str], tenant=None) -> List[List[float]]:
    """
    Embed multiple texts efficiently in batch.

    Args:
        texts: List of texts to embed
        tenant: Tenant context

    Returns:
        List of embedding vectors
    """
    if not texts:
        return []

    model = _get_embedding_model()

    if model is not None:
        try:
            embeddings = model.encode(
                texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=len(texts) > 10,
                batch_size=32
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")

    # Fallback: embed individually
    logger.warning("Using hash fallback for batch embeddings")
    return [embed_text(text, tenant)[0] for text in texts]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Note: This is kept for compatibility, but pgvector handles
    similarity calculations much more efficiently in the database.

    Args:
        a: First vector
        b: Second vector

    Returns:
        Cosine similarity score between -1 and 1
    """
    if len(a) != len(b):
        raise ValueError(f"Vector dimension mismatch: {len(a)} vs {len(b)}")

    numerator = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return numerator / (norm_a * norm_b)


def get_embedding_info() -> dict:
    """Get information about the current embedding configuration."""
    model = _get_embedding_model()

    return {
        "model": DEFAULT_MODEL if model else "hash-fallback",
        "dimension": EMBEDDING_DIMENSION,
        "model_loaded": model is not None,
        "cache_enabled": True,
    }
