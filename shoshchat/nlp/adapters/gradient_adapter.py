"""Adapter for DigitalOcean Gradient LLM."""
from __future__ import annotations

from chatbot.services.gradient_service import GradientLLM


class GradientAdapter:
    """Adapter responsible for calling Gradient using tenant config."""

    def __init__(self, config) -> None:
        self.config = config
        self.client = GradientLLM(config.endpoint)

    def generate(self, message: str) -> str:
        return self.client.generate(message, system_prompt=self.config.system_prompt)
