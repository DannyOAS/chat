"""App configuration for business management."""
from django.apps import AppConfig


class BusinessConfig(AppConfig):
    """Configuration for the business app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "business"
    verbose_name = "Business Management"
