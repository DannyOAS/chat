"""Serializers for knowledge ingestion API."""
from __future__ import annotations

from rest_framework import serializers

from knowledge.models import KnowledgeChunk, KnowledgeSource


class KnowledgeSourceSerializer(serializers.ModelSerializer):
    chunk_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = KnowledgeSource
        fields = [
            "id",
            "title",
            "source_type",
            "status",
            "metadata",
            "error_message",
            "created_at",
            "updated_at",
            "chunk_count",
        ]
        read_only_fields = ["status", "metadata", "error_message", "created_at", "updated_at", "chunk_count"]


class KnowledgeSourceCreateSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=False, allow_null=True)
    raw_text = serializers.CharField(required=False, allow_blank=True)
    url = serializers.URLField(required=False, allow_blank=True)

    class Meta:
        model = KnowledgeSource
        fields = ["title", "source_type", "file", "raw_text", "url"]

    def validate(self, attrs):
        source_type = attrs.get("source_type")
        if source_type == KnowledgeSource.SourceType.FILE and not attrs.get("file"):
            raise serializers.ValidationError({"file": "File upload required."})
        if source_type == KnowledgeSource.SourceType.URL and not attrs.get("url"):
            raise serializers.ValidationError({"url": "URL required."})
        if source_type == KnowledgeSource.SourceType.TEXT and not attrs.get("raw_text"):
            raise serializers.ValidationError({"raw_text": "Text content required."})
        return attrs


class KnowledgeChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeChunk
        fields = ["id", "sequence", "content", "token_count", "embedding_model"]
        read_only_fields = fields
