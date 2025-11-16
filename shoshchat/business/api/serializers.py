"""Serializers for Business API."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from business.models import Business, TeamMember

User = get_user_model()


class BusinessSerializer(serializers.ModelSerializer):
    """Serializer for Business model."""

    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    owner_name = serializers.CharField(source="owner.username", read_only=True)
    team_member_count = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "slug",
            "industry",
            "description",
            "website",
            "phone",
            "email",
            "address",
            "owner_email",
            "owner_name",
            "team_member_count",
            "paid_until",
            "on_trial",
            "trial_ends",
            "widget_welcome_message",
            "widget_primary_color",
            "widget_position",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "slug", "owner_email", "owner_name", "created_at", "updated_at"]

    def get_team_member_count(self, obj):
        """Get count of active team members."""
        return obj.team_members.filter(is_active=True).count()


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember model."""

    user_email = serializers.EmailField(source="user.email", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)
    invited_by_email = serializers.EmailField(source="invited_by.email", read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "business",
            "business_name",
            "user",
            "user_email",
            "user_name",
            "role",
            "permissions",
            "invited_by",
            "invited_by_email",
            "is_active",
            "joined_at",
        ]
        read_only_fields = ["id", "business", "user", "invited_by", "joined_at"]


class InviteTeamMemberSerializer(serializers.Serializer):
    """Serializer for inviting a team member."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=TeamMember.ROLE_CHOICES, default=TeamMember.MEMBER)
    permissions = serializers.JSONField(required=False, default=dict)

    def validate_role(self, value):
        """Prevent inviting as owner."""
        if value == TeamMember.OWNER:
            raise serializers.ValidationError("Cannot invite someone as owner.")
        return value


class UpdateTeamMemberRoleSerializer(serializers.Serializer):
    """Serializer for updating team member role."""

    role = serializers.ChoiceField(choices=TeamMember.ROLE_CHOICES)

    def validate_role(self, value):
        """Prevent promoting to owner."""
        if value == TeamMember.OWNER:
            raise serializers.ValidationError("Cannot promote to owner.")
        return value
