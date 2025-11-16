"""Models supporting business knowledge ingestion and retrieval."""
from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.postgres.fields import ArrayField
from django.db import models

if TYPE_CHECKING:  # pragma: no cover - typing only
    from business.models import Business


class KnowledgeSource(models.Model):
    """Represents a knowledge artifact uploaded or linked by a business."""

    class SourceType(models.TextChoices):
        FILE = "file", "File Upload"
        URL = "url", "URL"
        TEXT = "text", "Text Snippet"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey("tenancy.Tenant", related_name="knowledge_sources", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", related_name="knowledge_sources", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    title = models.CharField(max_length=255)
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    file = models.FileField(upload_to="knowledge_sources/", blank=True)
    url = models.URLField(blank=True)
    raw_text = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=['tenant', 'status'], name='knowledge_source_status_idx'),
            models.Index(fields=['-created_at'], name='knowledge_source_created_idx'),
        ]

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"{self.title} ({self.get_status_display()})"


class KnowledgeChunk(models.Model):
    """Chunk of processed text with vector embedding."""

    source = models.ForeignKey(KnowledgeSource, related_name="chunks", on_delete=models.CASCADE)
    tenant = models.ForeignKey("tenancy.Tenant", related_name="knowledge_chunks", on_delete=models.CASCADE, null=True, blank=True)  # Legacy, will be removed
    business = models.ForeignKey("business.Business", related_name="knowledge_chunks", on_delete=models.CASCADE, null=True, blank=True)  # New single-domain
    sequence = models.PositiveIntegerField()
    content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    # Updated to 384 dimensions for all-MiniLM-L6-v2
    embedding = ArrayField(models.FloatField(), size=384, blank=True, default=list)
    embedding_model = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("source", "sequence")
        unique_together = ("source", "sequence")
        indexes = [
            models.Index(fields=['tenant'], name='knowledge_chunk_tenant_idx'),
        ]

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Chunk {self.sequence} of {self.source.title}"
