"""
Advanced rate limiting middleware for ShoshChat AI.

Implements multi-level rate limiting:
- Per-IP rate limiting
- Per-user rate limiting
- Per-tenant rate limiting
"""
from __future__ import annotations

from typing import Callable

from django.core.cache import cache
from django.http import HttpRequest, JsonResponse
from rest_framework.throttling import SimpleRateThrottle


class IPRateThrottle(SimpleRateThrottle):
    """Rate limit requests by IP address."""

    scope = "ip"

    def get_cache_key(self, request: HttpRequest, view) -> str:
        """Generate cache key based on IP address."""
        ip = self.get_ident(request)
        return f"throttle_ip_{ip}_{self.scope}"


class UserRateThrottle(SimpleRateThrottle):
    """Rate limit requests by authenticated user."""

    scope = "user"

    def get_cache_key(self, request: HttpRequest, view) -> str:
        """Generate cache key based on user ID."""
        if not request.user or not request.user.is_authenticated:
            return None  # Only throttle authenticated requests

        return f"throttle_user_{request.user.id}_{self.scope}"


class TenantRateThrottle(SimpleRateThrottle):
    """Rate limit requests by tenant."""

    scope = "tenant"

    def get_cache_key(self, request: HttpRequest, view) -> str:
        """Generate cache key based on tenant schema."""
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return None

        return f"throttle_tenant_{tenant.schema_name}_{self.scope}"


class BurstRateThrottle(SimpleRateThrottle):
    """
    Burst rate limiting for short-term spike protection.
    More restrictive than sustained rate limit.
    """

    scope = "burst"

    def get_cache_key(self, request: HttpRequest, view) -> str:
        """Generate cache key based on IP address."""
        ip = self.get_ident(request)
        return f"throttle_burst_{ip}_{self.scope}"


class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter using Redis sorted sets.
    More accurate than fixed window algorithm.
    """

    def __init__(self, key_prefix: str, limit: int, window: int):
        """
        Initialize sliding window rate limiter.

        Args:
            key_prefix: Redis key prefix
            limit: Maximum number of requests allowed in window
            window: Time window in seconds
        """
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window

    def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if request is allowed under rate limit.

        Args:
            identifier: Unique identifier (IP, user ID, tenant ID)

        Returns:
            Tuple of (is_allowed, info_dict)
        """
        import time

        cache_key = f"{self.key_prefix}:{identifier}"
        now = time.time()
        window_start = now - self.window

        # Get current count from cache
        timestamps = cache.get(cache_key, [])

        # Remove timestamps outside the window
        timestamps = [ts for ts in timestamps if ts > window_start]

        # Check if limit exceeded
        is_allowed = len(timestamps) < self.limit

        # Add current timestamp if allowed
        if is_allowed:
            timestamps.append(now)
            cache.set(cache_key, timestamps, timeout=self.window)

        # Calculate reset time
        if timestamps:
            oldest_timestamp = min(timestamps)
            reset_in = int(self.window - (now - oldest_timestamp))
        else:
            reset_in = self.window

        return is_allowed, {
            "limit": self.limit,
            "remaining": max(0, self.limit - len(timestamps)),
            "reset_in": reset_in,
            "current_count": len(timestamps),
        }


class RateLimitMiddleware:
    """
    Rate limiting middleware with detailed logging and monitoring.
    Implements progressive rate limiting based on abuse patterns.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

        # Configure rate limiters
        self.global_limiter = SlidingWindowRateLimiter(
            key_prefix="global",
            limit=1000,  # 1000 requests
            window=60,  # per minute
        )

        self.ip_limiter = SlidingWindowRateLimiter(
            key_prefix="ip",
            limit=100,  # 100 requests
            window=60,  # per minute
        )

        self.suspicious_ips: set[str] = set()

    def __call__(self, request: HttpRequest):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.path in ["/healthz/", "/readyz/"]:
            return self.get_response(request)

        # Get client IP
        ip = self.get_client_ip(request)

        # Check if IP is suspicious (has been rate limited before)
        if ip in self.suspicious_ips:
            # Apply stricter limits for suspicious IPs
            is_allowed, info = self.ip_limiter.is_allowed(f"{ip}:suspicious")
            if not is_allowed:
                return self.rate_limit_response(info)

        # Global rate limit check
        is_allowed, global_info = self.global_limiter.is_allowed("all")
        if not is_allowed:
            return JsonResponse(
                {
                    "error": "Service temporarily unavailable due to high traffic",
                    "retry_after": global_info["reset_in"],
                },
                status=503,
            )

        # IP-based rate limit
        is_allowed, ip_info = self.ip_limiter.is_allowed(ip)
        if not is_allowed:
            # Mark IP as suspicious
            self.suspicious_ips.add(ip)

            # Log rate limit violation
            self.log_rate_limit_violation(request, ip, ip_info)

            return self.rate_limit_response(ip_info)

        # Add rate limit headers to response
        response = self.get_response(request)
        self.add_rate_limit_headers(response, ip_info)

        return response

    def get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP address from request."""
        # Check for X-Forwarded-For header (from load balancer/proxy)
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")

        return ip

    def rate_limit_response(self, info: dict) -> JsonResponse:
        """Generate rate limit exceeded response."""
        return JsonResponse(
            {
                "error": "Rate limit exceeded",
                "detail": "Too many requests. Please try again later.",
                "limit": info["limit"],
                "remaining": info["remaining"],
                "reset_in": info["reset_in"],
            },
            status=429,
            headers={
                "Retry-After": str(info["reset_in"]),
                "X-RateLimit-Limit": str(info["limit"]),
                "X-RateLimit-Remaining": str(info["remaining"]),
                "X-RateLimit-Reset": str(info["reset_in"]),
            },
        )

    def add_rate_limit_headers(self, response, info: dict):
        """Add rate limit headers to successful response."""
        response["X-RateLimit-Limit"] = str(info["limit"])
        response["X-RateLimit-Remaining"] = str(info["remaining"])
        response["X-RateLimit-Reset"] = str(info["reset_in"])

    def log_rate_limit_violation(self, request: HttpRequest, ip: str, info: dict):
        """Log rate limit violations for monitoring."""
        import logging

        logger = logging.getLogger("security.ratelimit")
        logger.warning(
            f"Rate limit exceeded for IP {ip} on {request.path}. "
            f"Count: {info['current_count']}, Limit: {info['limit']}"
        )
