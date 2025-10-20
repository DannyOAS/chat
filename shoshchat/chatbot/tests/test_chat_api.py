"""Basic smoke tests for chatbot API endpoints."""
from __future__ import annotations

from django.test import TestCase
from django.urls import reverse


class ChatApiTests(TestCase):
    def test_chat_endpoint_requires_message(self):
        url = reverse("chatbot:chat")
        response = self.client.post(url, {})
        self.assertEqual(response.status_code, 400)
