"""Authentication and user endpoints."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, response, status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import (
    EmailVerificationConfirmSerializer,
    EmailVerificationRequestSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterOnboardSerializer,
    RegisterSerializer,
    ShoshTokenObtainPairSerializer,
    UserSerializer,
    send_reset_email,
    send_verification_email,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user and issue validation errors when necessary."""

    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"


class ProfileView(generics.RetrieveAPIView):
    """Return details about the current authenticated user."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ShoshTokenObtainPairView(TokenObtainPairView):
    """Return a JWT pair along with serialized user data."""

    serializer_class = ShoshTokenObtainPairSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"


class RegisterOnboardView(generics.CreateAPIView):
    """Register a user and provision their tenant in one request."""

    serializer_class = RegisterOnboardSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_register"

    def perform_create(self, serializer):
        user = serializer.save()
        if user.email:
            send_verification_email(user, self.request)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_reset"

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user:
            send_reset_email(user, request)
        return response.Response({"detail": "If the email exists, a reset link was sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_reset"

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"detail": "Password updated."})


class EmailVerificationRequestView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_verify"

    def post(self, request):
        serializer = EmailVerificationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if user:
            send_verification_email(user, request)
        return response.Response({"detail": "If the email exists, verification instructions were sent."})


class EmailVerificationConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_verify"

    def post(self, request):
        serializer = EmailVerificationConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response({"detail": "Email verified."}, status=status.HTTP_200_OK)


# Two-Factor Authentication Views


class TwoFactorSetupView(APIView):
    """Initialize 2FA setup and return QR code data."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from accounts.two_factor import generate_qr_code, setup_two_factor
        import base64

        setup_data = setup_two_factor(request.user)

        # Generate QR code image
        qr_bytes = generate_qr_code(setup_data["qr_uri"])
        qr_base64 = base64.b64encode(qr_bytes).decode()

        return response.Response(
            {
                "secret": setup_data["secret"],
                "qr_code": f"data:image/png;base64,{qr_base64}",
                "backup_codes": setup_data["backup_codes"],
            }
        )


class TwoFactorEnableView(APIView):
    """Enable 2FA after verifying setup token."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from accounts.api.serializers import TwoFactorEnableSerializer
        from accounts.two_factor import enable_two_factor

        serializer = TwoFactorEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if enable_two_factor(request.user, serializer.validated_data["token"]):
            return response.Response({"detail": "Two-factor authentication enabled."})
        else:
            return response.Response(
                {"detail": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST
            )


class TwoFactorDisableView(APIView):
    """Disable 2FA after password verification."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from accounts.api.serializers import TwoFactorDisableSerializer
        from accounts.two_factor import disable_two_factor

        serializer = TwoFactorDisableSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        disable_two_factor(request.user)
        return response.Response({"detail": "Two-factor authentication disabled."})


class TwoFactorStatusView(APIView):
    """Check 2FA status for the current user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        return response.Response(
            {
                "enabled": profile.two_factor_enabled,
                "backup_codes_remaining": len(profile.backup_codes) if profile.two_factor_enabled else 0,
            }
        )


# RBAC Views


class TenantMembersView(generics.ListAPIView):
    """List all members of a tenant."""

    from accounts.api.serializers import TenantMembershipSerializer
    from accounts.permissions import TenantPermission

    serializer_class = TenantMembershipSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    required_permission = "manage_members"

    def get_queryset(self):
        from accounts.models import TenantMembership

        tenant = self.request.tenant  # Set by middleware
        return TenantMembership.objects.filter(tenant=tenant, is_active=True).select_related("user")


class InviteMemberView(APIView):
    """Invite a new member to the tenant."""

    from accounts.permissions import TenantPermission

    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    required_permission = "manage_members"

    def post(self, request):
        from accounts.api.serializers import InviteMemberSerializer
        from accounts.models import TenantMembership

        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        role = serializer.validated_data["role"]
        tenant = request.tenant

        # Check if user exists
        user = User.objects.filter(email=email).first()
        if not user:
            return response.Response(
                {"detail": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND
            )

        # Check if already a member
        existing = TenantMembership.objects.filter(tenant=tenant, user=user).first()
        if existing:
            return response.Response(
                {"detail": "User is already a member of this tenant."}, status=status.HTTP_400_BAD_REQUEST
            )

        # Create membership
        membership = TenantMembership.objects.create(
            tenant=tenant, user=user, role=role, invited_by=request.user
        )

        return response.Response(
            TenantMembershipSerializer(membership).data, status=status.HTTP_201_CREATED
        )


class UpdateMemberRoleView(APIView):
    """Update a member's role."""

    from accounts.permissions import IsOwnerOrAdmin

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def patch(self, request, membership_id):
        from accounts.models import Role, TenantMembership

        tenant = request.tenant
        membership = TenantMembership.objects.filter(id=membership_id, tenant=tenant).first()

        if not membership:
            return response.Response(
                {"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Prevent changing owner role
        if membership.role == Role.OWNER:
            return response.Response(
                {"detail": "Cannot change owner's role."}, status=status.HTTP_400_BAD_REQUEST
            )

        new_role = request.data.get("role")
        if not new_role or new_role not in dict(Role.choices):
            return response.Response({"detail": "Invalid role."}, status=status.HTTP_400_BAD_REQUEST)

        # Prevent promoting to owner
        if new_role == Role.OWNER:
            return response.Response(
                {"detail": "Cannot promote to owner."}, status=status.HTTP_400_BAD_REQUEST
            )

        membership.role = new_role
        membership.save(update_fields=["role"])

        return response.Response(TenantMembershipSerializer(membership).data)


class RemoveMemberView(APIView):
    """Remove a member from the tenant."""

    from accounts.permissions import IsOwnerOrAdmin

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def delete(self, request, membership_id):
        from accounts.models import Role, TenantMembership

        tenant = request.tenant
        membership = TenantMembership.objects.filter(id=membership_id, tenant=tenant).first()

        if not membership:
            return response.Response(
                {"detail": "Membership not found."}, status=status.HTTP_404_NOT_FOUND
            )

        # Prevent removing owner
        if membership.role == Role.OWNER:
            return response.Response(
                {"detail": "Cannot remove owner."}, status=status.HTTP_400_BAD_REQUEST
            )

        membership.is_active = False
        membership.save(update_fields=["is_active"])

        return response.Response({"detail": "Member removed."}, status=status.HTTP_204_NO_CONTENT)


class PublicPlansView(APIView):
    """Public billing plans for registration - no tenant context needed"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, *args, **kwargs):
        plans = [
            {
                "slug": "starter", 
                "name": "Starter Plan", 
                "monthly_price": "19.99", 
                "message_quota": 1000, 
                "features": ["Basic AI", "Email Support"]
            },
            {
                "slug": "pro", 
                "name": "Professional Plan", 
                "monthly_price": "49.99", 
                "message_quota": 5000, 
                "features": ["Advanced AI", "Priority Support"]
            },
            {
                "slug": "enterprise", 
                "name": "Enterprise Plan", 
                "monthly_price": "99.99", 
                "message_quota": 15000, 
                "features": ["Premium AI", "24/7 Support"]
            }
        ]
        return response.Response(plans)

