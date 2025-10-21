"""Settings for ShoshChat AI Django project."""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Final

from decouple import Csv, config

BASE_DIR: Final[Path] = Path(__file__).resolve().parent.parent

SECRET_KEY: Final[str] = config("DJANGO_SECRET_KEY", default="change-me")
DEBUG: Final[bool] = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS: list[str] = config(
    "DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv()
)

SHARED_APPS: Final[list[str]] = [
    "django_tenants",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "rest_framework.authtoken",
    "rest_framework_simplejwt.token_blacklist",
    "accounts",
    "djstripe",
    "tenancy",
    "knowledge",
]

TENANT_APPS: Final[list[str]] = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "chatbot",
    "billing",
    "compliance",
    "nlp",
]

INSTALLED_APPS: list[str] = list(dict.fromkeys(SHARED_APPS + TENANT_APPS))

TENANT_MODEL: Final[str] = "tenancy.Tenant"
TENANT_DOMAIN_MODEL: Final[str] = "tenancy.Domain"

MIDDLEWARE: list[str] = [
    "django_tenants.middleware.main.TenantMainMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "compliance.middleware.AuditMiddleware",
]

ROOT_URLCONF: Final[str] = "core.urls"
PUBLIC_SCHEMA_URLCONF: Final[str] = "core.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    }
]

DATABASES: dict[str, dict[str, str]] = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": config("POSTGRES_DB", default="shoshchat"),
        "USER": config("POSTGRES_USER", default="shoshchat"),
        "PASSWORD": config("POSTGRES_PASSWORD", default="shoshchat"),
        "HOST": config("POSTGRES_HOST", default="db"),
        "PORT": config("POSTGRES_PORT", default="5432"),
    }
}

DATABASE_ROUTERS: Final[list[str]] = ["django_tenants.routers.TenantSyncRouter"]

AUTH_PASSWORD_VALIDATORS: list[dict[str, str]] = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE: Final[str] = "en-us"
TIME_ZONE: Final[str] = "UTC"
USE_I18N: Final[bool] = True
USE_TZ: Final[bool] = True

STATIC_URL: Final[str] = "static/"
STATIC_ROOT: Final[Path] = BASE_DIR / "staticfiles"
MEDIA_URL: Final[str] = "media/"
MEDIA_ROOT: Final[Path] = BASE_DIR / "media"

DEFAULT_AUTO_FIELD: Final[str] = "django.db.models.BigAutoField"

REST_FRAMEWORK: Final[dict[str, object]] = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "user": config("DRF_THROTTLE_USER", default="1000/day"),
        "anon": config("DRF_THROTTLE_ANON", default="100/day"),
        "auth_login": config("DRF_THROTTLE_AUTH_LOGIN", default="10/min"),
        "auth_register": config("DRF_THROTTLE_AUTH_REGISTER", default="5/hour"),
        "auth_reset": config("DRF_THROTTLE_AUTH_RESET", default="5/hour"),
        "auth_verify": config("DRF_THROTTLE_AUTH_VERIFY", default="5/hour"),
        "chat": config("DRF_THROTTLE_CHAT", default="120/min"),
    },
}

DJSTRIPE_FOREIGN_KEY_TO_FIELD: Final[str] = "id"
DJSTRIPE_WEBHOOK_SECRET: Final[str | None] = config(
    "STRIPE_WEBHOOK_SECRET", default=None
)
STRIPE_LIVE_MODE: Final[bool] = config("STRIPE_LIVE_MODE", default=False, cast=bool)
STRIPE_TEST_PUBLIC_KEY: Final[str] = config("STRIPE_TEST_PUBLIC_KEY", default="")
STRIPE_TEST_SECRET_KEY: Final[str] = config("STRIPE_TEST_SECRET_KEY", default="")
STRIPE_LIVE_PUBLIC_KEY: Final[str] = config("STRIPE_LIVE_PUBLIC_KEY", default="")
STRIPE_LIVE_SECRET_KEY: Final[str] = config("STRIPE_LIVE_SECRET_KEY", default="")
DJSTRIPE_USE_NATIVE_JSONFIELD: Final[bool] = True

REDIS_URL: Final[str] = config("REDIS_URL", default="redis://redis:6379/0")
CELERY_BROKER_URL: Final[str] = REDIS_URL
CELERY_RESULT_BACKEND: Final[str] = REDIS_URL

AI_PROVIDER: Final[str] = config("AI_PROVIDER", default="gradient")
DO_GRADIENT_API_KEY: Final[str] = config("DO_GRADIENT_API_KEY", default="")

SIMPLE_JWT: Final[dict[str, object]] = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}

AUDIT_EVENT_TYPES: Final[tuple[str, ...]] = (
    "message.sent",
    "message.received",
    "billing.quota",
)

SECURE_PROXY_SSL_HEADER: Final[tuple[str, str]] = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT: Final[bool] = config("DJANGO_SECURE_SSL_REDIRECT", default=False, cast=bool)
SESSION_COOKIE_SECURE: Final[bool] = config("DJANGO_SESSION_COOKIE_SECURE", default=True, cast=bool)
CSRF_COOKIE_SECURE: Final[bool] = config("DJANGO_CSRF_COOKIE_SECURE", default=True, cast=bool)
SESSION_COOKIE_SAMESITE: Final[str] = config("DJANGO_SESSION_COOKIE_SAMESITE", default="Lax")
SECURE_HSTS_SECONDS: Final[int] = config("DJANGO_SECURE_HSTS_SECONDS", default=0, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS: Final[bool] = config(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False, cast=bool
)
SECURE_HSTS_PRELOAD: Final[bool] = config("DJANGO_SECURE_HSTS_PRELOAD", default=False, cast=bool)
SECURE_REFERRER_POLICY: Final[str] = config("DJANGO_SECURE_REFERRER_POLICY", default="strict-origin")
CSRF_TRUSTED_ORIGINS: list[str] = config(
    "DJANGO_CSRF_TRUSTED_ORIGINS", default="", cast=Csv()
)
X_FRAME_OPTIONS: Final[str] = "DENY"

EMAIL_BACKEND: Final[str] = config(
    "DJANGO_EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL: Final[str] = config("DJANGO_DEFAULT_FROM_EMAIL", default="support@shoshchat.ai")
