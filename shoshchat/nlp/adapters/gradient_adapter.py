"""Adapter for DigitalOcean Gradient LLM."""
from __future__ import annotations

from decouple import config as env_config
from chatbot.services.gradient_service import GradientLLM


class GradientAdapter:
    """Adapter responsible for calling Gradient using tenant config."""

    def __init__(self, config) -> None:
        self.config = config
        # Get API key from environment
        api_key = env_config('DO_GRADIENT_API_KEY', default='')
        self.client = GradientLLM(config.endpoint, api_key=api_key)

    def generate(self, message: str) -> str:
        return self.client.generate(message, system_prompt=self.config.system_prompt)
