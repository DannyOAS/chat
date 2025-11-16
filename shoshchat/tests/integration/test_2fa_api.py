"""Integration tests for Two-Factor Authentication API."""
import pytest
from django.urls import reverse
from rest_framework import status

from accounts.two_factor import setup_two_factor, verify_totp
from tests.factories import UserFactory


@pytest.mark.integration
@pytest.mark.django_db
class TestTwoFactorSetup:
    """Tests for 2FA setup endpoint."""

    def test_2fa_setup_authenticated(self, authenticated_client, user):
        """Test 2FA setup returns QR code and backup codes."""
        url = reverse("accounts:2fa-setup")
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert "secret" in response.data
        assert "qr_code" in response.data
        assert "backup_codes" in response.data
        assert len(response.data["backup_codes"]) == 10
        assert response.data["qr_code"].startswith("data:image/png;base64,")

        # Check user profile updated
        user.profile.refresh_from_db()
        assert user.profile.two_factor_secret != ""
        assert len(user.profile.backup_codes) == 10

    def test_2fa_setup_unauthenticated(self, api_client):
        """Test 2FA setup requires authentication."""
        url = reverse("accounts:2fa-setup")
        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.django_db
class TestTwoFactorEnable:
    """Tests for 2FA enable endpoint."""

    def test_2fa_enable_with_valid_token(self, authenticated_client, user):
        """Test enabling 2FA with valid TOTP token."""
        # Set up 2FA first
        setup_data = setup_two_factor(user)
        secret = setup_data["secret"]

        # Generate valid TOTP token
        import pyotp
        totp = pyotp.TOTP(secret)
        token = totp.now()

        url = reverse("accounts:2fa-enable")
        data = {"token": token}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "Two-factor authentication enabled" in response.data["detail"]

        # Check 2FA is enabled
        user.profile.refresh_from_db()
        assert user.profile.two_factor_enabled is True

    def test_2fa_enable_with_invalid_token(self, authenticated_client, user):
        """Test enabling 2FA with invalid token fails."""
        setup_two_factor(user)

        url = reverse("accounts:2fa-enable")
        data = {"token": "000000"}  # Invalid token
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Check 2FA is not enabled
        user.profile.refresh_from_db()
        assert user.profile.two_factor_enabled is False


@pytest.mark.integration
@pytest.mark.django_db
class TestTwoFactorDisable:
    """Tests for 2FA disable endpoint."""

    def test_2fa_disable_with_valid_password(self, authenticated_client, user):
        """Test disabling 2FA with valid password."""
        # Enable 2FA first
        setup_data = setup_two_factor(user)
        user.profile.two_factor_enabled = True
        user.profile.save()

        url = reverse("accounts:2fa-disable")
        data = {"password": "testpass123"}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check 2FA is disabled
        user.profile.refresh_from_db()
        assert user.profile.two_factor_enabled is False
        assert user.profile.two_factor_secret == ""
        assert user.profile.backup_codes == []

    def test_2fa_disable_with_invalid_password(self, authenticated_client, user):
        """Test disabling 2FA with invalid password fails."""
        setup_data = setup_two_factor(user)
        user.profile.two_factor_enabled = True
        user.profile.save()

        url = reverse("accounts:2fa-disable")
        data = {"password": "wrongpassword"}
        response = authenticated_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Check 2FA is still enabled
        user.profile.refresh_from_db()
        assert user.profile.two_factor_enabled is True


@pytest.mark.integration
@pytest.mark.django_db
class TestTwoFactorStatus:
    """Tests for 2FA status endpoint."""

    def test_2fa_status_disabled(self, authenticated_client, user):
        """Test 2FA status when disabled."""
        url = reverse("accounts:2fa-status")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["enabled"] is False
        assert response.data["backup_codes_remaining"] == 0

    def test_2fa_status_enabled(self, authenticated_client, user):
        """Test 2FA status when enabled."""
        setup_data = setup_two_factor(user)
        user.profile.two_factor_enabled = True
        user.profile.save()

        url = reverse("accounts:2fa-status")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["enabled"] is True
        assert response.data["backup_codes_remaining"] == 10
