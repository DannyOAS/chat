"""Billing signal handlers for Stripe events."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def handle_stripe_event(event_type: str, payload: dict) -> None:
    """Placeholder handler for Stripe webhook events."""

    logger.info("Stripe event received", extra={"event_type": event_type, "payload": payload})
