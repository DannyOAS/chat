"""
GDPR API endpoints for data portability and erasure.
"""
from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.gdpr import GDPRConsentManager, GDPRDataEraser, GDPRDataExporter

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_user_data(request):
    """
    Export all user data (GDPR Right to Access).

    GET /api/v1/gdpr/export/

    Returns:
        JSON containing all user data
    """
    exporter = GDPRDataExporter(request.user)

    try:
        data = exporter.export_all_data()

        logger.info(f"User {request.user.id} requested data export")

        return Response({
            "success": True,
            "data": data,
            "message": "Your data has been exported successfully.",
        })

    except Exception as e:
        logger.error(f"Error exporting user data: {e}", exc_info=True)

        return Response({
            "success": False,
            "error": "Failed to export data. Please contact support.",
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def request_data_deletion(request):
    """
    Request account and data deletion (GDPR Right to Erasure).

    POST /api/v1/gdpr/delete-account/
    Body: {
        "confirm": true,
        "anonymize": false  // optional, default true
    }

    Returns:
        Confirmation of deletion request
    """
    # Require explicit confirmation
    if not request.data.get("confirm"):
        return Response({
            "success": False,
            "error": "Please confirm account deletion by setting 'confirm' to true.",
        }, status=status.HTTP_400_BAD_REQUEST)

    # Get anonymize preference (default to True for referential integrity)
    anonymize = request.data.get("anonymize", True)

    eraser = GDPRDataEraser(request.user)

    try:
        # Perform deletion/anonymization
        summary = eraser.erase_all_data(anonymize=anonymize)

        logger.warning(
            f"User {request.user.id} ({request.user.email}) "
            f"requested account deletion (anonymize={anonymize})"
        )

        return Response({
            "success": True,
            "message": "Your account and data have been deleted.",
            "summary": summary,
        })

    except Exception as e:
        logger.error(f"Error deleting user data: {e}", exc_info=True)

        return Response({
            "success": False,
            "error": "Failed to delete data. Please contact support.",
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def manage_consent(request):
    """
    Manage user consent preferences.

    GET /api/v1/gdpr/consent/
    Returns all consent statuses

    POST /api/v1/gdpr/consent/
    Body: {
        "purpose": "marketing",
        "granted": true
    }

    Returns:
        Updated consent preferences
    """
    if request.method == "GET":
        # Get all consents
        consents = GDPRConsentManager.get_all_consents(request.user)

        return Response({
            "success": True,
            "consents": consents,
            "purposes": GDPRConsentManager.CONSENT_PURPOSES,
        })

    elif request.method == "POST":
        # Update consent
        purpose = request.data.get("purpose")
        granted = request.data.get("granted")

        if not purpose or granted is None:
            return Response({
                "success": False,
                "error": "Both 'purpose' and 'granted' are required.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate purpose
        if purpose not in GDPRConsentManager.CONSENT_PURPOSES:
            return Response({
                "success": False,
                "error": f"Invalid purpose. Must be one of: {list(GDPRConsentManager.CONSENT_PURPOSES.keys())}",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Cannot revoke essential consent
        if purpose == "essential" and not granted:
            return Response({
                "success": False,
                "error": "Essential consent cannot be revoked.",
            }, status=status.HTTP_400_BAD_REQUEST)

        # Record consent
        GDPRConsentManager.record_consent(request.user, purpose, granted)

        # Return updated consents
        consents = GDPRConsentManager.get_all_consents(request.user)

        return Response({
            "success": True,
            "message": f"Consent for '{purpose}' has been {'granted' if granted else 'revoked'}.",
            "consents": consents,
        })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def privacy_dashboard(request):
    """
    Privacy dashboard showing all privacy-related information.

    GET /api/v1/gdpr/dashboard/

    Returns:
        Complete privacy information including:
        - Data categories collected
        - Consent status
        - Data retention policies
        - Third-party data sharing
    """
    # Get consents
    consents = GDPRConsentManager.get_all_consents(request.user)

    # Build privacy dashboard data
    dashboard_data = {
        "user_rights": {
            "right_to_access": {
                "description": "You can request a copy of all your personal data.",
                "action": "Use the /api/v1/gdpr/export/ endpoint",
            },
            "right_to_erasure": {
                "description": "You can request deletion of your account and all data.",
                "action": "Use the /api/v1/gdpr/delete-account/ endpoint",
            },
            "right_to_rectification": {
                "description": "You can update your personal information at any time.",
                "action": "Update your profile via /api/v1/accounts/profile/",
            },
            "right_to_data_portability": {
                "description": "You can download your data in machine-readable format.",
                "action": "Use the /api/v1/gdpr/export/ endpoint",
            },
        },
        "data_collected": {
            "personal_information": [
                "Username",
                "Email address",
                "Name",
                "Profile information",
            ],
            "usage_data": [
                "Chat messages",
                "Knowledge sources",
                "Login history",
                "Audit logs",
            ],
            "billing_data": [
                "Subscription information",
                "Payment method (via Stripe - we don't store card details)",
            ],
            "technical_data": [
                "IP addresses (for security)",
                "Browser and device information",
                "Cookies and similar technologies",
            ],
        },
        "consents": consents,
        "data_retention": {
            "account_data": "Retained while account is active",
            "chat_messages": "Retained for 2 years or until deletion request",
            "audit_logs": "Retained for 7 years (compliance requirement)",
            "backups": "Deleted backups are purged after 30 days",
        },
        "third_party_sharing": {
            "stripe": {
                "purpose": "Payment processing",
                "data_shared": ["Email", "Name", "Billing information"],
                "privacy_policy": "https://stripe.com/privacy",
            },
            "openai": {
                "purpose": "AI chat functionality",
                "data_shared": ["Chat messages", "Knowledge content"],
                "privacy_policy": "https://openai.com/privacy",
            },
            "sentry": {
                "purpose": "Error tracking and monitoring",
                "data_shared": ["Error logs (anonymized)"],
                "privacy_policy": "https://sentry.io/privacy",
            },
        },
        "contact": {
            "data_protection_officer": "privacy@shoshchat.ai",
            "support_email": "support@shoshchat.ai",
        },
    }

    return Response({
        "success": True,
        "dashboard": dashboard_data,
    })
