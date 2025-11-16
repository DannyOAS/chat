"""
Database performance optimization settings.

Add these settings to your production settings file (core/settings/production.py).
"""

# Database connection pooling with django-db-pool or psycopg2 pooling
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "shoshchat_prod",
        "USER": "shoshchat",
        "PASSWORD": "<password>",
        "HOST": "db",
        "PORT": "5432",
        # Connection pooling settings
        "CONN_MAX_AGE": 600,  # Persistent connections (10 minutes)
        "ATOMIC_REQUESTS": True,  # Wrap each request in a transaction
        "OPTIONS": {
            # Connection pool size (per worker process)
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30 second query timeout
            # Server-side cursor for large querysets
            "server_side_binding": True,
        },
        # Connection health checks
        "CONN_HEALTH_CHECKS": True,
    }
}

# Database router for read replicas (optional)
DATABASE_ROUTERS = ["core.db_router.ReadReplicaRouter"]

# Read replica configuration
DATABASES["read_replica"] = {
    **DATABASES["default"],
    "HOST": "db-read-replica",
}

# Query logging and monitoring
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "db_queries": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/db_queries.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["db_queries"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Query optimization settings
# Log queries slower than this threshold (milliseconds)
DATABASE_QUERY_LOG_THRESHOLD = 100

# Maximum number of queries per request (raise warning if exceeded)
DATABASE_QUERY_COUNT_THRESHOLD = 50

# Enable query optimization middleware
MIDDLEWARE = [
    # ... other middleware
    "core.middleware.performance.DatabaseOptimizationMiddleware",
    "core.middleware.performance.QueryCountMiddleware",
]
