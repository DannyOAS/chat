"""API views for tenant knowledge management."""
from __future__ import annotations

from django.db.models import Count
from rest_framework import generics, permissions, response, status

from knowledge.api.serializers import (
    KnowledgeChunkSerializer,
    KnowledgeSourceCreateSerializer,
    KnowledgeSourceSerializer,
)
from knowledge.models import KnowledgeChunk, KnowledgeSource
from knowledge.tasks import process_knowledge_source


class KnowledgeSourceListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KnowledgeSourceSerializer

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return (
            KnowledgeSource.objects.filter(tenant=tenant)
            .annotate(chunk_count=Count("chunks"))
            .order_by("-created_at")
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return KnowledgeSourceCreateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        tenant = getattr(self.request, "tenant", None)
        source = serializer.save(tenant=tenant, status=KnowledgeSource.Status.PENDING)
        process_knowledge_source.delay(source.pk)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return response.Response({"detail": "Knowledge source queued for processing."}, status=status.HTTP_202_ACCEPTED)


class KnowledgeSourceDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KnowledgeSourceSerializer

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return KnowledgeSource.objects.filter(tenant=tenant).annotate(chunk_count=Count("chunks"))


class KnowledgeChunkListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = KnowledgeChunkSerializer

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        source_id = self.kwargs.get("source_id")
        queryset = KnowledgeChunk.objects.filter(tenant=tenant)
        if source_id:
            queryset = queryset.filter(source_id=source_id)
        return queryset.order_by("sequence")
