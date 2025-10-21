"""Signals for accounts app."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_profile(sender, instance: User, created: bool, **_: object) -> None:
    """Ensure every user has an associated profile."""

    if created:
        UserProfile.objects.create(user=instance)
