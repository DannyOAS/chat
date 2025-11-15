"""Add performance indexes to billing models."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0001_initial'),
    ]

    operations = [
        # Add indexes to Subscription
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['tenant', 'active'], name='subscription_tenant_active_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['current_period_end'], name='subscription_period_end_idx'),
        ),
        migrations.AddIndex(
            model_name='subscription',
            index=models.Index(fields=['stripe_subscription_id'], name='subscription_stripe_id_idx'),
        ),

        # Add indexes to UsageLog
        migrations.AddIndex(
            model_name='usagelog',
            index=models.Index(fields=['tenant', 'period_start', 'period_end'], name='usage_log_tenant_period_idx'),
        ),
        migrations.AddIndex(
            model_name='usagelog',
            index=models.Index(fields=['-last_message_at'], name='usage_log_last_message_idx'),
        ),
    ]
