"""Models for chatbot interactions."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from django.utils import timezone

if TYPE_CHECKING:  # pragma: no cover - typing only
    from tenancy.models import Tenant
    from business.models import Business


class ChatSession(models.Model):
    """Represents a chat session between a user and the chatbot."""

    user_id = models.CharField(max_length=255)
    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    started_at = models.DateTimeField(auto_now_add=True)
    last_interaction_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'user_id'], name='chat_session_tenant_user_idx'),
            models.Index(fields=['-last_interaction_at'], name='chat_session_last_interaction_idx'),
        ]

    @classmethod
    def log_interaction(
        cls, tenant: "Tenant", user_id: str, message: str, response: str
    ) -> "Message":
        session, _ = cls.objects.get_or_create(
            tenant=tenant,
            user_id=user_id,
        )
        cls.objects.filter(pk=session.pk).update(last_interaction_at=timezone.now())
        return Message.objects.create(
            session=session,
            role=Message.Role.USER,
            content=message,
            response_text=response,
        )


class Message(models.Model):
    """Stores an individual message exchanged in a session."""

    class Role(models.TextChoices):
        USER = "user", "User"
        BOT = "bot", "Bot"
        SYSTEM = "system", "System"

    session = models.ForeignKey(ChatSession, related_name="messages", on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    response_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session', '-created_at'], name='message_session_created_idx'),
            models.Index(fields=['-created_at'], name='message_created_idx'),
        ]
        ordering = ['-created_at']


class Intent(models.Model):
    """Intent classification for retail and finance businesses."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    samples = models.JSONField(default=list, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'name'], name='intent_tenant_name_idx'),
        ]


class Response(models.Model):
    """Predefined responses for structured intents."""

    intent = models.ForeignKey(Intent, related_name="responses", on_delete=models.CASCADE)
    tone = models.CharField(max_length=50, default="neutral")
    body = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("intent", "tone")
