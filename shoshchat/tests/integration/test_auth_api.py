"""Integration tests for authentication API."""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status

from tests.factories import UserFactory

User = get_user_model()


@pytest.mark.integration
@pytest.mark.django_db
class TestRegistrationAPI:
    """Tests for user registration endpoint."""

    def test_register_user_success(self, api_client):
        """Test successful user registration."""
        url = reverse("accounts:register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username="newuser").exists()
        user = User.objects.get(username="newuser")
        assert user.email == "newuser@example.com"
        assert user.check_password("StrongPass123!")

    def test_register_password_mismatch(self, api_client):
        """Test registration fails with password mismatch."""
        url = reverse("accounts:register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "password_confirm": "DifferentPass123!",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(username="newuser").exists()

    def test_register_duplicate_username(self, api_client):
        """Test registration fails with duplicate username."""
        UserFactory(username="existinguser")
        url = reverse("accounts:register")
        data = {
            "username": "existinguser",
            "email": "different@example.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.integration
@pytest.mark.django_db
class TestLoginAPI:
    """Tests for login endpoint."""

    def test_login_success(self, api_client):
        """Test successful login."""
        user = UserFactory(username="testuser", password="testpass123")
        url = reverse("accounts:login")
        data = {
            "username": "testuser",
            "password": "testpass123",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "user" in response.data
        assert response.data["user"]["username"] == "testuser"

    def test_login_invalid_credentials(self, api_client):
        """Test login fails with invalid credentials."""
        UserFactory(username="testuser", password="testpass123")
        url = reverse("accounts:login")
        data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.integration
@pytest.mark.django_db
class TestProfileAPI:
    """Tests for profile endpoint."""

    def test_get_profile_authenticated(self, authenticated_client, user):
        """Test getting profile when authenticated."""
        url = reverse("accounts:profile")
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    def test_get_profile_unauthenticated(self, api_client):
        """Test getting profile when not authenticated."""
        url = reverse("accounts:profile")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
