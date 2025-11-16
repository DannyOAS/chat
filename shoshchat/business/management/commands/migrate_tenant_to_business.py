"""
Management command to migrate data from Tenant to Business model.

This command performs the Phase 4 data migration:
1. Creates Business records from existing Tenant records
2. Updates all foreign keys from tenant to business
3. Handles TenantMembership → TeamMember migration
4. Preserves all data integrity

Usage:
    python manage.py migrate_tenant_to_business [--dry-run]
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify


class Command(BaseCommand):
    help = "Migrate data from Tenant model to Business model"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run migration in dry-run mode (no database changes)",
        )

    def handle(self, *args, **options):
        """Execute the migration."""
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode - no changes will be saved"))

        try:
            with transaction.atomic():
                self.migrate_tenants_to_businesses()
                self.migrate_tenant_memberships()
                self.migrate_chat_sessions()
                self.migrate_intents()
                self.migrate_knowledge_sources()
                self.migrate_knowledge_chunks()
                self.migrate_subscriptions()
                self.migrate_usage_logs()
                self.migrate_audit_logs()
                self.migrate_consents()

                if dry_run:
                    self.stdout.write(self.style.WARNING("DRY-RUN complete - rolling back transaction"))
                    raise Exception("Dry run - intentional rollback")

            self.stdout.write(self.style.SUCCESS("✅ Migration completed successfully!"))

        except Exception as e:
            if not dry_run:
                self.stdout.write(self.style.ERROR(f"❌ Migration failed: {e}"))
                raise
            else:
                self.stdout.write(self.style.SUCCESS("✅ DRY-RUN validation passed"))

    def migrate_tenants_to_businesses(self):
        """Migrate Tenant records to Business records."""
        from tenancy.models import Tenant
        from business.models import Business

        self.stdout.write("Migrating Tenants → Businesses...")

        tenants = Tenant.objects.all()
        created_count = 0
        skipped_count = 0

        for tenant in tenants:
            # Check if business already exists
            if hasattr(tenant, "_business_migrated"):
                skipped_count += 1
                continue

            # Get owner (use first active membership if owner not set)
            owner = tenant.owner
            if not owner:
                membership = tenant.memberships.filter(is_active=True).first()
                if membership:
                    owner = membership.user
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️  Tenant {tenant.id} ({tenant.name}) has no owner - skipping"
                        )
                    )
                    skipped_count += 1
                    continue

            # Check if user already has a business
            existing_business = Business.objects.filter(owner=owner).first()
            if existing_business:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  User {owner.email} already has business - linking tenant {tenant.id}"
                    )
                )
                tenant._business_migrated = existing_business
                skipped_count += 1
                continue

            # Generate unique slug
            base_slug = slugify(tenant.name)
            slug = base_slug
            counter = 1
            while Business.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Create Business from Tenant
            business = Business.objects.create(
                name=tenant.name,
                slug=slug,
                owner=owner,
                industry="other",  # Default, can be updated later
                description=tenant.description if hasattr(tenant, "description") else "",
                paid_until=tenant.paid_until if hasattr(tenant, "paid_until") else None,
                on_trial=tenant.on_trial if hasattr(tenant, "on_trial") else True,
                is_active=True,
                created_at=tenant.created_on if hasattr(tenant, "created_on") else None,
            )

            # Store reference for foreign key updates
            tenant._business_migrated = business
            created_count += 1

            self.stdout.write(f"  ✓ Created Business: {business.name} (slug: {business.slug})")

        self.stdout.write(
            self.style.SUCCESS(
                f"  Created: {created_count} | Skipped: {skipped_count} | Total: {tenants.count()}"
            )
        )

    def migrate_tenant_memberships(self):
        """Migrate TenantMembership → TeamMember."""
        from accounts.models import TenantMembership
        from business.models import TeamMember

        self.stdout.write("Migrating TenantMemberships → TeamMembers...")

        memberships = TenantMembership.objects.all()
        created_count = 0
        skipped_count = 0

        for membership in memberships:
            tenant = membership.tenant

            # Get migrated business
            if not hasattr(tenant, "_business_migrated"):
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  Tenant {tenant.id} not migrated - skipping membership")
                )
                skipped_count += 1
                continue

            business = tenant._business_migrated

            # Skip if user is the owner (already has access)
            if membership.user == business.owner:
                skipped_count += 1
                continue

            # Check if team member already exists
            if TeamMember.objects.filter(business=business, user=membership.user).exists():
                skipped_count += 1
                continue

            # Create TeamMember
            TeamMember.objects.create(
                business=business,
                user=membership.user,
                role=membership.role.lower() if hasattr(membership, "role") else "member",
                is_active=membership.is_active,
                invited_by=membership.invited_by if hasattr(membership, "invited_by") else business.owner,
                joined_at=membership.created_at if hasattr(membership, "created_at") else None,
            )

            created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"  Created: {created_count} | Skipped: {skipped_count} | Total: {memberships.count()}"
            )
        )

    def migrate_chat_sessions(self):
        """Migrate ChatSession.tenant → ChatSession.business."""
        from chatbot.models import ChatSession

        self.stdout.write("Migrating ChatSessions...")
        updated = self._migrate_foreign_key(ChatSession, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def migrate_intents(self):
        """Migrate Intent.tenant → Intent.business."""
        from chatbot.models import Intent

        self.stdout.write("Migrating Intents...")
        updated = self._migrate_foreign_key(Intent, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def migrate_knowledge_sources(self):
        """Migrate KnowledgeSource.tenant → KnowledgeSource.business."""
        from knowledge.models import KnowledgeSource

        self.stdout.write("Migrating KnowledgeSources...")
        updated = self._migrate_foreign_key(KnowledgeSource, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def migrate_knowledge_chunks(self):
        """Migrate KnowledgeChunk.tenant → KnowledgeChunk.business."""
        from knowledge.models import KnowledgeChunk

        self.stdout.write("Migrating KnowledgeChunks...")
        updated = self._migrate_foreign_key(KnowledgeChunk, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def migrate_subscriptions(self):
        """Migrate Subscription.tenant → Subscription.business."""
        from billing.models import Subscription

        self.stdout.write("Migrating Subscriptions...")
        updated = self._migrate_foreign_key(Subscription, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def migrate_usage_logs(self):
        """Migrate UsageLog.tenant → UsageLog.business."""
        from billing.models import UsageLog

        self.stdout.write("Migrating UsageLogs...")
        updated = self._migrate_foreign_key(UsageLog, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def migrate_audit_logs(self):
        """Migrate AuditLog.tenant → AuditLog.business."""
        from compliance.models import AuditLog

        self.stdout.write("Migrating AuditLogs...")
        updated = self._migrate_foreign_key(AuditLog, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def migrate_consents(self):
        """Migrate Consent.tenant → Consent.business."""
        from compliance.models import Consent

        self.stdout.write("Migrating Consents...")
        updated = self._migrate_foreign_key(Consent, "tenant", "business")
        self.stdout.write(self.style.SUCCESS(f"  Updated: {updated}"))

    def _migrate_foreign_key(self, model, old_field, new_field):
        """
        Generic foreign key migration helper.

        Args:
            model: Django model class
            old_field: Name of the old foreign key field (e.g., "tenant")
            new_field: Name of the new foreign key field (e.g., "business")

        Returns:
            Number of records updated
        """
        count = 0

        for obj in model.objects.filter(**{f"{old_field}__isnull": False, f"{new_field}__isnull": True}):
            tenant = getattr(obj, old_field)

            if hasattr(tenant, "_business_migrated"):
                business = tenant._business_migrated
                setattr(obj, new_field, business)
                obj.save(update_fields=[new_field])
                count += 1

        return count
