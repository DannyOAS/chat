"""Retrieval helpers for knowledge-aware chat responses."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from knowledge.embeddings import cosine_similarity, embed_query
from knowledge.models import KnowledgeChunk


@dataclass(slots=True)
class RetrievedChunk:
    content: str
    score: float
    source_title: str


def retrieve_relevant_chunks(tenant, query: str, top_k: int = 3) -> List[RetrievedChunk]:
    """Return top matching knowledge chunks for the tenant query."""

    chunks = KnowledgeChunk.objects.filter(tenant=tenant).select_related("source")
    if not chunks.exists():
        return []

    query_vector = embed_query(query, tenant)
    results: list[RetrievedChunk] = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        score = cosine_similarity(query_vector, chunk.embedding)
        if score <= 0:
            continue
        results.append(
            RetrievedChunk(
                content=chunk.content,
                score=score,
                source_title=chunk.source.title,
            )
        )
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:top_k]
