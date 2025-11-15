"""Routing for authentication endpoints."""
from __future__ import annotations

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    EmailVerificationConfirmView,
    EmailVerificationRequestView,
    InviteMemberView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    ProfileView,
    RegisterOnboardView,
    RegisterView,
    RemoveMemberView,
    ShoshTokenObtainPairView,
    TenantMembersView,
    TwoFactorDisableView,
    TwoFactorEnableView,
    TwoFactorSetupView,
    TwoFactorStatusView,
    UpdateMemberRoleView,
)

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("register/onboard/", RegisterOnboardView.as_view(), name="register-onboard"),
    path("login/", ShoshTokenObtainPairView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="refresh"),
    path("me/", ProfileView.as_view(), name="profile"),
    # Password Reset
    path("password/reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password/reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    # Email Verification
    path("email/verify/", EmailVerificationRequestView.as_view(), name="email-verify"),
    path("email/verify/confirm/", EmailVerificationConfirmView.as_view(), name="email-verify-confirm"),
    # Two-Factor Authentication
    path("2fa/setup/", TwoFactorSetupView.as_view(), name="2fa-setup"),
    path("2fa/enable/", TwoFactorEnableView.as_view(), name="2fa-enable"),
    path("2fa/disable/", TwoFactorDisableView.as_view(), name="2fa-disable"),
    path("2fa/status/", TwoFactorStatusView.as_view(), name="2fa-status"),
    # RBAC - Tenant Members
    path("members/", TenantMembersView.as_view(), name="tenant-members"),
    path("members/invite/", InviteMemberView.as_view(), name="invite-member"),
    path("members/<int:membership_id>/role/", UpdateMemberRoleView.as_view(), name="update-member-role"),
    path("members/<int:membership_id>/remove/", RemoveMemberView.as_view(), name="remove-member"),
]
