"""Models supporting tenant knowledge ingestion and retrieval."""
from __future__ import annotations

from django.contrib.postgres.fields import ArrayField
from django.db import models


class KnowledgeSource(models.Model):
    """Represents a knowledge artifact uploaded or linked by a tenant."""

    class SourceType(models.TextChoices):
        FILE = "file", "File Upload"
        URL = "url", "URL"
        TEXT = "text", "Text Snippet"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    tenant = models.ForeignKey("tenancy.Tenant", related_name="knowledge_sources", on_delete=models.CASCADE)
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

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"{self.title} ({self.get_status_display()})"


class KnowledgeChunk(models.Model):
    """Chunk of processed text with vector embedding."""

    source = models.ForeignKey(KnowledgeSource, related_name="chunks", on_delete=models.CASCADE)
    tenant = models.ForeignKey("tenancy.Tenant", related_name="knowledge_chunks", on_delete=models.CASCADE)
    sequence = models.PositiveIntegerField()
    content = models.TextField()
    token_count = models.PositiveIntegerField(default=0)
    embedding = ArrayField(models.FloatField(), size=256, blank=True, default=list)
    embedding_model = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("source", "sequence")
        unique_together = ("source", "sequence")

    def __str__(self) -> str:  # pragma: no cover - human readable
        return f"Chunk {self.sequence} of {self.source.title}"
