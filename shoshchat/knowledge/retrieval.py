"""Retrieval helpers for knowledge-aware chat responses using pgvector."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from django.db.models import F, FloatField
from django.db.models.expressions import RawSQL

from knowledge.embeddings import embed_query
from knowledge.models import KnowledgeChunk

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class RetrievedChunk:
    content: str
    score: float
    source_title: str
    chunk_id: int
    sequence: int


def retrieve_relevant_chunks(
    tenant,
    query: str,
    top_k: int = 3,
    min_score: float = 0.3
) -> List[RetrievedChunk]:
    """
    Return top matching knowledge chunks for the tenant query using pgvector.

    Args:
        tenant: Tenant to search within
        query: Search query text
        top_k: Number of top results to return
        min_score: Minimum similarity score threshold (0-1)

    Returns:
        List of RetrievedChunk objects sorted by relevance
    """
    # Check if tenant has any knowledge chunks
    if not KnowledgeChunk.objects.filter(tenant=tenant).exists():
        logger.debug(f"No knowledge chunks found for tenant {tenant.schema_name}")
        return []

    # Generate query embedding
    try:
        query_vector = embed_query(query, tenant)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    if not query_vector:
        logger.warning("Empty query vector generated")
        return []

    # Use PostgreSQL's cosine similarity with pgvector
    # For ArrayField, we calculate cosine similarity manually with SQL
    similarity_sql = """
        (
            SELECT
                COALESCE(
                    SUM(a.val * b.val) /
                    NULLIF(
                        (SQRT(SUM(a.val * a.val)) * SQRT(SUM(b.val * b.val))),
                        0
                    ),
                    0
                )
            FROM unnest(embedding) WITH ORDINALITY AS a(val, idx)
            JOIN unnest(%s::float[]) WITH ORDINALITY AS b(val, idx) USING (idx)
        )
    """

    try:
        chunks = (
            KnowledgeChunk.objects
            .filter(tenant=tenant)
            .exclude(embedding=[])  # Exclude empty embeddings
            .select_related("source")
            .annotate(
                similarity=RawSQL(
                    similarity_sql,
                    (query_vector,),
                    output_field=FloatField()
                )
            )
            .filter(similarity__gte=min_score)  # Filter by minimum score
            .order_by('-similarity')  # Sort by highest similarity first
            [:top_k]  # Limit to top k results
        )

        results = [
            RetrievedChunk(
                content=chunk.content,
                score=chunk.similarity,
                source_title=chunk.source.title,
                chunk_id=chunk.id,
                sequence=chunk.sequence,
            )
            for chunk in chunks
        ]

        logger.debug(
            f"Retrieved {len(results)} chunks for query '{query[:50]}...' "
            f"(top score: {results[0].score:.3f})" if results else f"Retrieved 0 chunks"
        )

        return results

    except Exception as e:
        logger.error(f"Error during retrieval: {e}", exc_info=True)
        return []


def retrieve_by_source(
    source_id: int,
    query: str,
    top_k: int = 5
) -> List[RetrievedChunk]:
    """
    Retrieve chunks from a specific knowledge source.

    Args:
        source_id: ID of the knowledge source
        query: Search query
        top_k: Number of results

    Returns:
        List of matching chunks from the source
    """
    try:
        query_vector = embed_query(query)
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        return []

    similarity_sql = """
        (
            SELECT
                COALESCE(
                    SUM(a.val * b.val) /
                    NULLIF(
                        (SQRT(SUM(a.val * a.val)) * SQRT(SUM(b.val * b.val))),
                        0
                    ),
                    0
                )
            FROM unnest(embedding) WITH ORDINALITY AS a(val, idx)
            JOIN unnest(%s::float[]) WITH ORDINALITY AS b(val, idx) USING (idx)
        )
    """

    try:
        chunks = (
            KnowledgeChunk.objects
            .filter(source_id=source_id)
            .exclude(embedding=[])
            .select_related("source")
            .annotate(
                similarity=RawSQL(
                    similarity_sql,
                    (query_vector,),
                    output_field=FloatField()
                )
            )
            .order_by('-similarity')
            [:top_k]
        )

        return [
            RetrievedChunk(
                content=chunk.content,
                score=chunk.similarity,
                source_title=chunk.source.title,
                chunk_id=chunk.id,
                sequence=chunk.sequence,
            )
            for chunk in chunks
        ]

    except Exception as e:
        logger.error(f"Error retrieving from source: {e}", exc_info=True)
        return []


def get_chunk_neighbors(chunk_id: int, context_window: int = 2) -> List[KnowledgeChunk]:
    """
    Get neighboring chunks around a specific chunk for context.

    Args:
        chunk_id: ID of the target chunk
        context_window: Number of chunks before and after to include

    Returns:
        List of neighboring chunks in sequence order
    """
    try:
        chunk = KnowledgeChunk.objects.select_related('source').get(id=chunk_id)

        neighbors = (
            KnowledgeChunk.objects
            .filter(
                source=chunk.source,
                sequence__gte=chunk.sequence - context_window,
                sequence__lte=chunk.sequence + context_window
            )
            .order_by('sequence')
        )

        return list(neighbors)

    except KnowledgeChunk.DoesNotExist:
        logger.warning(f"Chunk {chunk_id} not found")
        return []
    except Exception as e:
        logger.error(f"Error getting chunk neighbors: {e}")
        return []
