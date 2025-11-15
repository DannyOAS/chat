"""Add Two-Factor Authentication and RBAC support."""
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('tenancy', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add 2FA fields to UserProfile
        migrations.AddField(
            model_name='userprofile',
            name='two_factor_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='two_factor_secret',
            field=models.CharField(blank=True, default='', max_length=32),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='backup_codes',
            field=models.JSONField(blank=True, default=list),
        ),

        # Create Role choices class (stored as data, not model)

        # Create TenantMembership model
        migrations.CreateModel(
            name='TenantMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(
                    choices=[
                        ('owner', 'Owner'),
                        ('admin', 'Admin'),
                        ('member', 'Member'),
                        ('guest', 'Guest')
                    ],
                    default='member',
                    max_length=16
                )),
                ('joined_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('invited_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='invitations_sent',
                    to=settings.AUTH_USER_MODEL
                )),
                ('tenant', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memberships',
                    to='tenancy.tenant'
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='memberships',
                    to=settings.AUTH_USER_MODEL
                )),
            ],
            options={
                'ordering': ['-joined_at'],
                'unique_together': {('user', 'tenant')},
            },
        ),

        # Add indexes for performance
        migrations.AddIndex(
            model_name='tenantmembership',
            index=models.Index(fields=['tenant', 'role'], name='tenant_role_idx'),
        ),
        migrations.AddIndex(
            model_name='tenantmembership',
            index=models.Index(fields=['user', 'is_active'], name='user_active_idx'),
        ),
    ]
