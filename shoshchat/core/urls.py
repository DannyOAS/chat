"""Core URL configuration for ShoshChat AI."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

from core.health import health, ready

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.api.urls")),
    path("api/v1/chat/", include("chatbot.urls")),
    path("api/v1/billing/", include("billing.urls")),
    path("api/v1/tenants/", include("tenancy.urls")),
    path("api/v1/knowledge/", include("knowledge.api.urls")),
    path("healthz", health, name="healthz"),
    path("readyz", ready, name="readyz"),
]
