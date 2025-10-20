"""Integration with DigitalOcean Gradient endpoints."""
from __future__ import annotations

import logging
from typing import Any

try:  # pragma: no cover - imported lazily in tests
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional dependency in tests
    requests = None  # type: ignore[assignment]

try:  # pragma: no cover - exercised implicitly when Django is installed
    from django.conf import settings
except ModuleNotFoundError:  # pragma: no cover - used in lightweight test envs
    class _FallbackSettings:  # noqa: D401 - simple container for API key
        """Fallback shim providing the attribute used by the service."""

        DO_GRADIENT_API_KEY = ""

    settings = _FallbackSettings()  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class GradientLLM:
    """Thin wrapper around the DigitalOcean Gradient inference endpoint."""

    def __init__(
        self, endpoint: str, *, timeout: int = 30, api_key: str | None = None
    ) -> None:
        self.endpoint = endpoint
        self.timeout = timeout
        key = api_key if api_key is not None else getattr(settings, "DO_GRADIENT_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def generate(self, message: str, **kwargs: Any) -> str:
        payload = {
            "inputs": [
                {"role": "system", "content": kwargs.get("system_prompt", "")},
                {"role": "user", "content": message},
            ]
        }
        if requests is None:  # pragma: no cover - environment misconfiguration
            raise RuntimeError("The requests library is required to call Gradient API")
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
