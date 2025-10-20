"""Core URL configuration for ShoshChat AI."""
from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/chat/", include("chatbot.urls")),
    path("api/v1/billing/", include("billing.urls")),
    path("api/v1/tenants/", include("tenancy.urls")),
]
