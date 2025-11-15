"""Accounts-related models."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Stores auxiliary information for auth users."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, default="")
    backup_codes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Profile for {self.user}"  # pragma: no cover


class Role(models.TextChoices):
    """User roles for RBAC."""

    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MEMBER = "member", "Member"
    GUEST = "guest", "Guest"


class TenantMembership(models.Model):
    """Represents a user's membership in a tenant with a specific role."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="invitations_sent"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("user", "tenant")
        ordering = ["-joined_at"]
        indexes = [
            models.Index(fields=["tenant", "role"], name="tenant_role_idx"),
            models.Index(fields=["user", "is_active"], name="user_active_idx"),
        ]

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"{self.user.username} - {self.tenant.name} ({self.get_role_display()})"  # pragma: no cover

    def has_permission(self, permission: str) -> bool:
        """Check if this membership's role has the specified permission."""
        permissions_map = {
            Role.OWNER: {
                "manage_billing",
                "manage_members",
                "manage_chatbots",
                "manage_knowledge",
                "view_analytics",
                "delete_tenant",
                "manage_settings",
            },
            Role.ADMIN: {
                "manage_members",
                "manage_chatbots",
                "manage_knowledge",
                "view_analytics",
                "manage_settings",
            },
            Role.MEMBER: {
                "manage_chatbots",
                "manage_knowledge",
                "view_analytics",
            },
            Role.GUEST: {
                "view_analytics",
            },
        }
        return permission in permissions_map.get(self.role, set())
