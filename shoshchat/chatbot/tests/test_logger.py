"""Tests for the structured chat logger."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from chatbot.services.logger import ChatLogger


class DummyTenant:
    schema_name = "acme"


def test_chat_logger_emits_hashed_payload(caplog):
    logger = ChatLogger(tenant=DummyTenant())
    timestamp = datetime(2024, 1, 1, 12, 30, tzinfo=timezone.utc)

    with caplog.at_level("INFO"):
        logger.log_event(
            user_id="user-123",
            message="Hello there",
            response="General Kenobi",
            timestamp=timestamp,
        )

    assert caplog.records, "Expected a log record to be emitted"
    record = caplog.records[0]
    payload = record.__dict__["payload"]

    expected_message_hash = hashlib.sha256("Hello there".encode()).hexdigest()
    expected_response_hash = hashlib.sha256("General Kenobi".encode()).hexdigest()

    assert "acme" in payload
    assert expected_message_hash in payload
    assert expected_response_hash in payload
    assert timestamp.isoformat() in payload
