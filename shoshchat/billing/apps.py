"""Billing app configuration."""
from __future__ import annotations

from django.apps import AppConfig


class BillingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "billing"

    def ready(self) -> None:  # pragma: no cover - import side effects
        from . import signals  # noqa: F401
