"""Simple health check endpoints."""
from __future__ import annotations

from django.http import JsonResponse


def health(_: object) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def ready(_: object) -> JsonResponse:
    return JsonResponse({"status": "ready"})
