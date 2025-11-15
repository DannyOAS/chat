"""Add pgvector extension and update embedding dimensions."""
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField


class Migration(migrations.Migration):

    dependencies = [
        ('knowledge', '0001_initial'),
    ]

    operations = [
        # Enable pgvector extension
        CreateExtension('vector'),

        # Update embedding dimension from 256 to 384 for all-MiniLM-L6-v2
        migrations.AlterField(
            model_name='knowledgechunk',
            name='embedding',
            field=ArrayField(
                models.FloatField(),
                size=384,
                blank=True,
                default=list
            ),
        ),

        # Add index on tenant for faster filtering
        migrations.AddIndex(
            model_name='knowledgechunk',
            index=models.Index(fields=['tenant'], name='knowledge_chunk_tenant_idx'),
        ),

        # Add index on source and sequence for faster ordering
        migrations.AddIndex(
            model_name='knowledgesource',
            index=models.Index(fields=['tenant', 'status'], name='knowledge_source_status_idx'),
        ),

        # Add index on created_at for sorting
        migrations.AddIndex(
            model_name='knowledgesource',
            index=models.Index(fields=['-created_at'], name='knowledge_source_created_idx'),
        ),
    ]
