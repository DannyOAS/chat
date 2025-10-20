"""High-level orchestration for chatbot message processing."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from django.core.exceptions import ImproperlyConfigured
from django.utils import timezone

from billing.models import UsageLog
from chatbot.models import ChatSession
from compliance.models import AuditLog
from nlp.models import LLMConfig
from nlp.adapters.gradient_adapter import GradientAdapter
from nlp.adapters.openai_fallback import OpenAIAdapter
from .logger import ChatLogger

logger = logging.getLogger(__name__)


class ChatbotService:
    """Tenant-scoped service responsible for responding to user messages."""

    def __init__(self, tenant) -> None:  # pragma: no cover - initialization
        if tenant is None:
            raise ImproperlyConfigured("ChatbotService requires a tenant context")
        self.tenant = tenant
        self.config: Optional[LLMConfig] = LLMConfig.objects.filter(tenant=tenant).first()
        self.logger = ChatLogger(tenant=tenant)

    def _get_adapter(self) -> GradientAdapter | OpenAIAdapter:
        if self.config:
            return GradientAdapter(self.config)
        return OpenAIAdapter()

    def _log_usage(self, timestamp: datetime) -> None:
        period_start = timestamp.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (period_start + timedelta(days=32)).replace(day=1)
        usage, _ = UsageLog.objects.get_or_create(
            tenant=self.tenant,
            period_start=period_start,
            period_end=next_month - timedelta(seconds=1),
        )
        usage.increment(timestamp=timestamp)

    def process_message(self, message: str, user_id: str) -> str:
        adapter = self._get_adapter()
        try:
            response = adapter.generate(message)
        except Exception:  # pragma: no cover - fallback path
            logger.exception("Falling back to OpenAI adapter")
            response = OpenAIAdapter().generate(message)
        ChatSession.log_interaction(self.tenant, user_id, message, response)
        now = timezone.now()
        self._log_usage(now)
        AuditLog.record(self.tenant, user_id, "message.sent", message)
        AuditLog.record(self.tenant, user_id, "message.received", response)
        self.logger.log_event(
            user_id=user_id,
            message=message,
            response=response,
            timestamp=now,
        )
        return response


__all__ = ["ChatbotService"]
