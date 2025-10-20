"""Routing for billing endpoints."""
from __future__ import annotations

from django.urls import path

from .api.views import ActiveSubscriptionView, StripeWebhookView, UsageSummaryView

app_name = "billing"

urlpatterns = [
    path("usage/", UsageSummaryView.as_view(), name="usage"),
    path("subscription/", ActiveSubscriptionView.as_view(), name="subscription"),
    path("stripe/webhook/", StripeWebhookView.as_view(), name="stripe-webhook"),
]
