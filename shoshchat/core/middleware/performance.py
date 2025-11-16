"""
Performance monitoring middleware for ShoshChat AI.

Tracks query counts, slow queries, and request performance.
"""
from __future__ import annotations

import logging
import time
from typing import Callable

from django.conf import settings
from django.db import connection, reset_queries
from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class QueryCountMiddleware:
    """
    Middleware to count and log database queries per request.

    Helps identify N+1 query problems and excessive database usage.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and count queries."""
        # Only track queries in DEBUG mode or if explicitly enabled
        if not getattr(settings, "DEBUG", False) and not getattr(
            settings, "TRACK_DB_QUERIES", False
        ):
            return self.get_response(request)

        # Reset query count
        reset_queries()

        # Get initial query count
        initial_count = len(connection.queries)

        # Process request
        response = self.get_response(request)

        # Get final query count
        final_count = len(connection.queries)
        query_count = final_count - initial_count

        # Add query count to response headers (for debugging)
        response["X-DB-Query-Count"] = str(query_count)

        # Log if exceeds threshold
        threshold = getattr(settings, "DATABASE_QUERY_COUNT_THRESHOLD", 50)
        if query_count > threshold:
            logger.warning(
                f"High query count on {request.method} {request.path}: "
                f"{query_count} queries (threshold: {threshold})"
            )

            # Log the actual queries in DEBUG mode
            if settings.DEBUG:
                for query in connection.queries[-query_count:]:
                    logger.debug(f"Query ({query['time']}s): {query['sql']}")

        return response


class DatabaseOptimizationMiddleware:
    """
    Middleware to monitor and log slow database queries.

    Helps identify performance bottlenecks.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and monitor queries."""
        if not getattr(settings, "DEBUG", False):
            return self.get_response(request)

        # Reset queries
        reset_queries()

        # Process request
        response = self.get_response(request)

        # Analyze queries
        slow_queries = []
        threshold_ms = getattr(settings, "DATABASE_QUERY_LOG_THRESHOLD", 100)

        for query in connection.queries:
            query_time_ms = float(query.get("time", 0)) * 1000

            if query_time_ms > threshold_ms:
                slow_queries.append(
                    {
                        "sql": query["sql"][:200],  # Truncate for logging
                        "time_ms": round(query_time_ms, 2),
                    }
                )

        # Log slow queries
        if slow_queries:
            logger.warning(
                f"Slow queries on {request.method} {request.path}: "
                f"{len(slow_queries)} queries slower than {threshold_ms}ms"
            )

            for query in slow_queries:
                logger.warning(
                    f"Slow query ({query['time_ms']}ms): {query['sql']}..."
                )

        return response


class RequestPerformanceMiddleware:
    """
    Middleware to track overall request performance.

    Logs slow requests and adds timing headers.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and track timing."""
        # Start timer
        start_time = time.time()

        # Process request
        response = self.get_response(request)

        # Calculate request duration
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000

        # Add timing headers
        response["X-Request-Duration-Ms"] = str(round(duration_ms, 2))

        # Log slow requests
        threshold_ms = getattr(settings, "SLOW_REQUEST_THRESHOLD_MS", 1000)
        if duration_ms > threshold_ms:
            logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {duration_ms:.2f}ms (threshold: {threshold_ms}ms)"
            )

        # Log request metrics
        if getattr(settings, "LOG_REQUEST_METRICS", False):
            logger.info(
                f"Request: {request.method} {request.path} "
                f"- {response.status_code} - {duration_ms:.2f}ms"
            )

        return response


class CacheHitRateMiddleware:
    """
    Middleware to track cache hit rates.

    Adds cache hit/miss information to response headers.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.cache_hits = 0
        self.cache_misses = 0

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and track cache stats."""
        # Store initial cache stats
        request._cache_hits_before = self.cache_hits
        request._cache_misses_before = self.cache_misses

        # Process request
        response = self.get_response(request)

        # Calculate cache stats for this request
        hits = self.cache_hits - request._cache_hits_before
        misses = self.cache_misses - request._cache_misses_before
        total = hits + misses

        if total > 0:
            hit_rate = (hits / total) * 100
            response["X-Cache-Hit-Rate"] = f"{hit_rate:.1f}%"
            response["X-Cache-Hits"] = str(hits)
            response["X-Cache-Misses"] = str(misses)

        return response

    def record_cache_hit(self):
        """Record a cache hit."""
        self.cache_hits += 1

    def record_cache_miss(self):
        """Record a cache miss."""
        self.cache_misses += 1


class CompressionMiddleware:
    """
    Middleware to compress responses.

    Compresses responses with gzip for faster delivery.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and compress response."""
        import gzip

        # Process request
        response = self.get_response(request)

        # Check if client accepts gzip
        if "gzip" not in request.META.get("HTTP_ACCEPT_ENCODING", ""):
            return response

        # Check if response should be compressed
        if not self._should_compress(response):
            return response

        # Compress response
        compressed_content = gzip.compress(response.content)

        # Update response
        response.content = compressed_content
        response["Content-Encoding"] = "gzip"
        response["Content-Length"] = str(len(compressed_content))

        return response

    def _should_compress(self, response: HttpResponse) -> bool:
        """Check if response should be compressed."""
        # Don't compress if already compressed
        if response.get("Content-Encoding"):
            return False

        # Don't compress small responses (overhead not worth it)
        if len(response.content) < 1024:  # 1KB
            return False

        # Only compress text-based content
        content_type = response.get("Content-Type", "")
        compressible_types = [
            "text/",
            "application/json",
            "application/javascript",
            "application/xml",
        ]

        return any(ct in content_type for ct in compressible_types)


class MemoryUsageMiddleware:
    """
    Middleware to track memory usage per request.

    Helps identify memory leaks and excessive memory consumption.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request and track memory."""
        import psutil
        import os

        # Get current process
        process = psutil.Process(os.getpid())

        # Get memory before request
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Process request
        response = self.get_response(request)

        # Get memory after request
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        mem_delta = mem_after - mem_before

        # Add memory usage to response headers
        response["X-Memory-Usage-MB"] = str(round(mem_after, 2))
        response["X-Memory-Delta-MB"] = str(round(mem_delta, 2))

        # Log if memory increased significantly
        if mem_delta > 10:  # More than 10MB increase
            logger.warning(
                f"High memory increase on {request.method} {request.path}: "
                f"+{mem_delta:.2f}MB (total: {mem_after:.2f}MB)"
            )

        return response
