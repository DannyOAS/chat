"""Fallback adapter for OpenAI models."""
from __future__ import annotations


class OpenAIAdapter:
    """Placeholder adapter returning a deterministic response."""

    def generate(self, message: str) -> str:  # pragma: no cover - simple stub
        return f"Our assistant is unavailable. Echo: {message}"
