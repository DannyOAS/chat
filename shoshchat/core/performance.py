"""
Performance optimization utilities for ShoshChat AI.

Includes caching decorators, query optimization helpers, and performance monitoring.
"""
from __future__ import annotations

import functools
import hashlib
import logging
import time
from typing import Any, Callable, Optional

from django.core.cache import cache
from django.db import connection
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def cached(timeout: int = 300, key_prefix: str = "", key_func: Optional[Callable] = None):
    """
    Decorator to cache function results in Redis.

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
        key_func: Custom function to generate cache key from args

    Usage:
        @cached(timeout=600, key_prefix='user_profile')
        def get_user_profile(user_id):
            return expensive_database_query(user_id)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                # Default: hash all args and kwargs
                key_str = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
                key_hash = hashlib.md5(key_str.encode()).hexdigest()
                cache_key = f"{key_prefix}:{key_hash}"

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Cache miss - execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, timeout=timeout)

            return result

        # Add method to invalidate cache
        def invalidate(*args, **kwargs):
            """Invalidate cached result for specific args."""
            if key_func:
                cache_key = f"{key_prefix}:{key_func(*args, **kwargs)}"
            else:
                key_str = f"{func.__module__}.{func.__name__}:{args}:{sorted(kwargs.items())}"
                key_hash = hashlib.md5(key_str.encode()).hexdigest()
                cache_key = f"{key_prefix}:{key_hash}"
            cache.delete(cache_key)

        wrapper.invalidate = invalidate
        return wrapper

    return decorator


def cached_property_with_ttl(ttl: int = 300):
    """
    Cached property with time-to-live.

    Like @property but caches the result with a TTL.

    Usage:
        class MyModel(models.Model):
            @cached_property_with_ttl(ttl=600)
            def expensive_computation(self):
                return calculate_something_expensive()
    """

    def decorator(func: Callable) -> property:
        attr_name = f"_cached_{func.__name__}"
        timestamp_name = f"_cached_{func.__name__}_timestamp"

        @functools.wraps(func)
        def wrapper(self):
            # Check if cached value exists and is not expired
            if hasattr(self, attr_name):
                timestamp = getattr(self, timestamp_name, 0)
                if time.time() - timestamp < ttl:
                    return getattr(self, attr_name)

            # Compute and cache value
            value = func(self)
            setattr(self, attr_name, value)
            setattr(self, timestamp_name, time.time())
            return value

        return property(wrapper)

    return decorator


class QueryOptimizer:
    """
    Helper class for optimizing Django querysets.

    Automatically applies select_related and prefetch_related.
    """

    @staticmethod
    def optimize_queryset(
        queryset: QuerySet,
        select_related: list[str] = None,
        prefetch_related: list[str] = None,
    ) -> QuerySet:
        """
        Optimize queryset with select_related and prefetch_related.

        Args:
            queryset: Django QuerySet to optimize
            select_related: List of foreign key fields to select_related
            prefetch_related: List of fields to prefetch_related

        Returns:
            Optimized QuerySet
        """
        if select_related:
            queryset = queryset.select_related(*select_related)

        if prefetch_related:
            queryset = queryset.prefetch_related(*prefetch_related)

        return queryset

    @staticmethod
    def count_queries(func: Callable) -> Callable:
        """
        Decorator to count database queries made by a function.

        Useful for identifying N+1 query problems.

        Usage:
            @QueryOptimizer.count_queries
            def my_view(request):
                # View code...
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Reset query count
            from django.conf import settings

            if not settings.DEBUG:
                # Only count queries in DEBUG mode
                return func(*args, **kwargs)

            # Get initial query count
            initial_queries = len(connection.queries)

            # Execute function
            result = func(*args, **kwargs)

            # Get final query count
            final_queries = len(connection.queries)
            query_count = final_queries - initial_queries

            # Log query count
            logger.info(
                f"{func.__module__}.{func.__name__} executed {query_count} queries"
            )

            # Warn if too many queries
            if query_count > 10:
                logger.warning(
                    f"High query count ({query_count}) in {func.__name__}. "
                    "Consider using select_related or prefetch_related."
                )

            return result

        return wrapper


class PerformanceMonitor:
    """
    Monitor function execution time and log slow operations.
    """

    @staticmethod
    def monitor(threshold_ms: int = 1000, log_level: str = "WARNING"):
        """
        Decorator to monitor function execution time.

        Args:
            threshold_ms: Threshold in milliseconds to log slow operations
            log_level: Log level for slow operations (DEBUG, INFO, WARNING, ERROR)

        Usage:
            @PerformanceMonitor.monitor(threshold_ms=500)
            def slow_function():
                # Slow code...
        """

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                # Execute function
                result = func(*args, **kwargs)

                # Calculate execution time
                end_time = time.time()
                execution_time_ms = (end_time - start_time) * 1000

                # Log if exceeds threshold
                if execution_time_ms > threshold_ms:
                    log_func = getattr(logger, log_level.lower())
                    log_func(
                        f"Slow operation: {func.__module__}.{func.__name__} "
                        f"took {execution_time_ms:.2f}ms (threshold: {threshold_ms}ms)"
                    )

                return result

            return wrapper

        return decorator


def bulk_create_optimized(model_class, objects: list[dict], batch_size: int = 1000):
    """
    Optimized bulk create with batching.

    Args:
        model_class: Django model class
        objects: List of dictionaries with model data
        batch_size: Number of objects to create per batch

    Returns:
        List of created model instances
    """
    instances = [model_class(**obj) for obj in objects]

    # Create in batches
    created = []
    for i in range(0, len(instances), batch_size):
        batch = instances[i : i + batch_size]
        created.extend(model_class.objects.bulk_create(batch, batch_size=batch_size))

    logger.info(f"Bulk created {len(created)} {model_class.__name__} instances")

    return created


def batch_update_optimized(
    queryset: QuerySet, update_fields: dict, batch_size: int = 1000
):
    """
    Optimized batch update with chunking.

    Args:
        queryset: QuerySet to update
        update_fields: Dictionary of fields to update
        batch_size: Number of objects to update per batch

    Returns:
        Number of updated objects
    """
    total_updated = 0

    # Get IDs in batches
    ids = list(queryset.values_list("id", flat=True))

    for i in range(0, len(ids), batch_size):
        batch_ids = ids[i : i + batch_size]
        updated = queryset.filter(id__in=batch_ids).update(**update_fields)
        total_updated += updated

    logger.info(f"Batch updated {total_updated} objects")

    return total_updated


class CacheWarmer:
    """
    Utilities for cache warming on deployment.
    """

    @staticmethod
    def warm_tenant_configs():
        """
        Pre-warm cache with tenant configurations.

        Should be called on deployment to avoid cache stampede.
        """
        from tenancy.models import Tenant

        tenants = Tenant.objects.filter(is_active=True)
        count = 0

        for tenant in tenants:
            cache_key = f"tenant_config:{tenant.id}"
            cache.set(cache_key, tenant, timeout=3600)
            count += 1

        logger.info(f"Warmed cache for {count} tenant configs")
        return count

    @staticmethod
    def warm_llm_configs():
        """Pre-warm cache with LLM configurations."""
        # TODO: Implement when LLM config model is ready
        pass


def invalidate_cache_pattern(pattern: str):
    """
    Invalidate all cache keys matching a pattern.

    Args:
        pattern: Redis key pattern (e.g., 'user:*', 'tenant_config:*')

    Note: This requires Redis with KEYS command support.
    Only use in development or with small key spaces.
    """
    try:
        from django_redis import get_redis_connection

        redis_conn = get_redis_connection("default")

        # Get all keys matching pattern
        keys = redis_conn.keys(pattern)

        if keys:
            redis_conn.delete(*keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching '{pattern}'")
            return len(keys)

        return 0

    except Exception as e:
        logger.error(f"Failed to invalidate cache pattern '{pattern}': {e}")
        return 0


# Pre-configured cache decorators for common use cases
cache_5min = cached(timeout=300)
cache_15min = cached(timeout=900)
cache_1hour = cached(timeout=3600)
cache_1day = cached(timeout=86400)
