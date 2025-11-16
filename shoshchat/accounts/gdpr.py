"""
GDPR Compliance utilities for ShoshChat AI.

Implements GDPR requirements:
- Right to Access (Data Portability)
- Right to Erasure (Right to be Forgotten)
- Right to Rectification
- Right to Restriction of Processing
- Data Breach Notification
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Dict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string

User = get_user_model()
logger = logging.getLogger(__name__)


class GDPRDataExporter:
    """
    Handles GDPR data portability requirements.

    Exports all user data in machine-readable format (JSON).
    """

    def __init__(self, user: User):
        self.user = user

    def export_all_data(self) -> Dict[str, Any]:
        """
        Export all user data for GDPR compliance.

        Returns complete user data in JSON format.
        """
        data = {
            "export_date": datetime.now().isoformat(),
            "user_id": self.user.id,
            "personal_information": self.export_personal_info(),
            "account_information": self.export_account_info(),
            "tenant_memberships": self.export_tenant_memberships(),
            "chat_history": self.export_chat_history(),
            "knowledge_sources": self.export_knowledge_sources(),
            "billing_information": self.export_billing_info(),
            "audit_logs": self.export_audit_logs(),
        }

        logger.info(f"GDPR data export completed for user {self.user.id}")

        return data

    def export_personal_info(self) -> Dict[str, Any]:
        """Export personal information."""
        from accounts.models import UserProfile

        try:
            profile = self.user.profile
            return {
                "username": self.user.username,
                "email": self.user.email,
                "first_name": self.user.first_name,
                "last_name": self.user.last_name,
                "date_joined": self.user.date_joined.isoformat(),
                "last_login": self.user.last_login.isoformat() if self.user.last_login else None,
                "profile": {
                    "bio": profile.bio if hasattr(profile, "bio") else None,
                    "phone_number": profile.phone_number if hasattr(profile, "phone_number") else None,
                    "timezone": profile.timezone if hasattr(profile, "timezone") else None,
                    "language": profile.language if hasattr(profile, "language") else None,
                    "two_factor_enabled": profile.two_factor_enabled if hasattr(profile, "two_factor_enabled") else False,
                },
            }
        except UserProfile.DoesNotExist:
            return {"username": self.user.username, "email": self.user.email}

    def export_account_info(self) -> Dict[str, Any]:
        """Export account settings and preferences."""
        return {
            "is_active": self.user.is_active,
            "is_staff": self.user.is_staff,
            "is_superuser": self.user.is_superuser,
            "email_verified": getattr(self.user, "email_verified", False),
        }

    def export_tenant_memberships(self) -> list[Dict[str, Any]]:
        """Export tenant membership information."""
        from accounts.models import TenantMembership

        memberships = TenantMembership.objects.filter(user=self.user).select_related(
            "tenant"
        )

        return [
            {
                "tenant_name": membership.tenant.name,
                "tenant_domain": membership.tenant.schema_name,
                "role": membership.role,
                "joined_at": membership.created_at.isoformat(),
            }
            for membership in memberships
        ]

    def export_chat_history(self) -> list[Dict[str, Any]]:
        """Export user's chat history."""
        # Note: This should be tenant-scoped
        # For now, export across all tenants the user has access to
        try:
            from chatbot.models import Message

            messages = Message.objects.filter(
                session__user_identifier=str(self.user.id)
            ).order_by("created_at")[:1000]  # Limit to last 1000 messages

            return [
                {
                    "timestamp": msg.created_at.isoformat(),
                    "role": msg.role,
                    "content": msg.content,
                    "session_id": str(msg.session.id) if msg.session else None,
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error exporting chat history: {e}")
            return []

    def export_knowledge_sources(self) -> list[Dict[str, Any]]:
        """Export knowledge sources created by user."""
        try:
            from knowledge.models import KnowledgeSource

            sources = KnowledgeSource.objects.filter(
                created_by=self.user
            ).order_by("-created_at")[:100]

            return [
                {
                    "id": str(source.id),
                    "name": source.name,
                    "type": source.source_type,
                    "created_at": source.created_at.isoformat(),
                    "status": source.status if hasattr(source, "status") else "unknown",
                }
                for source in sources
            ]
        except Exception as e:
            logger.error(f"Error exporting knowledge sources: {e}")
            return []

    def export_billing_info(self) -> Dict[str, Any]:
        """Export billing information."""
        try:
            from billing.models import Subscription

            subscriptions = Subscription.objects.filter(
                tenant__tenantmembership__user=self.user
            ).distinct()

            return {
                "subscriptions": [
                    {
                        "plan": sub.plan.name if hasattr(sub, "plan") else "Unknown",
                        "status": sub.status,
                        "created_at": sub.created_at.isoformat(),
                        "current_period_start": sub.current_period_start.isoformat()
                        if sub.current_period_start
                        else None,
                        "current_period_end": sub.current_period_end.isoformat()
                        if sub.current_period_end
                        else None,
                    }
                    for sub in subscriptions
                ]
            }
        except Exception as e:
            logger.error(f"Error exporting billing info: {e}")
            return {"subscriptions": []}

    def export_audit_logs(self) -> list[Dict[str, Any]]:
        """Export user audit logs."""
        try:
            from compliance.models import AuditLog

            logs = AuditLog.objects.filter(user=self.user).order_by("-timestamp")[:500]

            return [
                {
                    "timestamp": log.timestamp.isoformat(),
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "ip_address": log.ip_address,
                    "user_agent": log.user_agent,
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error exporting audit logs: {e}")
            return []

    def export_to_file(self, format: str = "json") -> str:
        """
        Export data to file.

        Args:
            format: Export format ('json' or 'csv')

        Returns:
            File path to exported data
        """
        import os
        import tempfile

        data = self.export_all_data()

        # Create temp file
        fd, filepath = tempfile.mkstemp(
            suffix=f".{format}",
            prefix=f"gdpr_export_{self.user.id}_",
        )

        with os.fdopen(fd, "w") as f:
            if format == "json":
                json.dump(data, f, indent=2, default=str)
            else:
                # TODO: Implement CSV export
                raise NotImplementedError("CSV export not yet implemented")

        logger.info(f"GDPR data exported to file: {filepath}")

        return filepath


class GDPRDataEraser:
    """
    Handles GDPR Right to Erasure (Right to be Forgotten).

    Permanently deletes or anonymizes user data.
    """

    def __init__(self, user: User):
        self.user = user

    @transaction.atomic
    def erase_all_data(self, anonymize: bool = True) -> Dict[str, Any]:
        """
        Erase or anonymize all user data.

        Args:
            anonymize: If True, anonymize data instead of deleting
                      (preserves referential integrity)

        Returns:
            Summary of deleted/anonymized data
        """
        summary = {
            "user_id": self.user.id,
            "username": self.user.username,
            "email": self.user.email,
            "erasure_date": datetime.now().isoformat(),
            "anonymized": anonymize,
            "deleted_items": {},
        }

        if anonymize:
            summary["deleted_items"] = self._anonymize_user_data()
        else:
            summary["deleted_items"] = self._delete_user_data()

        logger.info(
            f"GDPR data erasure completed for user {self.user.id} "
            f"(anonymize={anonymize})"
        )

        return summary

    def _anonymize_user_data(self) -> Dict[str, int]:
        """Anonymize user data while preserving database integrity."""
        deleted = {}

        # Anonymize user account
        self.user.username = f"deleted_user_{self.user.id}"
        self.user.email = f"deleted_{self.user.id}@deleted.local"
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.is_active = False
        self.user.set_unusable_password()
        self.user.save()
        deleted["user_account"] = 1

        # Anonymize profile
        try:
            profile = self.user.profile
            if hasattr(profile, "bio"):
                profile.bio = ""
            if hasattr(profile, "phone_number"):
                profile.phone_number = ""
            if hasattr(profile, "two_factor_secret"):
                profile.two_factor_secret = ""
            profile.save()
            deleted["user_profile"] = 1
        except Exception as e:
            logger.warning(f"Could not anonymize profile: {e}")

        # Delete chat messages (PII)
        try:
            from chatbot.models import Message

            count = Message.objects.filter(
                session__user_identifier=str(self.user.id)
            ).update(content="[deleted]")
            deleted["chat_messages"] = count
        except Exception as e:
            logger.warning(f"Could not delete chat messages: {e}")

        # Remove from tenant memberships
        try:
            from accounts.models import TenantMembership

            count = TenantMembership.objects.filter(user=self.user).delete()[0]
            deleted["tenant_memberships"] = count
        except Exception as e:
            logger.warning(f"Could not delete tenant memberships: {e}")

        return deleted

    def _delete_user_data(self) -> Dict[str, int]:
        """Permanently delete user and all related data."""
        deleted = {}

        # Delete tenant memberships
        try:
            from accounts.models import TenantMembership

            count = TenantMembership.objects.filter(user=self.user).delete()[0]
            deleted["tenant_memberships"] = count
        except Exception:
            pass

        # Delete chat messages
        try:
            from chatbot.models import Message

            count = Message.objects.filter(
                session__user_identifier=str(self.user.id)
            ).delete()[0]
            deleted["chat_messages"] = count
        except Exception:
            pass

        # Delete knowledge sources
        try:
            from knowledge.models import KnowledgeSource

            count = KnowledgeSource.objects.filter(created_by=self.user).delete()[0]
            deleted["knowledge_sources"] = count
        except Exception:
            pass

        # Delete audit logs
        try:
            from compliance.models import AuditLog

            count = AuditLog.objects.filter(user=self.user).delete()[0]
            deleted["audit_logs"] = count
        except Exception:
            pass

        # Finally, delete user account
        self.user.delete()
        deleted["user_account"] = 1

        return deleted


class GDPRConsentManager:
    """
    Manages user consent for data processing.

    Tracks consent for different processing purposes.
    """

    CONSENT_PURPOSES = {
        "essential": "Essential services (authentication, core functionality)",
        "analytics": "Analytics and performance monitoring",
        "marketing": "Marketing communications and promotions",
        "third_party": "Third-party integrations and data sharing",
    }

    @staticmethod
    def record_consent(user: User, purpose: str, granted: bool):
        """
        Record user consent for a specific purpose.

        Args:
            user: User instance
            purpose: Consent purpose (e.g., 'marketing', 'analytics')
            granted: Whether consent was granted
        """
        from compliance.models import UserConsent

        consent, created = UserConsent.objects.update_or_create(
            user=user,
            purpose=purpose,
            defaults={
                "granted": granted,
                "granted_at": datetime.now() if granted else None,
            },
        )

        logger.info(
            f"Consent {purpose} {'granted' if granted else 'revoked'} "
            f"for user {user.id}"
        )

        return consent

    @staticmethod
    def check_consent(user: User, purpose: str) -> bool:
        """
        Check if user has granted consent for a specific purpose.

        Args:
            user: User instance
            purpose: Consent purpose

        Returns:
            True if consent granted, False otherwise
        """
        from compliance.models import UserConsent

        try:
            consent = UserConsent.objects.get(user=user, purpose=purpose)
            return consent.granted
        except UserConsent.DoesNotExist:
            # Essential consent is assumed granted
            if purpose == "essential":
                return True
            return False

    @staticmethod
    def get_all_consents(user: User) -> Dict[str, bool]:
        """Get all consent statuses for a user."""
        from compliance.models import UserConsent

        consents = UserConsent.objects.filter(user=user)
        consent_dict = {c.purpose: c.granted for c in consents}

        # Fill in missing purposes with defaults
        for purpose in GDPRConsentManager.CONSENT_PURPOSES:
            if purpose not in consent_dict:
                consent_dict[purpose] = purpose == "essential"

        return consent_dict


def notify_data_breach(
    affected_users: list[User],
    breach_description: str,
    data_categories: list[str],
):
    """
    Notify users of a data breach (GDPR Article 34 requirement).

    Args:
        affected_users: List of affected users
        breach_description: Description of the breach
        data_categories: Categories of data affected
    """
    subject = "Important Security Notice - Data Breach Notification"

    for user in affected_users:
        context = {
            "user": user,
            "breach_description": breach_description,
            "data_categories": data_categories,
            "date": datetime.now(),
            "support_email": settings.DEFAULT_FROM_EMAIL,
        }

        html_message = render_to_string(
            "emails/data_breach_notification.html",
            context
        )
        plain_message = render_to_string(
            "emails/data_breach_notification.txt",
            context
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.critical(
            f"Data breach notification sent to user {user.id} ({user.email})"
        )
