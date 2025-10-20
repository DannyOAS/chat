"""Database routers for tenant-aware operations."""
from __future__ import annotations

from django_tenants.routers import TenantSyncRouter

__all__ = ["TenantSyncRouter"]
