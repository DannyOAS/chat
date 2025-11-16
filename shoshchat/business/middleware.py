"""
Middleware for business context in single-domain architecture.

Replaces django-tenants middleware with simpler authentication-based approach.
"""
from __future__ import annotations

from typing import Callable

from django.http import HttpRequest, HttpResponse


class BusinessMiddleware:
    """
    Adds business context to requests based on authenticated user.

    Much simpler than django-tenants:
    - No subdomain parsing
    - No schema switching
    - Just adds request.business for authenticated users
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Add business to request context."""
        # Add business to request if user is authenticated
        if request.user and request.user.is_authenticated:
            try:
                # Get user's business (one-to-one relationship)
                request.business = request.user.business
            except AttributeError:
                # User doesn't have a business yet (e.g., just registered)
                request.business = None
        else:
            request.business = None

        # Process request
        response = self.get_response(request)

        return response


class BusinessAccessMiddleware:
    """
    Optional middleware to check team member access.

    If you want to support team members accessing other businesses.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Check if user has access to requested business."""
        # For API endpoints that specify a business_id
        business_id = request.GET.get("business_id") or request.POST.get("business_id")

        if business_id and request.user.is_authenticated:
            from business.models import Business, TeamMember

            # Check if user owns this business or is a team member
            try:
                # First check if user owns the business
                business = Business.objects.get(id=business_id, owner=request.user)
                request.business = business
                request.business_role = "owner"
            except Business.DoesNotExist:
                # Check if user is a team member
                try:
                    membership = TeamMember.objects.get(
                        business_id=business_id,
                        user=request.user,
                        is_active=True,
                    )
                    request.business = membership.business
                    request.business_role = membership.role
                except TeamMember.DoesNotExist:
                    # User doesn't have access
                    request.business = None
                    request.business_role = None

        # Process request
        response = self.get_response(request)

        return response
