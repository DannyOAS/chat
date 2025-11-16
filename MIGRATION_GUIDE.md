# ShoshChat AI - Tenant to Business Migration Guide

## Overview

This guide provides step-by-step instructions for migrating ShoshChat AI from the django-tenants multi-schema architecture to the single-domain business architecture.

## Prerequisites

### Backup Database
```bash
# PostgreSQL backup
pg_dump -U shoshchat -d shoshchat_prod > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql

# Or using Docker
docker exec postgres pg_dump -U shoshchat shoshchat_prod > backup_before_migration_$(date +%Y%m%d_%H%M%S).sql
```

### Verify Current State
```bash
# Check Django version
python manage.py --version

# Check all migrations are applied
python manage.py showmigrations

# Count existing tenants
python manage.py shell -c "from tenancy.models import Tenant; print(f'Tenants: {Tenant.objects.count()}')"
```

## Migration Steps

### Step 1: Deploy Code (Phases 1-3)

The code changes from Phases 1-3 are already deployed and backward compatible.

**Verify:**
```bash
# Check Business app is installed
python manage.py check business

# Check BusinessMiddleware is active
python manage.py shell -c "from django.conf import settings; print('BusinessMiddleware' in str(settings.MIDDLEWARE))"
```

### Step 2: Dry Run Migration

Test the migration without making changes:

```bash
cd shoshchat
python manage.py migrate_tenant_to_business --dry-run
```

**Expected Output:**
```
Running in DRY-RUN mode - no changes will be saved
Migrating Tenants → Businesses...
  ✓ Created Business: Example Corp (slug: example-corp)
  ✓ Created Business: Acme Inc (slug: acme-inc)
  Created: 25 | Skipped: 0 | Total: 25
Migrating TenantMemberships → TeamMembers...
  Created: 47 | Skipped: 25 | Total: 72
Migrating ChatSessions...
  Updated: 1,234
Migrating KnowledgeSources...
  Updated: 456
...
✅ DRY-RUN validation passed
```

**Review Output:**
- All tenants have owners
- No errors or warnings
- Counts match expectations

### Step 3: Run Actual Migration

**IMPORTANT:** This step modifies the database. Ensure backup is complete.

```bash
# Run migration
python manage.py migrate_tenant_to_business

# Expected: ✅ Migration completed successfully!
```

### Step 4: Verify Data Migration

```bash
# Check businesses created
python manage.py shell -c "from business.models import Business; print(f'Businesses: {Business.objects.count()}')"

# Check team members migrated
python manage.py shell -c "from business.models import TeamMember; print(f'Team Members: {TeamMember.objects.count()}')"

# Verify ChatSessions have business
python manage.py shell -c "from chatbot.models import ChatSession; print(f'Sessions with business: {ChatSession.objects.filter(business__isnull=False).count()}')"

# Verify all foreign keys updated
python manage.py check_migration_completeness  # Custom command (optional)
```

### Step 5: Deploy Model Changes (Make business required)

Create and run migrations to make business field required:

```bash
# This will be done via Django migrations in the next commit
# The migrations will:
# 1. Make business field required (NOT NULL)
# 2. Remove tenant field
# 3. Update indexes
```

### Step 6: Restart Application

```bash
# Docker
docker-compose restart web

# Or systemd
systemctl restart shoshchat

# Or Gunicorn
supervisorctl restart shoshchat
```

### Step 7: Verify Application

**Test Key Endpoints:**
```bash
# Health check
curl http://localhost:8000/healthz

# Business API
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/business/

# Chat API
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/chat/sessions/

# Knowledge API
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/knowledge/
```

**Test User Flows:**
1. User login
2. View business dashboard
3. Create chat session
4. Upload knowledge source
5. Invite team member
6. View billing/usage

### Step 8: Monitor for Issues

Monitor logs for errors:

```bash
# Docker logs
docker-compose logs -f web

# Or application logs
tail -f logs/django.log

# Check for errors
grep -i error logs/django.log | tail -50
```

**Watch for:**
- `AttributeError: 'NoneType' object has no attribute 'tenant'`
- `IntegrityError` related to tenant/business
- API endpoints returning empty data
- Permission errors

## Rollback Procedure

If issues are encountered, rollback is possible before Step 5:

### Immediate Rollback (Before Model Changes)

```bash
# 1. Restore database backup
psql -U shoshchat -d shoshchat_prod < backup_before_migration_YYYYMMDD_HHMMSS.sql

# 2. Restart application
docker-compose restart web

# 3. Verify old architecture works
curl http://tenant1.shoshchat.ai/api/v1/chat/sessions/
```

### After Model Changes

Rollback becomes more complex. Options:

1. **Restore Full Backup:**
   ```bash
   # Drop and recreate database
   dropdb shoshchat_prod
   createdb shoshchat_prod
   psql -U shoshchat -d shoshchat_prod < backup_before_migration_YYYYMMDD_HHMMSS.sql
   ```

2. **Reverse Migrations:**
   ```bash
   # Revert migrations (if possible)
   python manage.py migrate business 0001_initial
   python manage.py migrate chatbot XXXX_previous_migration
   # etc. for each app
   ```

## Post-Migration Tasks

### 1. Remove Legacy Code

After confirming migration success:

```bash
# Remove tenancy app from INSTALLED_APPS
# Remove /api/v1/tenants/ URL pattern
# Remove unused tenant-related code
```

### 2. Update Frontend

```bash
# Remove subdomain detection
# Update API endpoints from /tenants/ to /business/
# Remove tenant switching UI
# Update dashboard routing
```

### 3. Clean Up Database

```bash
# Drop tenant schemas (after confirming not needed)
python manage.py drop_tenant_schemas  # Custom command

# Optimize database
python manage.py vacuum_db  # Custom command
```

### 4. Update Documentation

- Update API documentation
- Update deployment guides
- Update developer setup instructions
- Update user guides

## Troubleshooting

### Issue: Migration fails with "Tenant has no owner"

**Solution:**
```python
# In Django shell
from tenancy.models import Tenant
from accounts.models import User

# Find tenant without owner
tenant = Tenant.objects.get(id=TENANT_ID)

# Assign owner
membership = tenant.memberships.filter(is_active=True).first()
if membership:
    tenant.owner = membership.user
    tenant.save()
```

### Issue: Duplicate slug errors

**Solution:**
The migration automatically handles this by appending numbers. If manual intervention needed:

```python
from business.models import Business

# Find duplicate
business = Business.objects.get(slug='example')

# Update slug
business.slug = 'example-2'
business.save()
```

### Issue: Some data still has null business

**Solution:**
```python
# Find records without business
from chatbot.models import ChatSession

orphaned = ChatSession.objects.filter(business__isnull=True, tenant__isnull=False)

# Re-run migration for specific records
for session in orphaned:
    if hasattr(session.tenant, '_business_migrated'):
        session.business = session.tenant._business_migrated
        session.save()
```

### Issue: Permission denied errors

**Solution:**
Check BusinessMiddleware is setting request.business:

```python
# In views, add debugging
print(f"Business: {request.business}")
print(f"User: {request.user}")

# Ensure user has business
if not request.user.business:
    # User needs to create business
```

## Testing Checklist

After migration, verify:

- [ ] All users can login
- [ ] Users can see their business dashboard
- [ ] Chat sessions are accessible
- [ ] Knowledge sources are visible
- [ ] Team members can be invited
- [ ] Billing information is correct
- [ ] Analytics data is accurate
- [ ] No 404 or 500 errors in logs
- [ ] Database queries are efficient
- [ ] Performance is acceptable
- [ ] Backup and restore procedures work

## Performance Optimization

After migration:

```bash
# Rebuild indexes
python manage.py sqlsequencereset chatbot knowledge billing compliance | python manage.py dbshell

# Update statistics
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('ANALYZE;')"

# Vacuum database
# For PostgreSQL
psql -U shoshchat -d shoshchat_prod -c "VACUUM ANALYZE;"
```

## Support

If you encounter issues not covered in this guide:

1. Check logs: `logs/django.log`, `logs/celery.log`
2. Review code changes in ARCHITECTURE_REFACTORING_PHASE*.md
3. Run dry-run again: `python manage.py migrate_tenant_to_business --dry-run`
4. Check database state in Django shell
5. Restore from backup if necessary

## Timeline

Recommended migration schedule:

1. **Week 1:** Deploy code (Phases 1-3), test in staging
2. **Week 2:** Run dry-run in production, identify issues
3. **Week 3:** Scheduled maintenance window for actual migration
4. **Week 4:** Monitor, optimize, clean up legacy code

## Success Criteria

Migration is successful when:

✅ All data migrated (Tenant → Business)
✅ All foreign keys updated
✅ No errors in application logs
✅ All API endpoints working
✅ Users can access their data
✅ Team collaboration working
✅ Performance is acceptable or better
✅ Backup and rollback tested

---

**Last Updated:** 2025-11-16
**Migration Version:** Phase 4
**Document Version:** 1.0
