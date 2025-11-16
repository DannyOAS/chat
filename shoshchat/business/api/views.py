"""Business API views."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, response, status
from rest_framework.views import APIView

from business.models import Business, TeamMember
from business.permissions import IsBusinessOwner, IsBusinessOwnerOrAdmin

from .serializers import (
    BusinessSerializer,
    InviteTeamMemberSerializer,
    TeamMemberSerializer,
    UpdateTeamMemberRoleSerializer,
)

User = get_user_model()


class BusinessDetailView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current user's business.

    Uses request.business set by BusinessMiddleware.
    """

    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Return the authenticated user's business."""
        if not self.request.business:
            from rest_framework.exceptions import NotFound

            raise NotFound("You don't have a business yet. Please create one first.")
        return self.request.business


class TeamMembersListView(generics.ListAPIView):
    """
    List all active team members of the current business.

    Requires: User must be authenticated and have a business.
    """

    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return active team members for the user's business."""
        if not self.request.business:
            return TeamMember.objects.none()

        return TeamMember.objects.filter(
            business=self.request.business, is_active=True
        ).select_related("user", "invited_by", "business")


class InviteTeamMemberView(APIView):
    """
    Invite a new team member to the business.

    Requires: User must be the business owner or admin.
    Permissions: manage_members
    """

    permission_classes = [permissions.IsAuthenticated, IsBusinessOwnerOrAdmin]

    def post(self, request):
        """Invite a user to join the business."""
        if not request.business:
            return response.Response(
                {"detail": "You don't have a business."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InviteTeamMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]
        perms = serializer.validated_data.get("permissions", {})

        # Check if user exists
        user = User.objects.filter(email=email).first()
        if not user:
            return response.Response(
                {"detail": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND
            )

        # Prevent owner from inviting themselves
        if user == request.business.owner:
            return response.Response(
                {"detail": "Owner is already part of the business."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already a member
        existing = TeamMember.objects.filter(business=request.business, user=user).first()
        if existing and existing.is_active:
            return response.Response(
                {"detail": "User is already a team member."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Reactivate if previously removed
        if existing and not existing.is_active:
            existing.is_active = True
            existing.role = role
            existing.permissions = perms
            existing.invited_by = request.user
            existing.save(update_fields=["is_active", "role", "permissions", "invited_by"])
            return response.Response(TeamMemberSerializer(existing).data)

        # Create new team member
        member = TeamMember.objects.create(
            business=request.business, user=user, role=role, permissions=perms, invited_by=request.user
        )

        return response.Response(TeamMemberSerializer(member).data, status=status.HTTP_201_CREATED)


class UpdateTeamMemberRoleView(APIView):
    """
    Update a team member's role.

    Requires: User must be the business owner or admin.
    """

    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]

    def patch(self, request, member_id):
        """Update team member role."""
        if not request.business:
            return response.Response(
                {"detail": "You don't have a business."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Get team member
        member = TeamMember.objects.filter(id=member_id, business=request.business).first()
        if not member:
            return response.Response({"detail": "Team member not found."}, status=status.HTTP_404_NOT_FOUND)

        # Prevent changing owner role (owner is not a team member)
        if member.user == request.business.owner:
            return response.Response(
                {"detail": "Cannot change owner's role."}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UpdateTeamMemberRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        member.role = serializer.validated_data["role"]
        member.save(update_fields=["role"])

        return response.Response(TeamMemberSerializer(member).data)


class RemoveTeamMemberView(APIView):
    """
    Remove a team member from the business.

    Requires: User must be the business owner or admin.
    """

    permission_classes = [permissions.IsAuthenticated, IsBusinessOwner]

    def delete(self, request, member_id):
        """Remove (deactivate) a team member."""
        if not request.business:
            return response.Response(
                {"detail": "You don't have a business."}, status=status.HTTP_400_BAD_REQUEST
            )

        member = TeamMember.objects.filter(id=member_id, business=request.business).first()
        if not member:
            return response.Response({"detail": "Team member not found."}, status=status.HTTP_404_NOT_FOUND)

        # Prevent removing owner
        if member.user == request.business.owner:
            return response.Response(
                {"detail": "Cannot remove the business owner."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Deactivate instead of deleting
        member.is_active = False
        member.save(update_fields=["is_active"])

        return response.Response({"detail": "Team member removed."}, status=status.HTTP_204_NO_CONTENT)
