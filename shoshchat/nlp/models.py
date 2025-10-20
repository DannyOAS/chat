"""Models representing NLP configuration."""
from __future__ import annotations

from django.db import models


class LLMConfig(models.Model):
    """Configuration for interacting with the tenant's preferred LLM."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE)
    endpoint = models.URLField()
    model_name = models.CharField(max_length=255)
    system_prompt = models.TextField(blank=True)
    temperature = models.FloatField(default=0.3)

    class Meta:
        unique_together = ("tenant", "model_name")


class PromptTemplate(models.Model):
    """Prompt templates controlling chatbot tone and instructions."""

    tenant = models.ForeignKey("tenancy.Tenant", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    content = models.TextField()
    industry = models.CharField(max_length=32, blank=True)

    class Meta:
        unique_together = ("tenant", "name")
