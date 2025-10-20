"""Application configuration for the tenancy app."""
from __future__ import annotations

from django.apps import AppConfig


class TenancyConfig(AppConfig):
    """Configure tenancy application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "tenancy"
