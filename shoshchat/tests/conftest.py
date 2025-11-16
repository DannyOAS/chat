"""Pytest configuration and shared fixtures."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tenancy.models import Tenant
from billing.models import Plan

User = get_user_model()


@pytest.fixture
def api_client():
    """Return a DRF API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create a test user."""
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
    )


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def tenant(db, user):
    """Create a test tenant."""
    return Tenant.objects.create(
        name="Test Company",
        schema_name="test_company",
        industry="retail",
        owner=user,
        onboarding_completed=True,
    )


@pytest.fixture
def plan(db):
    """Create a test plan."""
    return Plan.objects.create(
        slug="starter",
        name="Starter Plan",
        stripe_price_id="price_test123",
        monthly_price=29.00,
        message_quota=1000,
        features=["Basic support", "1 user"],
    )


@pytest.fixture
def user_with_tenant(user, tenant):
    """Return a user with a tenant."""
    return user


@pytest.fixture
def authenticated_client_with_tenant(authenticated_client, tenant, user):
    """Return an authenticated client with tenant context."""
    # Create tenant membership
    from accounts.models import Role, TenantMembership

    TenantMembership.objects.create(
        user=user,
        tenant=tenant,
        role=Role.OWNER,
    )

    # Add tenant to request
    authenticated_client.tenant = tenant
    return authenticated_client
