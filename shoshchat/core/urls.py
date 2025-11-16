"""Core URL configuration for ShoshChat AI."""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.health import health, ready
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({'csrfToken': get_token(request)})

def public_plans_view(request):
    """Public billing plans endpoint that doesn't require tenant context"""
    plans = [
        {
            "slug": "starter", 
            "name": "Starter Plan", 
            "monthly_price": "19.99", 
            "message_quota": 1000, 
            "features": ["Basic AI", "Email Support"]
        },
        {
            "slug": "pro", 
            "name": "Professional Plan", 
            "monthly_price": "49.99", 
            "message_quota": 5000, 
            "features": ["Advanced AI", "Priority Support"]
        },
        {
            "slug": "enterprise", 
            "name": "Enterprise Plan", 
            "monthly_price": "99.99", 
            "message_quota": 15000, 
            "features": ["Premium AI", "24/7 Support"]
        }
    ]
    return JsonResponse(plans, safe=False)

urlpatterns = [
    path("admin/", admin.site.urls),
    # CSRF Token
    path("api/v1/csrf/", csrf_token_view, name="csrf_token"),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # API Endpoints
    path("api/v1/auth/", include("accounts.api.urls")),
    path("api/v1/chat/", include("chatbot.urls")),
    path("api/v1/billing/", include("billing.urls")),
    path("api/v1/tenants/", include("tenancy.urls")),
    path("api/v1/knowledge/", include("knowledge.api.urls")),
    # Health Checks
    path("healthz", health, name="healthz"),
    path("readyz", ready, name="readyz"),
]

# Add static files handling in development and when whitenoise fails
if settings.DEBUG or True:  # Force for debugging
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
