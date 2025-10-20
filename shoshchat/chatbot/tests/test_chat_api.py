"""Basic smoke tests for chatbot API endpoints."""
from __future__ import annotations

import pytest

django = pytest.importorskip("django", reason="Django is required for API endpoint tests")

from django.test import TestCase  # type: ignore  # noqa: E402  # imported after guard
from django.urls import reverse  # type: ignore  # noqa: E402


class ChatApiTests(TestCase):
    def test_chat_endpoint_requires_message(self):
        url = reverse("chatbot:chat")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
