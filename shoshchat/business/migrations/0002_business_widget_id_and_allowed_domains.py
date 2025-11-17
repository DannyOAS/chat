# Generated migration for widget_id and allowed_domains

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='business',
            name='widget_id',
            field=models.UUIDField(
                default=uuid.uuid4,
                unique=True,
                editable=False,
                help_text='Unique widget ID for anonymous chat widget embedding',
            ),
        ),
        migrations.AddField(
            model_name='business',
            name='allowed_domains',
            field=models.JSONField(
                default=list,
                blank=True,
                help_text='List of domains allowed to embed this widget (empty = all domains allowed)',
            ),
        ),
        migrations.AddIndex(
            model_name='business',
            index=models.Index(fields=['widget_id'], name='business_bus_widget__idx'),
        ),
    ]
