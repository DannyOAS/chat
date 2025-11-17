"""Custom throttling classes for chatbot API."""
from rest_framework.throttling import SimpleRateThrottle


class WidgetRateThrottle(SimpleRateThrottle):
    """
    Rate limit chat requests per widget ID.

    Limits anonymous widget requests based on widget_id to prevent abuse
    while allowing authenticated users higher limits.
    """
    scope = "widget"

    def get_cache_key(self, request, view):
        """Generate cache key based on widget_id or user."""
        # For authenticated requests, use user-based throttling
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                "scope": "widget_auth",
                "ident": request.user.pk,
            }

        # For anonymous widget requests, use widget_id
        widget_id = request.data.get("widget_id")
        if widget_id:
            return self.cache_format % {
                "scope": self.scope,
                "ident": widget_id,
            }

        # Fallback to IP-based throttling for requests without widget_id
        ident = self.get_ident(request)
        return self.cache_format % {
            "scope": self.scope,
            "ident": ident,
        }
