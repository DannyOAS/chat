"""Core URL configuration for ShoshChat AI."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.health import health, ready

urlpatterns = [
    path("admin/", admin.site.urls),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API Endpoints
    path("api/v1/auth/", include("accounts.api.urls")),
    path("api/v1/business/", include("business.api.urls")),  # Single-domain business API
    path("api/v1/chat/", include("chatbot.urls")),
    path("api/v1/billing/", include("billing.urls")),
    path("api/v1/tenants/", include("tenancy.urls")),  # Legacy - will be removed in Phase 4
    path("api/v1/knowledge/", include("knowledge.api.urls")),
    # Health Checks
    path("healthz", health, name="healthz"),
    path("readyz", ready, name="readyz"),
]
