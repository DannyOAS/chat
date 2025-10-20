"""Middleware for audit logging and PII redaction."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Callable

from django.http import HttpRequest, HttpResponse

logger = logging.getLogger(__name__)


class AuditMiddleware:
    """Capture API interactions for compliance with PHIPA/PIPEDA."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if request.path.startswith("/api/"):
            payload = {
                "path": request.path,
                "method": request.method,
                "status": response.status_code,
                "tenant": getattr(getattr(request, "tenant", None), "schema_name", None),
                "user_hash": hashlib.sha256(str(request.user.pk).encode()).hexdigest()
                if request.user.is_authenticated
                else None,
            }
            logger.info("audit.middleware", extra={"payload": json.dumps(payload)})
        return response
