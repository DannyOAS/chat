"""Service helpers for tenant provisioning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from django.db import transaction
from django.utils import timezone

from billing.models import Plan, Subscription
from tenancy.models import Domain, Tenant


@dataclass(slots=True)
class ProvisioningResult:
    tenant: Tenant
    subscription: Optional[Subscription]
    domain: Optional[Domain]


@transaction.atomic
def create_tenant_with_subscription(
    *,
    name: str,
    schema_name: str,
    industry: str,
    owner,
    plan: Optional[Plan] = None,
    domain_name: Optional[str] = None,
    accent: str = "retail",
    welcome_message: str | None = None,
    primary_color: str | None = None,
) -> ProvisioningResult:
    """Provision a tenant schema and optional subscription details."""

    normalized_schema = schema_name.replace(" ", "-").lower()
    tenant = Tenant.objects.create(
        name=name,
        schema_name=normalized_schema,
        industry=industry,
        owner=owner,
        widget_accent=accent,
        widget_welcome_message=welcome_message or Tenant.widget_welcome_message.field.default,
        widget_primary_color=primary_color or Tenant.widget_primary_color.field.default,
        onboarding_completed=True,
    )

    subscription: Subscription | None = None
    if plan:
        now = timezone.now()
        subscription = Subscription.objects.create(
            tenant=tenant,
            plan=plan,
            active=True,
            current_period_start=now,
            current_period_end=now + timezone.timedelta(days=30),
        )
        tenant.on_trial = False
        tenant.paid_until = subscription.current_period_end.date()
        tenant.save(update_fields=["on_trial", "paid_until"])

    domain: Domain | None = None
    if domain_name:
        domain = Domain.objects.create(
            tenant=tenant,
            domain=domain_name.lower(),
            is_primary=True,
        )

    return ProvisioningResult(tenant=tenant, subscription=subscription, domain=domain)
