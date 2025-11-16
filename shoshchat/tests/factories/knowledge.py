"""Knowledge factory for tests."""
import factory
from faker import Faker

from knowledge.models import KnowledgeSource, KnowledgeChunk
from .tenant import TenantFactory

fake = Faker()


class KnowledgeSourceFactory(factory.django.DjangoModelFactory):
    """Factory for creating test knowledge sources."""

    class Meta:
        model = KnowledgeSource

    tenant = factory.SubFactory(TenantFactory)
    title = factory.Faker("sentence", nb_words=4)
    content = factory.Faker("text", max_nb_chars=1000)
    source_type = "text"
    status = "completed"
    chunk_count = 0


class KnowledgeChunkFactory(factory.django.DjangoModelFactory):
    """Factory for creating test knowledge chunks."""

    class Meta:
        model = KnowledgeChunk

    tenant = factory.SelfAttribute("source.tenant")
    source = factory.SubFactory(KnowledgeSourceFactory)
    content = factory.Faker("paragraph")
    sequence = factory.Sequence(lambda n: n)
    embedding = factory.LazyFunction(lambda: [0.0] * 384)  # 384-dim zero vector
