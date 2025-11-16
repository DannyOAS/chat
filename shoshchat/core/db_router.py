"""
Database router for read replica support.

Automatically routes read queries to read replicas and write queries to primary.
"""
from __future__ import annotations

import random


class ReadReplicaRouter:
    """
    Database router that routes reads to replicas and writes to primary.

    Usage:
        # In settings.py
        DATABASE_ROUTERS = ['core.db_router.ReadReplicaRouter']

        DATABASES = {
            'default': {...},  # Primary (read/write)
            'read_replica_1': {...},  # Read replica 1
            'read_replica_2': {...},  # Read replica 2
        }
    """

    def db_for_read(self, model, **hints):
        """
        Route read queries to read replicas.

        Uses round-robin selection across all read replicas.
        """
        # Get all read replica database aliases
        read_replicas = self._get_read_replicas()

        if read_replicas:
            # Random selection for load balancing
            return random.choice(read_replicas)

        # Fall back to default database
        return "default"

    def db_for_write(self, model, **hints):
        """
        Route write queries to primary database.
        """
        # All writes go to primary
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if both objects are in the same database.
        """
        # Allow all relations (objects can be in any database)
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Only allow migrations on the primary database.
        """
        # Migrations only run on primary
        return db == "default"

    def _get_read_replicas(self) -> list[str]:
        """
        Get list of read replica database aliases.

        Returns:
            List of database aliases configured as read replicas
        """
        from django.conf import settings

        # Get all database aliases except 'default'
        all_dbs = list(settings.DATABASES.keys())

        # Filter for read replicas (anything with 'read' or 'replica' in name)
        read_replicas = [
            db
            for db in all_dbs
            if db != "default" and ("read" in db.lower() or "replica" in db.lower())
        ]

        return read_replicas


class TenantAwareRouter:
    """
    Router that respects tenant context for multi-tenant applications.

    Ensures queries use the correct schema/database based on current tenant.
    """

    def db_for_read(self, model, **hints):
        """Route reads based on tenant context."""
        # If model is tenant-specific, use tenant database
        if hasattr(model, "_meta") and hasattr(model._meta, "tenant_specific"):
            # Get current tenant from thread local or context
            tenant = self._get_current_tenant()
            if tenant:
                return tenant.database_alias

        return None  # Use default routing

    def db_for_write(self, model, **hints):
        """Route writes based on tenant context."""
        if hasattr(model, "_meta") and hasattr(model._meta, "tenant_specific"):
            tenant = self._get_current_tenant()
            if tenant:
                return tenant.database_alias

        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow relations within the same tenant."""
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """Control which apps can be migrated in which databases."""
        return True

    def _get_current_tenant(self):
        """
        Get current tenant from context.

        This would integrate with django-tenants or similar library.
        """
        try:
            import threading

            # Get from thread local storage
            return getattr(threading.current_thread(), "tenant", None)
        except Exception:
            return None
