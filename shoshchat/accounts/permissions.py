"""Permission classes and decorators for RBAC."""
from __future__ import annotations

from functools import wraps
from typing import TYPE_CHECKING

from django.core.exceptions import PermissionDenied
from rest_framework import permissions

if TYPE_CHECKING:
    from django.http import HttpRequest

    from tenancy.models import Tenant


def get_user_tenant_membership(user, tenant):
    """Get the user's membership for a specific tenant."""
    if not user or not user.is_authenticated:
        return None

    from accounts.models import TenantMembership

    return TenantMembership.objects.filter(user=user, tenant=tenant, is_active=True).first()


def user_has_tenant_permission(user, tenant, permission: str) -> bool:
    """Check if a user has a specific permission for a tenant."""
    membership = get_user_tenant_membership(user, tenant)
    if not membership:
        return False
    return membership.has_permission(permission)


def require_tenant_permission(permission: str):
    """
    Decorator to check if the user has the specified permission for the tenant.

    Usage:
        @require_tenant_permission('manage_chatbots')
        def my_view(request, tenant):
            ...
    """

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            tenant = kwargs.get("tenant") or getattr(request, "tenant", None)
            if not tenant:
                raise PermissionDenied("Tenant not found in request.")

            if not user_has_tenant_permission(request.user, tenant, permission):
                raise PermissionDenied(f"You do not have permission to {permission}.")

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


class TenantPermission(permissions.BasePermission):
    """
    DRF permission class that checks tenant-level permissions.

    Usage:
        class MyView(APIView):
            permission_classes = [TenantPermission]
            required_permission = 'manage_chatbots'
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Get required permission from view
        required_permission = getattr(view, "required_permission", None)
        if not required_permission:
            return True  # No specific permission required

        # Get tenant from request (set by middleware or view)
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        return user_has_tenant_permission(request.user, tenant, required_permission)


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permission class that only allows owners or admins."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        membership = get_user_tenant_membership(request.user, tenant)
        if not membership:
            return False

        from accounts.models import Role

        return membership.role in [Role.OWNER, Role.ADMIN]


class IsOwnerOnly(permissions.BasePermission):
    """Permission class that only allows tenant owners."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        tenant = getattr(request, "tenant", None)
        if not tenant:
            return False

        membership = get_user_tenant_membership(request.user, tenant)
        if not membership:
            return False

        from accounts.models import Role

        return membership.role == Role.OWNER
