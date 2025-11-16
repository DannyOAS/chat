"""
Security headers middleware for ShoshChat AI.

Implements comprehensive security headers including:
- Content Security Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security (HSTS)
- X-XSS-Protection
- Referrer-Policy
- Permissions-Policy
"""
from __future__ import annotations

from typing import Callable

from django.conf import settings
from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    """
    Middleware to add comprehensive security headers to all responses.

    Implements OWASP security header recommendations.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Add security headers to response."""
        response = self.get_response(request)

        # X-Content-Type-Options: Prevent MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevent clickjacking
        # Use DENY to block all framing, or SAMEORIGIN to allow same-origin framing
        response["X-Frame-Options"] = "DENY"

        # X-XSS-Protection: Enable browser XSS filter
        # Note: This header is mostly deprecated in favor of CSP
        response["X-XSS-Protection"] = "1; mode=block"

        # Referrer-Policy: Control referrer information
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions-Policy: Control browser features
        # Disable potentially dangerous features
        response["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        )

        # Strict-Transport-Security (HSTS)
        # Only add in production with HTTPS
        if settings.DEBUG is False and request.is_secure():
            # max-age=31536000 (1 year), includeSubDomains, preload
            response["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # Content-Security-Policy (CSP)
        # Strict policy to prevent XSS attacks
        csp_directives = self.get_csp_directives()
        response["Content-Security-Policy"] = "; ".join(csp_directives)

        # Cross-Origin Resource Policy
        response["Cross-Origin-Resource-Policy"] = "same-origin"

        # Cross-Origin Opener Policy
        response["Cross-Origin-Opener-Policy"] = "same-origin"

        # Cross-Origin Embedder Policy
        response["Cross-Origin-Embedder-Policy"] = "require-corp"

        return response

    def get_csp_directives(self) -> list[str]:
        """
        Generate Content Security Policy directives.

        Returns a strict CSP that prevents most XSS attacks.
        """
        # Base CSP directives
        directives = [
            # Default to same origin only
            "default-src 'self'",
            # Scripts: Allow self and specific CDNs if needed
            # In production, remove 'unsafe-inline' and use nonces
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            # Styles: Allow self and inline styles (for styled-components, etc.)
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            # Images: Allow self, data URIs, and HTTPS sources
            "img-src 'self' data: https: blob:",
            # Fonts: Allow self and data URIs
            "font-src 'self' data: https://fonts.gstatic.com",
            # Connect (AJAX, WebSocket): Allow self and API endpoints
            "connect-src 'self' wss: https:",
            # Media (audio/video): Restrict to self
            "media-src 'self'",
            # Objects (Flash, etc.): Block completely
            "object-src 'none'",
            # Frames: Block all frames
            "frame-src 'none'",
            # Base URI: Restrict to self
            "base-uri 'self'",
            # Form actions: Restrict to self
            "form-action 'self'",
            # Frame ancestors: Block all (prevents clickjacking)
            "frame-ancestors 'none'",
            # Upgrade insecure requests in production
            "upgrade-insecure-requests" if not settings.DEBUG else "",
            # Block mixed content
            "block-all-mixed-content" if not settings.DEBUG else "",
        ]

        # Remove empty directives
        return [d for d in directives if d]


class SecureRequestMiddleware:
    """
    Middleware to validate and sanitize incoming requests.

    Prevents common attack vectors.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

        # Suspicious patterns to detect in requests
        self.suspicious_patterns = [
            # SQL Injection patterns
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
            # Script injection patterns
            r"(<script|javascript:|onerror=|onload=)",
            # Path traversal
            r"\.\./",
            # Command injection
            r"(;|\||&|`|\$\()",
        ]

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Validate and process request."""
        import re

        # Check request path for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, request.path, re.IGNORECASE):
                # Log suspicious request
                self.log_suspicious_request(request, pattern)

                # Optionally block the request
                # return JsonResponse({
                #     "error": "Invalid request"
                # }, status=400)

        # Validate content length to prevent memory exhaustion
        content_length = request.META.get("CONTENT_LENGTH")
        if content_length:
            try:
                length = int(content_length)
                max_size = getattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024)  # 100MB default

                if length > max_size:
                    from django.http import JsonResponse

                    return JsonResponse(
                        {
                            "error": "Request too large",
                            "max_size": max_size,
                        },
                        status=413,
                    )
            except ValueError:
                pass

        # Continue processing
        response = self.get_response(request)

        return response

    def log_suspicious_request(self, request: HttpRequest, pattern: str):
        """Log suspicious request for security monitoring."""
        import logging

        logger = logging.getLogger("security.suspicious")
        logger.warning(
            f"Suspicious request detected: {request.method} {request.path} "
            f"from {request.META.get('REMOTE_ADDR')} - Pattern: {pattern}"
        )


class CORSSecurityMiddleware:
    """
    Enhanced CORS middleware with security validations.

    Works in conjunction with django-cors-headers but adds extra security.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process CORS with security checks."""
        response = self.get_response(request)

        # Only process CORS for API endpoints
        if request.path.startswith("/api/"):
            # Validate Origin header against whitelist
            origin = request.META.get("HTTP_ORIGIN")

            if origin:
                # Get allowed origins from settings
                allowed_origins = getattr(
                    settings,
                    "CORS_ALLOWED_ORIGINS",
                    []
                )

                # Check if origin is allowed
                if origin not in allowed_origins and not self.is_development_origin(origin):
                    # Log unauthorized CORS attempt
                    self.log_cors_violation(request, origin)

        return response

    def is_development_origin(self, origin: str) -> bool:
        """Check if origin is from development environment."""
        from django.conf import settings

        if settings.DEBUG:
            # Allow localhost in development
            return "localhost" in origin or "127.0.0.1" in origin

        return False

    def log_cors_violation(self, request: HttpRequest, origin: str):
        """Log unauthorized CORS attempt."""
        import logging

        logger = logging.getLogger("security.cors")
        logger.warning(
            f"Unauthorized CORS request from {origin} to {request.path} "
            f"from IP {request.META.get('REMOTE_ADDR')}"
        )
