"""Routing for knowledge management API."""
from __future__ import annotations

from django.urls import path

from knowledge.api.views import (
    KnowledgeChunkListView,
    KnowledgeSourceDetailView,
    KnowledgeSourceListCreateView,
)

app_name = "knowledge"

urlpatterns = [
    path("sources/", KnowledgeSourceListCreateView.as_view(), name="sources"),
    path("sources/<int:pk>/", KnowledgeSourceDetailView.as_view(), name="source-detail"),
    path("sources/<int:source_id>/chunks/", KnowledgeChunkListView.as_view(), name="source-chunks"),
]
