"""Billing signal handlers for Stripe events."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Iterable

from django.utils import timezone

from billing.models import Plan, Subscription
from tenancy.models import Tenant

logger = logging.getLogger(__name__)


ACTIVATED_STATUSES: set[str] = {"active", "trialing"}


@dataclass(frozen=True)
class PlanPayload:
    """Subset of Stripe price payload required for local plans."""

    slug: str
    name: str
    stripe_price_id: str
    monthly_price: Decimal
    message_quota: int
    features: list[str]


def _parse_plan(price: dict) -> PlanPayload | None:
    """Convert a Stripe price dictionary into a plan payload."""

    price_id = price.get("id")
    if not price_id:
        return None

    nickname = price.get("nickname") or price_id
    amount = price.get("unit_amount")
    monthly_price = Decimal(amount or 0) / Decimal("100")
    metadata = price.get("metadata", {}) or {}

    quota_value = metadata.get("message_quota")
    try:
        message_quota = int(quota_value) if quota_value is not None else 0
    except (TypeError, ValueError):
        message_quota = 0

    features_raw = metadata.get("features") or []
    if isinstance(features_raw, str):
        features: Iterable[str] = (item.strip() for item in features_raw.split(","))
    elif isinstance(features_raw, Iterable):
        features = features_raw
    else:
        features = []

    filtered_features = [item for item in features if item]

    slug = metadata.get("slug") or nickname.lower().replace(" ", "-")

    return PlanPayload(
        slug=slug,
        name=nickname,
        stripe_price_id=price_id,
        monthly_price=monthly_price,
        message_quota=message_quota,
        features=filtered_features,
    )


def _parse_timestamp(value) -> datetime | None:
    if value in (None, ""):
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return None


def _update_tenant_subscription(tenant: Tenant, payload: dict) -> None:
    status = str(payload.get("status", "")).lower()
    price = (payload.get("items") or {}).get("data", [{}])[0].get("price", {})
    plan_payload = _parse_plan(price)

    if not plan_payload:
        logger.warning(
            "Stripe subscription payload missing price information", extra={"tenant": tenant.id}
        )
        return

    plan, _ = Plan.objects.update_or_create(
        stripe_price_id=plan_payload.stripe_price_id,
        defaults={
            "slug": plan_payload.slug,
            "name": plan_payload.name,
            "monthly_price": plan_payload.monthly_price,
            "message_quota": plan_payload.message_quota,
            "features": plan_payload.features,
        },
    )

    subscription, _ = Subscription.objects.get_or_create(
        tenant=tenant,
        defaults={
            "plan": plan,
            "stripe_subscription_id": payload.get("id", ""),
        },
    )

    subscription.plan = plan
    subscription.stripe_subscription_id = payload.get("id", subscription.stripe_subscription_id)
    subscription.active = status in ACTIVATED_STATUSES
    subscription.current_period_start = _parse_timestamp(payload.get("current_period_start"))
    subscription.current_period_end = _parse_timestamp(payload.get("current_period_end"))
    subscription.save()

    period_end = subscription.current_period_end
    if period_end:
        tenant.paid_until = period_end.date()
    tenant.on_trial = status == "trialing"
    tenant.onboarding_completed = True
    tenant.save(update_fields=["paid_until", "on_trial", "onboarding_completed"])


def handle_stripe_event(event_type: str, payload: dict) -> None:
    """Synchronise billing artefacts based on Stripe webhook events."""

    logger.info(
        "Stripe event received",
        extra={"event_type": event_type, "object_id": payload.get("id")},
    )

    customer_id = payload.get("customer")
    if not customer_id:
        logger.debug("Stripe event without customer; skipping")
        return

    tenant = Tenant.objects.filter(stripe_customer_id=customer_id).first()
    if not tenant:
        logger.warning(
            "Stripe event for unknown customer", extra={"customer_id": customer_id}
        )
        return

    event_type = event_type or ""
    event_type = event_type.lower()

    if event_type in {"customer.subscription.created", "customer.subscription.updated"}:
        _update_tenant_subscription(tenant, payload)
    elif event_type == "customer.subscription.deleted":
        Subscription.objects.filter(
            tenant=tenant,
            stripe_subscription_id=payload.get("id", ""),
        ).update(active=False, current_period_end=_parse_timestamp(payload.get("ended_at")))
        tenant.on_trial = False
        tenant.save(update_fields=["on_trial"])
    elif event_type == "invoice.payment_succeeded":
        # Mark tenant as paid through the period end of the invoice subscription.
        subscription_data = payload.get("lines", {}).get("data", [])
        if subscription_data:
            period = subscription_data[0].get("period", {})
            period_end = _parse_timestamp(period.get("end"))
            if period_end:
                tenant.paid_until = period_end.date()
                tenant.save(update_fields=["paid_until"])
