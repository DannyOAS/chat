"""Custom middleware for tenant routing and enforcement."""
from __future__ import annotations

from django.http import HttpRequest, HttpResponse


class TenantOnboardingMiddleware:
    """Ensure tenants have completed onboarding before accessing dashboard."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Placeholder for onboarding checks per tenant
        return self.get_response(request)
