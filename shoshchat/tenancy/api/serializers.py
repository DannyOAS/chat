"""Serializers for tenant provisioning."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from tenancy.models import Tenant

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(write_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "schema_name",
            "industry",
            "owner_email",
        ]

    def create(self, validated_data):
        owner_email = validated_data.pop("owner_email")
        owner, _ = User.objects.get_or_create(
            email=owner_email,
            defaults={"username": owner_email},
        )
        validated_data["schema_name"] = validated_data["schema_name"].replace(" ", "-").lower()
        tenant = Tenant.objects.create(owner=owner, **validated_data)
        return tenant
