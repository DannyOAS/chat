"""API routing for chatbot endpoints."""
from __future__ import annotations

from django.urls import path

from .api.views import ChatAnalyticsView, ChatMessageView, ChatSessionListView

app_name = "chatbot"

urlpatterns = [
    path("", ChatMessageView.as_view(), name="chat"),
    path("sessions/", ChatSessionListView.as_view(), name="sessions"),
    path("analytics/", ChatAnalyticsView.as_view(), name="analytics"),
]
