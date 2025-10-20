"""Billing and subscription models."""
from __future__ import annotations

from django.db import models


class Plan(models.Model):
    """Represents a subscription plan synchronized with Stripe."""

    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    stripe_price_id = models.CharField(max_length=255)
    monthly_price = models.DecimalField(max_digits=7, decimal_places=2)
    message_quota = models.PositiveIntegerField(default=0)
    features = models.JSONField(default=list, blank=True)

    def __str__(self) -> str:  # pragma: no cover - human readable
        return self.name


class Subscription(models.Model):
    """Stores active subscription information for a tenant."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    active = models.BooleanField(default=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"{self.tenant} -> {self.plan}"


class UsageLog(models.Model):
    """Tracks chat message usage for quota enforcement."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE)
    message_count = models.PositiveIntegerField(default=0)
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("tenant", "period_start", "period_end")

    def increment(self, amount: int = 1, *, timestamp=None) -> None:
        self.message_count += amount
        if timestamp:
            self.last_message_at = timestamp
        self.save(update_fields=["message_count", "last_message_at"])
