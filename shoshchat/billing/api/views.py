"""Billing API views."""
from __future__ import annotations

import logging

from rest_framework import permissions, response, status
from rest_framework.response import Response
from rest_framework.views import APIView

from billing.models import Subscription, UsageLog
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

    def post(self, request, *args, **kwargs):
        event_type = request.data.get("type", "unknown")
        logger.info("Stripe webhook received", extra={"event_type": event_type})
        return response.Response({"received": True}, status=status.HTTP_200_OK)
