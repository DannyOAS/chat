"""Structured logging helpers for chatbot interactions."""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatLogger:
    """Dataclass encapsulating audit logging helpers."""

    tenant: object

    def log_event(self, *, user_id: str, message: str, response: str, timestamp: datetime) -> None:
        payload = {
            "tenant": getattr(self.tenant, "schema_name", "unknown"),
            "user": user_id,
            "message_hash": hashlib.sha256(message.encode()).hexdigest(),
            "response_hash": hashlib.sha256(response.encode()).hexdigest(),
            "timestamp": timestamp.isoformat(),
        }
        logger.info("chat.interaction", extra={"payload": json.dumps(payload)})
