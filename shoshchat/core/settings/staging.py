"""Staging settings."""
from __future__ import annotations

from decouple import config

from .production import *  # noqa: F403

# Staging uses production settings with some relaxations
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)

# Sentry environment override
SENTRY_ENVIRONMENT = "staging"

# Lower sample rate for staging
SENTRY_TRACES_SAMPLE_RATE = config("SENTRY_TRACES_SAMPLE_RATE", default=0.25, cast=float)

# Can use console email backend in staging if needed
EMAIL_BACKEND = config(
    "DJANGO_EMAIL_BACKEND",
    default="django.core.mail.backends.smtp.EmailBackend"
)

# Slightly relaxed security for staging
SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=True, cast=bool)

# Logging for staging
LOGGING = {  # noqa: F405
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}
