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
