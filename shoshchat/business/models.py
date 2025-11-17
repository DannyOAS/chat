"""
Simplified business models for single-domain SaaS architecture.

Each user owns exactly one business. No subdomain routing, no schema isolation.
Simple and clean like Mailchimp, Shopify, etc.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class Business(models.Model):
    """
    Represents a user's business.

    Each user owns exactly one business (one-to-one relationship).
    All business data is filtered by business_id in queries.
    """

    RETAIL = "retail"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    EDUCATION = "education"
    OTHER = "other"

    INDUSTRY_CHOICES = [
        (RETAIL, "Retail / E-commerce"),
        (FINANCE, "Finance / Insurance"),
        (HEALTHCARE, "Healthcare"),
        (TECHNOLOGY, "Technology / SaaS"),
        (EDUCATION, "Education / Training"),
        (OTHER, "Other"),
    ]

    # Core fields
    name = models.CharField(max_length=255, help_text="Business name")
    slug = models.SlugField(max_length=100, unique=True, help_text="URL-friendly identifier")

    # Widget identification (for anonymous widget usage)
    widget_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Unique widget ID for anonymous chat widget embedding",
    )

    # Owner (one-to-one with user)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business",
        help_text="Business owner (each user owns one business)",
    )

    # Business details
    industry = models.CharField(max_length=32, choices=INDUSTRY_CHOICES, default=OTHER)
    description = models.TextField(blank=True, help_text="Business description")
    website = models.URLField(blank=True, help_text="Business website")
    phone = models.CharField(max_length=20, blank=True)

    # Billing
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)

    # Onboarding
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step = models.IntegerField(default=0)

    # Widget customization
    widget_welcome_message = models.CharField(
        max_length=255,
        default="Hi there! How can I help you today?",
    )
    widget_primary_color = models.CharField(max_length=7, default="#14b8a6")
    widget_accent_color = models.CharField(max_length=7, default="#10b981")
    widget_position = models.CharField(
        max_length=20,
        choices=[
            ("bottom-right", "Bottom Right"),
            ("bottom-left", "Bottom Left"),
        ],
        default="bottom-right",
    )

    # Widget security
    allowed_domains = models.JSONField(
        default=list,
        blank=True,
        help_text="List of domains allowed to embed this widget (empty = all domains allowed)",
    )

    # Status
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["widget_id"]),
            models.Index(fields=["is_active", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.owner.username})"

    def save(self, *args, **kwargs):
        """Generate slug if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            # Ensure unique slug
            while Business.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)


class TeamMember(models.Model):
    """
    Team members who can access a business (optional collaboration feature).

    This is simpler than multi-tenant: the business owner can invite team members
    to help manage their business, but each user still owns their own business.
    """

    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

    ROLE_CHOICES = [
        (ADMIN, "Admin - Full access except billing"),
        (MEMBER, "Member - Can manage chatbot and knowledge"),
        (VIEWER, "Viewer - Read-only access"),
    ]

    # Relationships
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="team_members",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="team_memberships",
    )

    # Role
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default=MEMBER)

    # Invitation
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="team_invitations_sent",
    )
    invited_at = models.DateTimeField(auto_now_add=True)

    # Status
    is_active = models.BooleanField(default=True)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("business", "user")
        ordering = ["-invited_at"]
        indexes = [
            models.Index(fields=["business", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} → {self.business.name} ({self.get_role_display()})"

    def has_permission(self, permission: str) -> bool:
        """Check if this team member has a specific permission."""
        permissions_map = {
            self.ADMIN: {
                "manage_chatbot",
                "manage_knowledge",
                "manage_team",
                "view_analytics",
                "manage_settings",
            },
            self.MEMBER: {
                "manage_chatbot",
                "manage_knowledge",
                "view_analytics",
            },
            self.VIEWER: {
                "view_analytics",
            },
        }
        return permission in permissions_map.get(self.role, set())
