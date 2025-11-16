"""Comprehensive health check endpoints for monitoring and observability."""
from __future__ import annotations

import time
from typing import Any, Dict

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


def health(_: object) -> JsonResponse:
    """
    Basic health check - returns 200 if the application is running.
    This is used by load balancers and container orchestration.
    """
    return JsonResponse({
        "status": "healthy",
        "timestamp": timezone.now().isoformat(),
        "service": "shoshchat-api",
    })


def ready(_: object) -> JsonResponse:
    """
    Comprehensive readiness check - verifies all dependencies are available.
    Returns 200 only if all critical services are operational.
    """
    start_time = time.time()
    checks = {
        "database": _check_database(),
        "cache": _check_cache(),
        "celery": _check_celery(),
    }

    # Overall status is healthy only if all checks pass
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    status_code = 200 if all_healthy else 503

    response_time = (time.time() - start_time) * 1000  # Convert to ms

    return JsonResponse({
        "status": "healthy" if all_healthy else "unhealthy",
        "timestamp": timezone.now().isoformat(),
        "service": "shoshchat-api",
        "checks": checks,
        "response_time_ms": round(response_time, 2),
    }, status=status_code)


def _check_database() -> Dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        latency = (time.time() - start) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "database": connection.settings_dict.get("NAME", "unknown"),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "database": connection.settings_dict.get("NAME", "unknown"),
        }


def _check_cache() -> Dict[str, Any]:
    """Check Redis cache connectivity and performance."""
    try:
        start = time.time()
        test_key = "health_check_test"
        test_value = "ok"

        # Test write
        cache.set(test_key, test_value, timeout=10)

        # Test read
        cached_value = cache.get(test_key)

        # Cleanup
        cache.delete(test_key)

        latency = (time.time() - start) * 1000

        if cached_value != test_value:
            return {
                "status": "unhealthy",
                "error": "Cache read/write mismatch",
                "latency_ms": round(latency, 2),
            }

        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "backend": settings.CACHES.get("default", {}).get("BACKEND", "unknown"),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "backend": settings.CACHES.get("default", {}).get("BACKEND", "unknown"),
        }


def _check_celery() -> Dict[str, Any]:
    """Check Celery worker availability."""
    try:
        from core.celery import app as celery_app

        start = time.time()

        # Inspect active workers
        inspect = celery_app.control.inspect(timeout=2.0)
        stats = inspect.stats()

        latency = (time.time() - start) * 1000

        if not stats:
            return {
                "status": "unhealthy",
                "error": "No active Celery workers found",
                "latency_ms": round(latency, 2),
            }

        worker_count = len(stats)

        return {
            "status": "healthy",
            "latency_ms": round(latency, 2),
            "workers": worker_count,
            "worker_names": list(stats.keys()),
        }
    except Exception as e:
        return {
            "status": "degraded",  # Celery is optional for read-only operations
            "error": str(e),
            "note": "Celery unavailable - background tasks may be delayed",
        }
