"""Permission classes for Business access control."""
from __future__ import annotations

from rest_framework import permissions

from business.models import TeamMember


class IsBusinessOwner(permissions.BasePermission):
    """
    Permission that checks if user is the owner of the business.

    Requires request.business to be set by BusinessMiddleware.
    """

    def has_permission(self, request, view):
        """Check if user owns the business."""
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.business:
            return False

        return request.business.owner == request.user


class IsBusinessOwnerOrAdmin(permissions.BasePermission):
    """
    Permission that checks if user is the owner or an admin of the business.

    Requires request.business to be set by BusinessMiddleware.
    """

    def has_permission(self, request, view):
        """Check if user is owner or admin."""
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.business:
            return False

        # Check if owner
        if request.business.owner == request.user:
            return True

        # Check if admin team member
        team_member = TeamMember.objects.filter(
            business=request.business, user=request.user, is_active=True
        ).first()

        if team_member and team_member.role == TeamMember.ADMIN:
            return True

        return False


class IsBusinessMember(permissions.BasePermission):
    """
    Permission that checks if user is a member of the business (owner, admin, manager, or member).

    Requires request.business to be set by BusinessMiddleware.
    """

    def has_permission(self, request, view):
        """Check if user is any member of the business."""
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.business:
            return False

        # Check if owner
        if request.business.owner == request.user:
            return True

        # Check if active team member
        return TeamMember.objects.filter(
            business=request.business, user=request.user, is_active=True
        ).exists()


class HasBusinessPermission(permissions.BasePermission):
    """
    Permission that checks if user has a specific business permission.

    Usage: Set required_permission attribute on the view.

    Example:
        class MyView(APIView):
            permission_classes = [HasBusinessPermission]
            required_permission = "manage_knowledge"
    """

    def has_permission(self, request, view):
        """Check if user has the required permission."""
        if not request.user or not request.user.is_authenticated:
            return False

        if not request.business:
            return False

        # Get required permission from view
        required_perm = getattr(view, "required_permission", None)
        if not required_perm:
            return False

        # Owner has all permissions
        if request.business.owner == request.user:
            return True

        # Check team member permissions
        team_member = TeamMember.objects.filter(
            business=request.business, user=request.user, is_active=True
        ).first()

        if not team_member:
            return False

        # Admin has all permissions
        if team_member.role == TeamMember.ADMIN:
            return True

        # Check custom permissions JSON field
        member_perms = team_member.permissions or {}
        return member_perms.get(required_perm, False)
