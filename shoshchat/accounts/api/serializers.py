"""Serializers for authentication endpoints."""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from billing.models import Plan
from tenancy.models import Tenant
from tenancy.services import create_tenant_with_subscription

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    email_verified = serializers.BooleanField(source="profile.email_verified", read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email", "email_verified"]
        read_only_fields = ["id", "username", "email"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm", "first_name", "last_name"]

    def validate(self, attrs):
        password = attrs.get("password")
        password_confirm = attrs.pop("password_confirm", None)
        if password != password_confirm:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        validate_password(password)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save(update_fields=["password"])
        return user


class ShoshTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Return JWT pair alongside serialized user data."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.get_username()
        token["email"] = user.email
        token["tenants"] = list(user.tenants.values_list("schema_name", flat=True))
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class RegisterOnboardSerializer(RegisterSerializer):
    company_name = serializers.CharField(max_length=255)
    industry = serializers.ChoiceField(choices=Tenant.INDUSTRY_CHOICES)
    plan = serializers.SlugField(required=False)
    domain = serializers.CharField(required=False, allow_blank=True)
    accent = serializers.CharField(required=False, allow_blank=True)
    welcome_message = serializers.CharField(required=False, allow_blank=True)
    primary_color = serializers.CharField(required=False, allow_blank=True)

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields + [
            "company_name",
            "industry",
            "plan",
            "domain",
            "accent",
            "welcome_message",
            "primary_color",
        ]

    def create(self, validated_data):
        plan_slug = validated_data.pop("plan", "")
        company_name = validated_data.pop("company_name")
        industry = validated_data.pop("industry")
        domain = validated_data.pop("domain", "")
        accent = validated_data.pop("accent", "retail")
        welcome_message = validated_data.pop("welcome_message", "")
        primary_color = validated_data.pop("primary_color", "")

        user = super().create(validated_data)
        plan = Plan.objects.filter(slug=plan_slug).first() if plan_slug else None
        create_tenant_with_subscription(
            name=company_name,
            schema_name=company_name,
            industry=industry,
            owner=user,
            plan=plan,
            domain_name=domain or None,
            accent=accent or "retail",
            welcome_message=welcome_message or None,
            primary_color=primary_color or None,
        )
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid user."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        password = self.validated_data["new_password"]
        validate_password(password, user=user)
        user.set_password(password)
        user.save(update_fields=["password"])
        return user


class EmailVerificationRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class EmailVerificationConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):
        try:
            user_id = force_str(urlsafe_base64_decode(attrs["uid"]))
            user = User.objects.get(pk=user_id)
        except (ValueError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid user."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        if hasattr(user, "profile"):
            user.profile.email_verified = True
            user.profile.save(update_fields=["email_verified"])
        return user


def send_reset_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_link = f"{request.build_absolute_uri('/reset-password')}?uid={uid}&token={token}"
    if user.email:
        send_mail(
            subject="Reset your ShoshChat password",
            message=f"Use this link to reset your password: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


def send_verification_email(user, request):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    verify_link = f"{request.build_absolute_uri('/verify-email')}?uid={uid}&token={token}"
    if user.email:
        send_mail(
            subject="Verify your ShoshChat email",
            message=f"Confirm your email by visiting: {verify_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )


# Two-Factor Authentication Serializers


class TwoFactorSetupSerializer(serializers.Serializer):
    """Serializer for initiating 2FA setup."""

    pass  # No input needed, just triggers setup


class TwoFactorEnableSerializer(serializers.Serializer):
    """Serializer for enabling 2FA after setup."""

    token = serializers.CharField(min_length=6, max_length=6, help_text="6-digit TOTP code")


class TwoFactorDisableSerializer(serializers.Serializer):
    """Serializer for disabling 2FA."""

    password = serializers.CharField(write_only=True, help_text="User password for verification")

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Invalid password.")
        return value


class TwoFactorVerifySerializer(serializers.Serializer):
    """Serializer for verifying 2FA during login."""

    token = serializers.CharField(
        min_length=6, max_length=16, help_text="6-digit TOTP code or backup code"
    )


# RBAC Serializers


class TenantMembershipSerializer(serializers.Serializer):
    """Serializer for tenant membership."""

    from accounts.models import Role

    id = serializers.IntegerField(read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.ChoiceField(choices=Role.choices)
    joined_at = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)


class InviteMemberSerializer(serializers.Serializer):
    """Serializer for inviting a member to a tenant."""

    from accounts.models import Role

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Role.choices, default=Role.MEMBER)

    def validate_role(self, value):
        # Prevent creating owners through invite
        from accounts.models import Role

        if value == Role.OWNER:
            raise serializers.ValidationError("Cannot invite a user as owner.")
        return value
