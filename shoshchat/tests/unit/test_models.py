"""Unit tests for models."""
import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role, TenantMembership, UserProfile
from tests.factories import TenantFactory, UserFactory

User = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class TestUserProfile:
    """Tests for UserProfile model."""

    def test_user_profile_created_on_user_creation(self):
        """Test that UserProfile is created when user is created."""
        user = UserFactory()
        assert hasattr(user, "profile")
        assert isinstance(user.profile, UserProfile)

    def test_email_verified_default_false(self):
        """Test that email_verified defaults to False."""
        user = UserFactory()
        assert user.profile.email_verified is False

    def test_two_factor_disabled_by_default(self):
        """Test that 2FA is disabled by default."""
        user = UserFactory()
        assert user.profile.two_factor_enabled is False
        assert user.profile.two_factor_secret == ""
        assert user.profile.backup_codes == []


@pytest.mark.unit
@pytest.mark.django_db
class TestTenantMembership:
    """Tests for TenantMembership model."""

    def test_create_membership(self):
        """Test creating a tenant membership."""
        user = UserFactory()
        tenant = TenantFactory()
        membership = TenantMembership.objects.create(
            user=user,
            tenant=tenant,
            role=Role.OWNER,
        )
        assert membership.user == user
        assert membership.tenant == tenant
        assert membership.role == Role.OWNER
        assert membership.is_active is True

    def test_owner_has_all_permissions(self):
        """Test that owner role has all permissions."""
        membership = TenantMembership(role=Role.OWNER)
        assert membership.has_permission("manage_billing")
        assert membership.has_permission("manage_members")
        assert membership.has_permission("manage_chatbots")
        assert membership.has_permission("manage_knowledge")
        assert membership.has_permission("view_analytics")
        assert membership.has_permission("delete_tenant")

    def test_admin_cannot_manage_billing(self):
        """Test that admin cannot manage billing."""
        membership = TenantMembership(role=Role.ADMIN)
        assert not membership.has_permission("manage_billing")
        assert membership.has_permission("manage_members")
        assert membership.has_permission("manage_chatbots")

    def test_member_limited_permissions(self):
        """Test that member has limited permissions."""
        membership = TenantMembership(role=Role.MEMBER)
        assert not membership.has_permission("manage_billing")
        assert not membership.has_permission("manage_members")
        assert membership.has_permission("manage_chatbots")
        assert membership.has_permission("manage_knowledge")

    def test_guest_minimal_permissions(self):
        """Test that guest has minimal permissions."""
        membership = TenantMembership(role=Role.GUEST)
        assert not membership.has_permission("manage_billing")
        assert not membership.has_permission("manage_members")
        assert not membership.has_permission("manage_chatbots")
        assert membership.has_permission("view_analytics")

    def test_unique_user_tenant_pair(self):
        """Test that user can only have one membership per tenant."""
        user = UserFactory()
        tenant = TenantFactory()
        TenantMembership.objects.create(user=user, tenant=tenant, role=Role.MEMBER)

        # Trying to create another membership should fail
        with pytest.raises(Exception):  # IntegrityError
            TenantMembership.objects.create(user=user, tenant=tenant, role=Role.ADMIN)
