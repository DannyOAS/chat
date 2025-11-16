"""Tenant factory for tests."""
import factory
from faker import Faker

from tenancy.models import Tenant
from .user import UserFactory

fake = Faker()


class TenantFactory(factory.django.DjangoModelFactory):
    """Factory for creating test tenants."""

    class Meta:
        model = Tenant

    name = factory.Faker("company")
    schema_name = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "_"))
    industry = factory.Iterator(["retail", "finance", "healthcare", "tech"])
    owner = factory.SubFactory(UserFactory)
    widget_accent = "retail"
    widget_welcome_message = "Hello! How can I help you today?"
    widget_primary_color = "#14b8a6"
    onboarding_completed = True
    on_trial = True
    trial_ends = factory.Faker("future_date", end_date="+30d")
