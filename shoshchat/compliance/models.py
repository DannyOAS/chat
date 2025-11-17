"""Compliance models for auditing and consent."""
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:  # pragma: no cover - typing only
    from business.models import Business


class AuditLog(models.Model):
    """Business scoped audit entries with hashed content."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    user = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    user_id_hash = models.CharField(max_length=128)
    action = models.CharField(max_length=100)  # e.g., "user.login", "knowledge.upload"
    event_type = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=100, blank=True)  # e.g., "KnowledgeSource", "Subscription"
    resource_id = models.CharField(max_length=255, blank=True)
    content_hash = models.CharField(max_length=128)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "timestamp"]),
            models.Index(fields=["tenant", "timestamp"]),
            models.Index(fields=["action", "timestamp"]),
        ]
        ordering = ["-timestamp"]

    @classmethod
    def record(cls, tenant, user_id: str, event_type: str, content: str) -> "AuditLog":
        return cls.objects.create(
            tenant=tenant,
            user_id_hash=hashlib.sha256(user_id.encode()).hexdigest(),
            event_type=event_type,
            action=event_type,  # For backwards compatibility
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
        )


class Consent(models.Model):
    """Tracks user consent records for data usage."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    user_id_hash = models.CharField(max_length=128)
    granted = models.BooleanField(default=True)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "user_id_hash")


class UserConsent(models.Model):
    """
    GDPR-compliant user consent tracking.

    Tracks consent for different data processing purposes.
    """

    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="consents")
    purpose = models.CharField(
        max_length=50,
        choices=[
            ("essential", "Essential Services"),
            ("analytics", "Analytics and Performance"),
            ("marketing", "Marketing Communications"),
            ("third_party", "Third-Party Integrations"),
        ],
    )
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "purpose")
        indexes = [
            models.Index(fields=["user", "purpose"]),
            models.Index(fields=["granted", "purpose"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.purpose}: {'✓' if self.granted else '✗'}"
