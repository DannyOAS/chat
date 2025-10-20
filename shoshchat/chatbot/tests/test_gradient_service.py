"""Unit tests for the Gradient LLM service wrapper."""

from __future__ import annotations

import pytest

from chatbot.services.gradient_service import GradientLLM


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_gradient_llm_generate_sends_expected_payload(monkeypatch):
    captured = {}

    class DummyRequests:
        @staticmethod
        def post(url, headers, json, timeout):  # noqa: A002 - matches requests signature
            captured.update({
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            })
            return DummyResponse({"outputs": [{"content": "Hi there"}]})

    monkeypatch.setattr("chatbot.services.gradient_service.requests", DummyRequests, raising=False)

    llm = GradientLLM("https://gradient.ai", timeout=15, api_key="secret-key")
    result = llm.generate("Hello", system_prompt="You are helpful")

    assert result == "Hi there"
    assert captured["url"] == "https://gradient.ai"
    assert captured["timeout"] == 15
    assert captured["headers"]["Authorization"] == "Bearer secret-key"
    assert captured["json"]["inputs"][0]["role"] == "system"
    assert captured["json"]["inputs"][0]["content"] == "You are helpful"
    assert captured["json"]["inputs"][1]["content"] == "Hello"


def test_gradient_llm_generate_raises_for_unexpected_payload(monkeypatch, caplog):
    class DummyRequests:
        @staticmethod
        def post(*_args, **_kwargs):
            return DummyResponse({"unexpected": []})

    monkeypatch.setattr("chatbot.services.gradient_service.requests", DummyRequests, raising=False)

    llm = GradientLLM("https://gradient.ai", api_key="secret")

    with caplog.at_level("ERROR"):
        with pytest.raises(ValueError):
            llm.generate("hi")

    assert any("Unexpected Gradient response" in message for message in caplog.messages)
