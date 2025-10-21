"""Accounts-related models."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Stores auxiliary information for auth users."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Profile for {self.user}"  # pragma: no cover
