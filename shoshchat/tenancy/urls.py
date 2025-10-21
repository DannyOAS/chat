"""Routing for tenant management endpoints."""
from __future__ import annotations

from django.urls import path

from .api.views import (
    TenantCreateView,
    TenantDetailView,
    TenantDomainView,
    TenantEmbedCodeView,
    TenantSettingsView,
)

app_name = "tenancy"

urlpatterns = [
    path("", TenantCreateView.as_view(), name="create"),
    path("me/", TenantDetailView.as_view(), name="detail"),
    path("me/settings/", TenantSettingsView.as_view(), name="settings"),
    path("me/domains/", TenantDomainView.as_view(), name="domains"),
    path("me/embed/", TenantEmbedCodeView.as_view(), name="embed"),
]
