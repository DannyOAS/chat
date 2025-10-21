"""Views for chatbot REST endpoints."""
from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count
from rest_framework import generics, permissions, response, status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from chatbot.models import ChatSession, Message
from chatbot.services.chatbot_service import ChatbotService
from .serializers import ChatRequestSerializer, ChatSessionSerializer


class ChatMessageView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "chat"

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tenant = getattr(request, "tenant", None)
        try:
            service = ChatbotService(tenant)
        except ImproperlyConfigured:
            return response.Response(
                {"detail": "Tenant context is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        data = serializer.validated_data
        reply = service.process_message(data["message"], data["user_id"])
        return response.Response({"reply": reply}, status=status.HTTP_200_OK)


class ChatSessionListView(generics.ListAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return ChatSession.objects.filter(tenant=tenant).order_by("-last_interaction_at")


class ChatAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        total_sessions = ChatSession.objects.filter(tenant=tenant).count()
        total_messages = Message.objects.filter(session__tenant=tenant).count()
        last_messages = (
            Message.objects.filter(session__tenant=tenant)
            .values("role")
            .annotate(total=Count("id"))
        )
        role_breakdown = {entry["role"]: entry["total"] for entry in last_messages}
        recent_sessions = (
            ChatSession.objects.filter(tenant=tenant)
            .values("user_id", "last_interaction_at")
            .order_by("-last_interaction_at")[:5]
        )
        return response.Response(
            {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "role_breakdown": role_breakdown,
                "recent_sessions": list(recent_sessions),
            }
        )
