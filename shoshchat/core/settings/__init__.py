"""
Settings module initialization.

Automatically loads the appropriate settings module based on DJANGO_SETTINGS_MODULE
environment variable. Defaults to development settings.
"""
from __future__ import annotations

import os

# Determine which settings to use
ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    from .production import *  # noqa: F401, F403
elif ENVIRONMENT == "staging":
    from .staging import *  # noqa: F401, F403
else:
    # Default to development
    from .development import *  # noqa: F401, F403
