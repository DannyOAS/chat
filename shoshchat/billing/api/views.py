"""Billing API views."""
from __future__ import annotations

import json
import logging
from typing import Any

import stripe
from django.conf import settings
from rest_framework import permissions, response, status
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.models import Subscription, UsageLog
from billing.signals import handle_stripe_event
from .serializers import SubscriptionSerializer, UsageLogSerializer

logger = logging.getLogger(__name__)


class UsageSummaryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        usage = (
            UsageLog.objects.filter(tenant=tenant).order_by("-period_end").first()
        )
        if not usage:
            return Response({})
        serializer = UsageLogSerializer(usage)
        return Response(serializer.data)


class ActiveSubscriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        subscription = Subscription.objects.filter(tenant=tenant, active=True).first()
        if not subscription:
            return Response({})
        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data)


class StripeWebhookView(APIView):
    permission_classes = [permissions.AllowAny]

    @staticmethod
    def _construct_event(payload: bytes, signature: str | None) -> dict[str, Any]:
        """Return a verified Stripe event payload."""

        secret = settings.DJSTRIPE_WEBHOOK_SECRET
        if secret and signature:
            try:
                event = stripe.Webhook.construct_event(payload, signature, secret)
                return event
            except stripe.error.SignatureVerificationError as exc:
                logger.warning("Stripe signature verification failed", exc_info=exc)
                raise
        try:
            return json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("Invalid JSON payload received from Stripe", exc_info=exc)
            raise

    def post(self, request, *args, **kwargs):
        payload = request.body
        signature = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = self._construct_event(payload, signature)
        except (ValueError, stripe.error.SignatureVerificationError):
            return response.Response(
                {"detail": "Invalid webhook payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        event_type = event.get("type", "unknown")
        data = event.get("data", {}).get("object", {})
        handle_stripe_event(event_type, data)

        logger.info("Stripe webhook processed", extra={"event_type": event_type})
        return response.Response({"received": True}, status=status.HTTP_200_OK)
