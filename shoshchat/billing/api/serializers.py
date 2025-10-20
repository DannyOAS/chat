"""Serializers for billing endpoints."""
from __future__ import annotations

from rest_framework import serializers

from billing.models import Subscription, UsageLog


class UsageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageLog
        fields = ["message_count", "period_start", "period_end", "last_message_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source="plan.name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "plan_name",
            "active",
            "current_period_start",
            "current_period_end",
        ]
