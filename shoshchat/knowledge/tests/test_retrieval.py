"""Tests for knowledge retrieval pipeline."""
from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from knowledge.models import KnowledgeChunk, KnowledgeSource
from knowledge.retrieval import retrieve_relevant_chunks
from tenancy.models import Tenant


class KnowledgeRetrievalTests(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create(username="owner", email="owner@example.com")
        Tenant.auto_create_schema = False  # Avoid tenant schema creation during tests
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            schema_name="test_tenant",
            industry=Tenant.RETAIL,
            owner=self.user,
        )
        self.source = KnowledgeSource.objects.create(
            tenant=self.tenant,
            title="Support FAQ",
            source_type=KnowledgeSource.SourceType.TEXT,
            status=KnowledgeSource.Status.READY,
        )

    def tearDown(self) -> None:
        Tenant.auto_create_schema = True

    def test_retrieval_returns_ranked_chunks(self):
        embedding = [1.0] + [0.0] * 255
        KnowledgeChunk.objects.create(
            source=self.source,
            tenant=self.tenant,
            sequence=0,
            content="Answer about store hours",
            token_count=4,
            embedding=embedding,
            embedding_model="hash-fallback",
        )

        with patch("knowledge.retrieval.embed_query", return_value=embedding):
            results = retrieve_relevant_chunks(self.tenant, "When are you open?")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content, "Answer about store hours")
        self.assertGreater(results[0].score, 0.9)
