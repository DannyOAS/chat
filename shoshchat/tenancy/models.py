"""Tenant models leveraging django-tenants."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import models
from django_tenants.models import DomainMixin, TenantMixin

User = get_user_model()


class Tenant(TenantMixin):
    """Represents a tenant schema for the SaaS platform."""

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
        User, related_name="tenants", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    widget_accent = models.CharField(max_length=32, default="retail")
    widget_welcome_message = models.CharField(
        max_length=255, default="Hi there! I'm your ShoshChat assistant."
    )
    widget_primary_color = models.CharField(max_length=7, default="#14b8a6")

    auto_create_schema = True

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"{self.name} ({self.schema_name})"


class Domain(DomainMixin):
    """Stores custom domains mapped to tenants."""

    tenant = models.ForeignKey(Tenant, related_name="domains", on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Domain"
        verbose_name_plural = "Domains"

    def __str__(self) -> str:  # pragma: no cover - human readable
        return self.domain
