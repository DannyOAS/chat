"""Billing and subscription models."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:  # pragma: no cover - typing only
    from business.models import Business


class Plan(models.Model):
    """Represents a subscription plan synchronized with Stripe."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=255)
    monthly_price = models.DecimalField(max_digits=7, decimal_places=2)
    message_quota = models.PositiveIntegerField(default=0)
    features = models.JSONField(default=list, blank=True)

    class Meta:
        # This model should be in the public schema for registration
        pass

    def __str__(self) -> str:  # pragma: no cover - human readable
        return self.name


class Subscription(models.Model):
    """Stores active subscription information for a business."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'active'], name='subscription_tenant_active_idx'),
            models.Index(fields=['current_period_end'], name='subscription_period_end_idx'),
            models.Index(fields=['stripe_subscription_id'], name='subscription_stripe_id_idx'),
        ]

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"{self.tenant} -> {self.plan}"


class UsageLog(models.Model):
    """Tracks chat message usage for quota enforcement."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    message_count = models.PositiveIntegerField(default=0)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("tenant", "period_start", "period_end")
        indexes = [
            models.Index(fields=['tenant', 'period_start', 'period_end'], name='usage_log_tenant_period_idx'),
            models.Index(fields=['-last_message_at'], name='usage_log_last_message_idx'),
        ]

    def increment(self, amount: int = 1, *, timestamp=None) -> None:
        self.message_count += amount
        if timestamp:
            self.last_message_at = timestamp
        self.save(update_fields=["message_count", "last_message_at"])
