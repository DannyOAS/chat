"""Compliance models for auditing and consent."""
from __future__ import annotations

import hashlib

from django.db import models


class AuditLog(models.Model):
    """Tenant scoped audit entries with hashed content."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE)
    user_id_hash = models.CharField(max_length=128)
    event_type = models.CharField(max_length=50)
    content_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)

    @classmethod
    def record(cls, tenant, user_id: str, event_type: str, content: str) -> "AuditLog":
        return cls.objects.create(
            tenant=tenant,
            user_id_hash=hashlib.sha256(user_id.encode()).hexdigest(),
            event_type=event_type,
            content_hash=hashlib.sha256(content.encode()).hexdigest(),
        )


class Consent(models.Model):
    """Tracks user consent records for data usage."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE)
    user_id_hash = models.CharField(max_length=128)
    granted = models.BooleanField(default=True)
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "user_id_hash")
