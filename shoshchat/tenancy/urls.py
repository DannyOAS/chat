"""Routing for tenant management endpoints."""
from __future__ import annotations

from django.urls import path

from .api.views import TenantCreateView

app_name = "tenancy"

urlpatterns = [
    path("", TenantCreateView.as_view(), name="create"),
]
