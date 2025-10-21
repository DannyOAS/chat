"""Serializers for tenant provisioning."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from billing.models import Plan, Subscription
from tenancy.models import Domain, Tenant
from tenancy.services import create_tenant_with_subscription

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(write_only=True)
    plan_slug = serializers.SlugRelatedField(
        queryset=Plan.objects.all(), slug_field="slug", write_only=True, required=False
    )
    domain = serializers.CharField(write_only=True, required=False, allow_blank=True)
    accent = serializers.CharField(write_only=True, required=False)
    welcome_message = serializers.CharField(write_only=True, required=False)
    primary_color = serializers.CharField(write_only=True, required=False)
    plan = serializers.SerializerMethodField(read_only=True)
    widget_settings = serializers.SerializerMethodField(read_only=True)
    domains = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "schema_name",
            "industry",
            "owner_email",
            "plan_slug",
            "domain",
            "accent",
            "welcome_message",
            "primary_color",
            "plan",
            "widget_settings",
            "domains",
        ]

    def create(self, validated_data):
        owner_email = validated_data.pop("owner_email")
        plan = validated_data.pop("plan_slug", None)
        domain_value = validated_data.pop("domain", "")
        accent = validated_data.pop("accent", Tenant.widget_accent.field.default)
        welcome_message = validated_data.pop(
            "welcome_message", Tenant.widget_welcome_message.field.default
        )
        primary_color = validated_data.pop(
            "primary_color", Tenant.widget_primary_color.field.default
        )

        owner, _ = User.objects.get_or_create(
            email=owner_email,
            defaults={"username": owner_email},
        )
        plan_obj = None
        if plan:
            plan_obj = Plan.objects.filter(slug=plan).first()

        result = create_tenant_with_subscription(
            name=validated_data["name"],
            schema_name=validated_data["schema_name"],
            industry=validated_data["industry"],
            owner=owner,
            plan=plan_obj,
            domain_name=domain_value or None,
            accent=accent,
            welcome_message=welcome_message,
            primary_color=primary_color,
        )
        return result.tenant

    def get_plan(self, obj: Tenant):
        subscription = Subscription.objects.filter(tenant=obj, active=True).select_related("plan").first()
        if not subscription:
            return None
        return {
            "name": subscription.plan.name,
            "slug": subscription.plan.slug,
            "message_quota": subscription.plan.message_quota,
            "monthly_price": str(subscription.plan.monthly_price),
        }

    def get_widget_settings(self, obj: Tenant):
        return {
            "accent": obj.widget_accent,
            "welcome_message": obj.widget_welcome_message,
            "primary_color": obj.widget_primary_color,
        }

    def get_domains(self, obj: Tenant):
        return list(obj.domains.values("domain", "is_primary"))


class TenantSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "widget_accent",
            "widget_welcome_message",
            "widget_primary_color",
        ]


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ["domain", "is_primary"]
        extra_kwargs = {"is_primary": {"required": False}}


class TenantDetailSerializer(serializers.ModelSerializer):
    plan = serializers.SerializerMethodField()
    domains = DomainSerializer(many=True, read_only=True)

    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "schema_name",
            "industry",
            "widget_accent",
            "widget_welcome_message",
            "widget_primary_color",
            "paid_until",
            "on_trial",
            "plan",
            "domains",
        ]

    def get_plan(self, obj: Tenant):
        subscription = Subscription.objects.filter(tenant=obj, active=True).select_related("plan").first()
        if not subscription:
            return None
        plan = subscription.plan
        return {
            "name": plan.name,
            "slug": plan.slug,
            "monthly_price": str(plan.monthly_price),
            "message_quota": plan.message_quota,
            "current_period_start": subscription.current_period_start,
            "current_period_end": subscription.current_period_end,
        }
