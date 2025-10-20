"""Celery tasks for billing and usage tracking."""
from __future__ import annotations

import logging

import stripe
from celery import shared_task
from django.conf import settings

from billing.signals import handle_stripe_event
from tenancy.models import Tenant

logger = logging.getLogger(__name__)


@shared_task
def sync_stripe_subscriptions() -> int:
    """Synchronise Stripe subscriptions for known tenants.

    Returns the number of subscriptions processed. The task relies on the
    configured Stripe API key and will gracefully skip tenants when the API call
    fails so that a single outage does not cancel the entire run.
    """

    api_key = settings.STRIPE_LIVE_SECRET_KEY or settings.STRIPE_TEST_SECRET_KEY
    if not api_key:
        logger.warning("Stripe API key missing; skipping subscription sync")
        return 0

    stripe.api_key = api_key
    processed = 0

    tenant_qs = Tenant.objects.exclude(stripe_customer_id="").values_list("id", "stripe_customer_id")
    for tenant_id, customer_id in tenant_qs.iterator():
        try:
            customer = stripe.Customer.retrieve(
                customer_id,
                expand=["subscriptions"],
            )
        except stripe.error.StripeError:
            logger.exception(
                "Unable to retrieve Stripe customer",
                extra={"customer_id": customer_id, "tenant_id": tenant_id},
            )
            continue

        subscriptions = (customer.get("subscriptions") or {}).get("data", [])
        for subscription in subscriptions:
            handle_stripe_event("customer.subscription.updated", subscription)
            processed += 1

    logger.info("Stripe subscription sync completed", extra={"processed": processed})
    return processed
