"""Billing factory for tests."""
import factory
from django.utils import timezone

from billing.models import Plan, Subscription
from .tenant import TenantFactory


class PlanFactory(factory.django.DjangoModelFactory):
    """Factory for creating test plans."""

    class Meta:
        model = Plan

    slug = factory.Sequence(lambda n: f"plan_{n}")
    name = factory.Faker("word")
    stripe_price_id = factory.Sequence(lambda n: f"price_test_{n}")
    monthly_price = factory.Faker("pydecimal", left_digits=2, right_digits=2, positive=True)
    message_quota = factory.Iterator([1000, 5000, 10000, 50000])
    features = factory.LazyFunction(lambda: ["Feature 1", "Feature 2"])


class SubscriptionFactory(factory.django.DjangoModelFactory):
    """Factory for creating test subscriptions."""

    class Meta:
        model = Subscription

    tenant = factory.SubFactory(TenantFactory)
    plan = factory.SubFactory(PlanFactory)
    stripe_subscription_id = factory.Sequence(lambda n: f"sub_test_{n}")
    active = True
    current_period_start = factory.LazyFunction(timezone.now)
    current_period_end = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))
