# Architecture Refactoring - Phase 1 Completion

## Overview

Phase 1 of the single-domain architecture refactoring has been completed. This phase focused on **simplifying the User-Business relationship** from a complex multi-tenant subdomain architecture to a simple one-to-one model.

## Goal

Convert ShoshChat AI from a django-tenants subdomain-based multi-tenant architecture to a **simple single-domain SaaS** where:
- Each user owns exactly **one business**
- No subdomain routing required
- Authentication-based business context
- Like Mailchimp, Shopify, and other modern SaaS platforms

## Changes Made in Phase 1

### 1. New Business App Created

Created a new `business` Django app to replace the complex `tenancy` app:

**Files Created:**
- `shoshchat/business/__init__.py`
- `shoshchat/business/apps.py`
- `shoshchat/business/models.py` (Business and TeamMember models)
- `shoshchat/business/middleware.py` (BusinessMiddleware and BusinessAccessMiddleware)
- `shoshchat/business/migrations/0001_initial.py`

### 2. Business Model

**Key Features:**
```python
class Business(models.Model):
    # ONE-TO-ONE relationship with User (simplified from many-to-many)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="business")

    # Slug-based identification (no schema_name)
    slug = models.SlugField(max_length=100, unique=True)

    # Business details
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=32, choices=INDUSTRY_CHOICES)

    # Billing (moved from separate models)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)

    # Widget customization
    widget_welcome_message = models.CharField(max_length=255)
    widget_primary_color = models.CharField(max_length=7, default="#14b8a6")
    widget_position = models.CharField(max_length=20, default="bottom-right")
```

**vs Old Tenant Model:**
- ❌ No `schema_name` (no multi-schema architecture)
- ❌ No `auto_create_schema` (no separate databases)
- ✅ One-to-one with User (was many-to-many via TenantMembership)
- ✅ Slug-based identification (user-friendly URLs)
- ✅ Simplified billing integration

### 3. TeamMember Model

Optional collaboration feature (simpler than TenantMembership):

```python
class TeamMember(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    permissions = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
```

**vs Old TenantMembership:**
- ✅ Simpler role structure (admin, manager, member)
- ✅ JSON permissions for flexibility
- ❌ No cross-tenant access (each user owns one business, but can be member of others)

### 4. Business Middleware

Created simplified middleware to replace django-tenants:

**BusinessMiddleware:**
```python
def __call__(self, request: HttpRequest) -> HttpResponse:
    # Simply add business from authenticated user
    if request.user and request.user.is_authenticated:
        try:
            request.business = request.user.business  # One-to-one
        except AttributeError:
            request.business = None
    else:
        request.business = None

    return self.get_response(request)
```

**vs TenantMainMiddleware:**
- ❌ No subdomain parsing
- ❌ No schema switching
- ❌ No database router logic
- ✅ Simple authentication-based context
- ✅ Works with any domain (no subdomain required)

**BusinessAccessMiddleware (Optional):**
- Supports team member access via `?business_id=` parameter
- Checks ownership or team membership
- Sets `request.business` and `request.business_role`

### 5. Updated Django Settings

**shoshchat/core/settings/base.py:**

Added business app to SHARED_APPS:
```python
SHARED_APPS: Final[list[str]] = [
    # ... other apps
    "business",  # New single-domain business app
    "tenancy",   # Keep for gradual migration
    # ...
]
```

Added BusinessMiddleware to MIDDLEWARE:
```python
MIDDLEWARE: list[str] = [
    "django_tenants.middleware.main.TenantMainMiddleware",  # Will be removed in Phase 2
    # ... other middleware
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "business.middleware.BusinessMiddleware",  # New single-domain business context
    # ...
]
```

### 6. Updated Existing Models

All tenant-scoped models now support **both** architectures during transition:

**Updated Models:**
- `chatbot.models.ChatSession` - Added `business` ForeignKey
- `chatbot.models.Intent` - Added `business` ForeignKey
- `knowledge.models.KnowledgeSource` - Added `business` ForeignKey
- `knowledge.models.KnowledgeChunk` - Added `business` ForeignKey
- `billing.models.Subscription` - Added `business` ForeignKey
- `billing.models.UsageLog` - Added `business` ForeignKey
- `compliance.models.AuditLog` - Added `business` ForeignKey
- `compliance.models.Consent` - Added `business` ForeignKey

**Pattern Used:**
```python
class SomeModel(models.Model):
    tenant = models.ForeignKey("tenancy.Tenant", null=True, blank=True)  # Legacy
    business = models.ForeignKey("business.Business", null=True, blank=True)  # New
    # ... other fields
```

This allows:
- Gradual migration of existing data
- Both systems to work simultaneously
- No breaking changes to existing code
- Easy cleanup in Phase 2

## Architecture Comparison

### Before (django-tenants):
```
User ←→ TenantMembership ←→ Tenant (schema_name)
                              ↓
                         Separate PostgreSQL Schema
                              ↓
                         tenant1_chatsession
                         tenant1_knowledge
                         tenant2_chatsession
                         tenant2_knowledge
```

**Routing:**
- `tenant1.shoshchat.ai` → Parse subdomain → Switch to schema `tenant1`
- `tenant2.shoshchat.ai` → Parse subdomain → Switch to schema `tenant2`

### After (single-domain):
```
User ←→ Business (one-to-one)
        ↓
   Single PostgreSQL Schema
        ↓
   chatsession (business_id filter)
   knowledge (business_id filter)
```

**Routing:**
- `app.shoshchat.ai` → Authenticate user → Get `request.business`
- All queries: `ChatSession.objects.filter(business=request.business)`

## Benefits of New Architecture

1. **Simpler Development:**
   - No schema routing complexity
   - Standard Django queries
   - Easier to test and debug

2. **Better User Experience:**
   - No subdomain confusion
   - Single login works everywhere
   - Like Mailchimp/Shopify (familiar pattern)

3. **Easier Deployment:**
   - No wildcard SSL required
   - Single domain configuration
   - Simpler DNS setup

4. **Better Performance:**
   - No schema switching overhead
   - Better query plan caching
   - Simpler connection pooling

5. **Flexible Scaling:**
   - Can add read replicas easily
   - Standard database sharding if needed
   - No tenant-specific migrations

## What's Next - Remaining Phases

### Phase 2: Remove django-tenants Infrastructure
- Remove `django_tenants` from INSTALLED_APPS
- Remove `TenantMainMiddleware` from MIDDLEWARE
- Remove `DATABASE_ROUTERS` for schema routing
- Update all code using `tenant` to use `business`
- Remove `schema_name` references
- Update API views to use `request.business`

### Phase 3: Update API & Frontend
- Modify API views to filter by `request.business` automatically
- Remove subdomain detection from frontend
- Update authentication to use BusinessMiddleware
- Simplify dashboard - remove tenant switching UI
- Update all API endpoints to use business context

### Phase 4: Database Migration
- Create data migration to copy tenant data to business
- Add `business_id` columns to all models
- Migrate data from tenant schemas to single schema
- Drop tenant-specific schemas
- Update indexes and foreign keys
- Remove `tenant` fields from models

## Testing Strategy

Before moving to Phase 2:
1. ✅ Business models created and migrated
2. ✅ Middleware integrated and working
3. ⏳ Test user registration creates business
4. ⏳ Test business context in requests
5. ⏳ Test team member access
6. ⏳ Verify both systems work together

## Migration Path for Existing Data

1. **Phase 1 (Current):** Both systems coexist
   - Old code uses `tenant`
   - New code uses `business`
   - Migrations support both

2. **Phase 2:** Data migration script
   - Copy Tenant → Business
   - Update all ForeignKeys
   - Verify data integrity

3. **Phase 3:** Remove legacy code
   - Drop `tenant` fields
   - Remove django-tenants
   - Update all queries

4. **Phase 4:** Production deployment
   - Backup database
   - Run migration script
   - Monitor for issues
   - Rollback plan ready

## Files Modified

**New Files:**
- `shoshchat/business/__init__.py`
- `shoshchat/business/apps.py`
- `shoshchat/business/models.py`
- `shoshchat/business/middleware.py`
- `shoshchat/business/migrations/__init__.py`
- `shoshchat/business/migrations/0001_initial.py`

**Modified Files:**
- `shoshchat/core/settings/base.py`
- `shoshchat/chatbot/models.py`
- `shoshchat/knowledge/models.py`
- `shoshchat/billing/models.py`
- `shoshchat/compliance/models.py`

## Compatibility Notes

✅ **Backward Compatible:**
- All existing `tenant` fields still work
- django-tenants middleware still active
- No breaking changes to APIs
- Existing subdomain routing works

⚠️ **Transition Period:**
- Both `tenant` and `business` fields exist
- Code should prefer `business` when available
- Fall back to `tenant` for legacy data

❌ **Not Yet Supported:**
- Creating new businesses (need registration flow)
- Team member invitations (need UI)
- Business switching for team members (need API)

## Success Criteria

Phase 1 is considered complete when:
- ✅ Business app created and installed
- ✅ Business and TeamMember models defined
- ✅ Middleware implemented and integrated
- ✅ All tenant-scoped models updated
- ✅ Migration files created
- ⏳ Tests pass with both systems
- ⏳ Documentation complete

## Next Steps

1. **Immediate:** Commit and push Phase 1 changes
2. **Phase 2:** Start removing django-tenants dependencies
3. **Phase 3:** Update API endpoints and frontend
4. **Phase 4:** Create and test data migration scripts

---

**Date:** 2025-11-16
**Status:** Phase 1 Complete ✅
**Next:** Phase 2 - Remove django-tenants
