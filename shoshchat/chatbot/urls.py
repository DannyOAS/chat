"""API routing for chatbot endpoints."""
from __future__ import annotations

from django.urls import path

from .api.views import ChatMessageView, ChatSessionListView

app_name = "chatbot"

urlpatterns = [
    path("", ChatMessageView.as_view(), name="chat"),
    path("sessions/", ChatSessionListView.as_view(), name="sessions"),
]
