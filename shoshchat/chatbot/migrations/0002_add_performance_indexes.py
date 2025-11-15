"""Add performance indexes to chatbot models."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chatbot', '0001_initial'),
    ]

    operations = [
        # Add indexes to ChatSession
        migrations.AddIndex(
            model_name='chatsession',
            index=models.Index(fields=['tenant', 'user_id'], name='chat_session_tenant_user_idx'),
        ),
        migrations.AddIndex(
            model_name='chatsession',
            index=models.Index(fields=['-last_interaction_at'], name='chat_session_last_interaction_idx'),
        ),

        # Add indexes to Message
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['session', '-created_at'], name='message_session_created_idx'),
        ),
        migrations.AddIndex(
            model_name='message',
            index=models.Index(fields=['-created_at'], name='message_created_idx'),
        ),

        # Add ordering to Message model
        migrations.AlterModelOptions(
            name='message',
            options={'ordering': ['-created_at']},
        ),

        # Add indexes to Intent
        migrations.AddIndex(
            model_name='intent',
            index=models.Index(fields=['tenant', 'name'], name='intent_tenant_name_idx'),
        ),
    ]
