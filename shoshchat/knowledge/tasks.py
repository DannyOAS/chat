"""Celery tasks for processing tenant knowledge sources."""
from __future__ import annotations

import logging

from celery import shared_task
from django.db import transaction

from knowledge.chunker import chunk_text
from knowledge.embeddings import embed_text
from knowledge.models import KnowledgeChunk, KnowledgeSource
from knowledge.processors import combine_segments, extract_text_from_file, extract_text_from_html

logger = logging.getLogger(__name__)


@shared_task
def process_knowledge_source(source_id: int) -> str:
    """Extract, chunk, embed, and persist knowledge for a source."""

    try:
        source = KnowledgeSource.objects.select_related("tenant").get(pk=source_id)
    except KnowledgeSource.DoesNotExist:  # pragma: no cover - defensive
        logger.error("KnowledgeSource %s no longer exists", source_id)
        return "missing"

    if source.status == KnowledgeSource.Status.PROCESSING:
        return "already-processing"

    source.status = KnowledgeSource.Status.PROCESSING
    source.save(update_fields=["status"])

    try:
        text = _extract_text(source)
        _store_chunks(source, text)
        source.status = KnowledgeSource.Status.READY
        source.error_message = ""
        source.save(update_fields=["status", "error_message"])
        return "ready"
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Knowledge ingestion failed", exc_info=exc)
        source.status = KnowledgeSource.Status.FAILED
        source.error_message = str(exc)
        source.save(update_fields=["status", "error_message"])
        return "failed"


def _extract_text(source: KnowledgeSource) -> str:
    if source.source_type == KnowledgeSource.SourceType.FILE and source.file:
        return extract_text_from_file(source.file)
    if source.source_type == KnowledgeSource.SourceType.URL and source.url:
        return extract_text_from_html(source.url)
    if source.source_type == KnowledgeSource.SourceType.TEXT and source.raw_text:
        return source.raw_text
    raise ValueError("No extractable content for knowledge source")


@transaction.atomic
def _store_chunks(source: KnowledgeSource, text: str) -> None:
    tenant = source.tenant
    KnowledgeChunk.objects.filter(source=source).delete()
    segments = list(chunk_text(text))
    combined = combine_segments(segments)
    if not combined:
        return

    for index, chunk in enumerate(chunk_text(combined)):
        embedding, model_name = embed_text(chunk, tenant)
        KnowledgeChunk.objects.create(
            source=source,
            tenant=tenant,
            sequence=index,
            content=chunk,
            token_count=len(chunk.split()),
            embedding=embedding,
            embedding_model=model_name,
        )
