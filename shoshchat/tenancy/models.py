"""Legacy tenant models - simplified for data migration."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Tenant(models.Model):
    """Legacy tenant model - simplified for backward compatibility during migration."""

    RETAIL = "retail"
    FINANCE = "finance"
    INDUSTRY_CHOICES = [
        (RETAIL, "Retail / E-commerce"),
        (FINANCE, "Finance / Insurance"),
    ]

    name = models.CharField(max_length=255)
    schema_name = models.CharField(max_length=63, unique=True)
    industry = models.CharField(max_length=32, choices=INDUSTRY_CHOICES)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    onboarding_completed = models.BooleanField(default=False)
    owner = models.ForeignKey(
        User, related_name="legacy_tenants", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    widget_accent = models.CharField(max_length=32, default="retail")
    widget_welcome_message = models.CharField(
        max_length=255, default="Hi there! I'm your ShoshChat assistant."
    )
    widget_primary_color = models.CharField(max_length=7, default="#14b8a6")

    class Meta:
        verbose_name = "Legacy Tenant"
        verbose_name_plural = "Legacy Tenants"

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"{self.name} ({self.schema_name})"


class Domain(models.Model):
    """Legacy domain model - simplified for backward compatibility."""

    domain = models.CharField(max_length=253, unique=True)
    tenant = models.ForeignKey(Tenant, related_name="domains", on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Legacy Domain"
        verbose_name_plural = "Legacy Domains"

    def __str__(self) -> str:  # pragma: no cover - human readable
        return self.domain
