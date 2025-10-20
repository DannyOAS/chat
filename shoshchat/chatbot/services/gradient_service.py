"""Integration with DigitalOcean Gradient endpoints."""
from __future__ import annotations

import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class GradientLLM:
    """Thin wrapper around the DigitalOcean Gradient inference endpoint."""

    def __init__(self, endpoint: str, *, timeout: int = 30) -> None:
        self.endpoint = endpoint
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {settings.DO_GRADIENT_API_KEY}",
            "Content-Type": "application/json",
        }

    def generate(self, message: str, **kwargs: Any) -> str:
        payload = {
            "inputs": [
                {"role": "system", "content": kwargs.get("system_prompt", "")},
                {"role": "user", "content": message},
            ]
        }
        response = requests.post(
            self.endpoint,
            headers=self.headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        try:
            return data["outputs"][0]["content"]
        except (KeyError, IndexError) as exc:  # pragma: no cover - defensive
            logger.exception("Unexpected Gradient response: %s", data)
            raise ValueError("Unexpected response from Gradient API") from exc
