"""Serializers for chatbot API endpoints."""
from __future__ import annotations

from rest_framework import serializers

from chatbot.models import ChatSession, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "response_text", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ["id", "user_id", "started_at", "last_interaction_at", "messages"]


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField()
    user_id = serializers.CharField(max_length=255)
