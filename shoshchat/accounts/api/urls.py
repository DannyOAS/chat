"""Routing for authentication endpoints."""
from __future__ import annotations

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    EmailVerificationConfirmView,
    EmailVerificationRequestView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterOnboardView,
    RegisterView,
    ShoshTokenObtainPairView,
)

app_name = "accounts"

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register/onboard/", RegisterOnboardView.as_view(), name="register-onboard"),
    path("login/", ShoshTokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", ProfileView.as_view(), name="profile"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("email/verify/", EmailVerificationRequestView.as_view(), name="email-verify"),
    path("email/verify/confirm/", EmailVerificationConfirmView.as_view(), name="email-verify-confirm"),
]
