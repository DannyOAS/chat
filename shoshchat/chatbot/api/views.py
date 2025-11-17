"""Views for chatbot REST endpoints."""
from __future__ import annotations

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Count
from rest_framework import generics, permissions, response, status
from rest_framework.views import APIView
from urllib.parse import urlparse

from business.models import Business
from chatbot.models import ChatSession, Message
from chatbot.services.chatbot_service import ChatbotService
from chatbot.throttling import WidgetRateThrottle
from .serializers import ChatRequestSerializer, ChatSessionSerializer


class ChatMessageView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [WidgetRateThrottle]

    def _verify_domain(self, request, business):
        """Verify that the request origin is allowed for this business."""
        # If no domains are configured, allow all
        if not business.allowed_domains:
            return True

        # Get origin/referer from request headers
        origin = request.META.get('HTTP_ORIGIN', '')
        referer = request.META.get('HTTP_REFERER', '')

        # Extract domain from origin or referer
        request_domain = None
        if origin:
            request_domain = urlparse(origin).netloc
        elif referer:
            request_domain = urlparse(referer).netloc

        # If we can't determine the domain, reject the request
        if not request_domain:
            return False

        # Check if domain is in allowed list
        # Support both exact match and wildcard subdomains
        for allowed in business.allowed_domains:
            if allowed.startswith('*.'):
                # Wildcard subdomain match (e.g., *.example.com matches shop.example.com)
                base_domain = allowed[2:]
                if request_domain.endswith(base_domain):
                    return True
            elif request_domain == allowed:
                # Exact match
                return True

        return False

    def post(self, request, *args, **kwargs):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Determine business context
        business = None

        # Option 1: Widget ID provided (anonymous widget request)
        if 'widget_id' in data:
            try:
                business = Business.objects.get(widget_id=data['widget_id'], is_active=True)
            except Business.DoesNotExist:
                return response.Response(
                    {"detail": "Invalid widget ID."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Verify domain for widget requests
            if not self._verify_domain(request, business):
                return response.Response(
                    {"detail": "Domain not authorized for this widget."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Option 2: Authenticated request (dashboard usage)
        else:
            business = getattr(request, "business", None)

        # Ensure we have a business context
        if not business:
            return response.Response(
                {"detail": "Business context is required. Provide widget_id or authenticate."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Process the message
        try:
            service = ChatbotService(business)
        except ImproperlyConfigured:
            return response.Response(
                {"detail": "Business context is improperly configured."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reply = service.process_message(data["message"], data["user_id"])
        return response.Response({"reply": reply}, status=status.HTTP_200_OK)


class ChatSessionListView(generics.ListAPIView):
    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Changed from request.tenant to request.business (Phase 3: Single-domain)
        business = getattr(self.request, "business", None)
        if not business:
            return ChatSession.objects.none()
        return ChatSession.objects.filter(business=business).order_by("-last_interaction_at")


class ChatAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Changed from request.tenant to request.business (Phase 3: Single-domain)
        business = getattr(request, "business", None)
        if not business:
            return response.Response(
                {"detail": "Business context is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_sessions = ChatSession.objects.filter(business=business).count()
        total_messages = Message.objects.filter(session__business=business).count()
        last_messages = (
            Message.objects.filter(session__business=business)
            .values("role")
            .annotate(total=Count("id"))
        )
        role_breakdown = {entry["role"]: entry["total"] for entry in last_messages}
        recent_sessions = (
            ChatSession.objects.filter(business=business)
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
