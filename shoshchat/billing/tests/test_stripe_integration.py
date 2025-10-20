"""Tests for Stripe webhook and sync workflows."""
from __future__ import annotations

import json
from datetime import datetime
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from billing.models import Plan, Subscription
from billing.tasks import sync_stripe_subscriptions
from tenancy.models import Tenant


class StripeWebhookTests(TestCase):
    def setUp(self) -> None:  # noqa: D401 - standard TestCase hook
        super().setUp()
        patcher = patch.object(Tenant, "auto_create_schema", False)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.tenant = Tenant.objects.create(
            name="Retail Corp",
            schema_name="retail_corp",
            industry=Tenant.RETAIL,
            stripe_customer_id="cus_123",
        )

    def test_subscription_created_updates_plan_and_subscription(self):
        url = reverse("billing:stripe-webhook")
        payload = {
            "id": "evt_123",
            "type": "customer.subscription.created",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "status": "active",
                    "current_period_start": 1_700_000_000,
                    "current_period_end": 1_700_086_400,
                    "items": {
                        "data": [
                            {
                                "price": {
                                    "id": "price_123",
                                    "nickname": "Retail Pro",
                                    "unit_amount": 9900,
                                    "metadata": {
                                        "message_quota": "1000",
                                        "features": "Priority support,Custom persona",
                                    },
                                }
                            }
                        ]
                    },
                }
            },
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        plan = Plan.objects.get(stripe_price_id="price_123")
        subscription = Subscription.objects.get(tenant=self.tenant)

        self.assertEqual(plan.name, "Retail Pro")
        self.assertEqual(plan.message_quota, 1000)
        self.assertEqual(plan.features, ["Priority support", "Custom persona"])
        self.assertTrue(subscription.active)
        self.assertEqual(subscription.plan, plan)
        self.assertEqual(subscription.stripe_subscription_id, "sub_123")
        self.assertEqual(subscription.current_period_end.date(), datetime.utcfromtimestamp(1_700_086_400).date())
        self.assertEqual(self.tenant.paid_until, datetime.utcfromtimestamp(1_700_086_400).date())

    def test_subscription_deleted_marks_inactive(self):
        Plan.objects.create(
            slug="retail-pro",
            name="Retail Pro",
            stripe_price_id="price_123",
            monthly_price=99,
        )
        Subscription.objects.create(
            tenant=self.tenant,
            plan=Plan.objects.get(stripe_price_id="price_123"),
            stripe_subscription_id="sub_123",
            active=True,
        )
        url = reverse("billing:stripe-webhook")
        payload = {
            "id": "evt_del",
            "type": "customer.subscription.deleted",
            "data": {
                "object": {
                    "id": "sub_123",
                    "customer": "cus_123",
                    "ended_at": 1_700_173_200,
                    "status": "canceled",
                }
            },
        }

        response = self.client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        subscription = Subscription.objects.get(tenant=self.tenant)
        self.assertFalse(subscription.active)
        self.assertEqual(
            subscription.current_period_end,
            datetime.fromtimestamp(1_700_173_200, tz=timezone.utc),
        )
        self.tenant.refresh_from_db()
        self.assertFalse(self.tenant.on_trial)


@override_settings(STRIPE_TEST_SECRET_KEY="sk_test")
class StripeSyncTaskTests(TestCase):
    def setUp(self) -> None:  # noqa: D401
        super().setUp()
        patcher = patch.object(Tenant, "auto_create_schema", False)
        self.addCleanup(patcher.stop)
        patcher.start()
        self.tenant = Tenant.objects.create(
            name="Sync Corp",
            schema_name="sync_corp",
            industry=Tenant.RETAIL,
            stripe_customer_id="cus_sync",
        )

    @patch("billing.tasks.stripe.Customer.retrieve")
    def test_sync_task_updates_subscriptions(self, mock_retrieve):
        mock_retrieve.return_value = {
            "subscriptions": {
                "data": [
                    {
                        "id": "sub_sync",
                        "customer": "cus_sync",
                        "status": "trialing",
                        "current_period_start": 1_700_000_000,
                        "current_period_end": 1_700_172_800,
                        "items": {
                            "data": [
                                {
                                    "price": {
                                        "id": "price_sync",
                                        "nickname": "Sync Plan",
                                        "unit_amount": 4900,
                                        "metadata": {"message_quota": "500"},
                                    }
                                }
                            ]
                        },
                    }
                ]
            }
        }

        processed = sync_stripe_subscriptions()

        self.assertEqual(processed, 1)
        subscription = Subscription.objects.get(tenant=self.tenant)
        self.assertEqual(subscription.stripe_subscription_id, "sub_sync")
        self.assertTrue(subscription.active)
        self.assertEqual(subscription.plan.name, "Sync Plan")
        self.assertEqual(subscription.plan.message_quota, 500)
        self.assertEqual(
            subscription.current_period_end,
            datetime.fromtimestamp(1_700_172_800, tz=timezone.utc),
        )
        self.tenant.refresh_from_db()
        self.assertTrue(self.tenant.on_trial)
