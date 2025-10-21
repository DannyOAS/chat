"""Utilities for splitting knowledge source text into manageable chunks."""
from __future__ import annotations

from typing import Iterable

DEFAULT_CHUNK_SIZE = 700  # characters
DEFAULT_CHUNK_OVERLAP = 100  # characters


def chunk_text(text: str, chunk_size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_CHUNK_OVERLAP) -> Iterable[str]:
    """Yield overlapping chunks from the provided text."""

    if not text:
        return []

    cleaned = " ".join(text.split())
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        yield cleaned[start:end]
        if end == length:
            break
        start = max(0, end - overlap)
