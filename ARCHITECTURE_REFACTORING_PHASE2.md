# Architecture Refactoring - Phase 2 Completion

## Overview

Phase 2 of the single-domain architecture refactoring has been completed. This phase focused on **removing django-tenants infrastructure** from the Django settings and configuration.

## Goal

Remove all django-tenants dependencies and configuration to complete the transition to a standard Django single-domain architecture.

## Changes Made in Phase 2

### 1. Removed django-tenants from INSTALLED_APPS

**Before:**
```python
SHARED_APPS: Final[list[str]] = [
    "django_tenants",
    # ...other apps
]

TENANT_APPS: Final[list[str]] = [
    # ...tenant-specific apps
]

INSTALLED_APPS: list[str] = list(dict.fromkeys(SHARED_APPS + TENANT_APPS))
```

**After:**
```python
# Single-domain architecture - no more SHARED_APPS/TENANT_APPS split
INSTALLED_APPS: Final[list[str]] = [
    # Django core apps
    "django.contrib.contenttypes",
    # ...
    # ShoshChat apps
    "business",  # Single-domain business management
    "tenancy",   # Legacy - kept temporarily for data migration
    # ...
]
```

**Changes:**
- ✅ Removed `django_tenants` from installed apps
- ✅ Removed SHARED_APPS/TENANT_APPS split
- ✅ Unified into single INSTALLED_APPS list
- ⚠️ Kept `tenancy` app temporarily for data migration

### 2. Removed Tenant-Specific Settings

**Removed Settings:**
```python
# REMOVED:
TENANT_MODEL: Final[str] = "tenancy.Tenant"
TENANT_DOMAIN_MODEL: Final[str] = "tenancy.Domain"
PUBLIC_SCHEMA_URLCONF: Final[str] = "core.urls"
DATABASE_ROUTERS: Final[list[str]] = ["django_tenants.routers.TenantSyncRouter"]
```

**Why:**
- No more schema-based routing
- No tenant model configuration needed
- Single URL configuration for all requests
- No database routers for schema switching

### 3. Removed TenantMainMiddleware

**Before:**
```python
MIDDLEWARE: list[str] = [
    "django_tenants.middleware.main.TenantMainMiddleware",  # Subdomain → schema
    # ...
    "business.middleware.BusinessMiddleware",
]
```

**After:**
```python
MIDDLEWARE: list[str] = [
    # Removed TenantMainMiddleware (Phase 2: Single-domain architecture)
    "django.middleware.security.SecurityMiddleware",
    # ...
    "business.middleware.BusinessMiddleware",  # Single-domain business context
]
```

**Impact:**
- ❌ No more subdomain parsing
- ❌ No more schema switching per request
- ✅ Only BusinessMiddleware for auth-based context

### 4. Changed Database Engine

**Before:**
```python
DATABASES: dict[str, dict[str, str]] = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",  # Multi-schema support
        # ...
    }
}
```

**After:**
```python
DATABASES: dict[str, dict[str, str]] = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # Standard PostgreSQL
        # Connection pooling and performance settings
        "CONN_MAX_AGE": 600,
        "ATOMIC_REQUESTS": True,
        "OPTIONS": {
            "connect_timeout": 10,
        },
    }
}
```

**Benefits:**
- ✅ Standard Django PostgreSQL backend
- ✅ No schema-switching overhead
- ✅ Better connection pooling
- ✅ Simpler database configuration

### 5. Updated requirements.txt

**Removed:**
```python
django-tenants>=3.5
```

**Reason:**
- No longer needed for single-domain architecture
- Removes unnecessary dependency
- Simplifies deployment

## Architecture Comparison

### Database Schema Structure

**Before (django-tenants):**
```
PostgreSQL Database: shoshchat
├── public (shared schema)
│   ├── auth_user
│   ├── tenancy_tenant
│   └── tenancy_domain
├── tenant1 (isolated schema)
│   ├── chatbot_chatsession
│   ├── knowledge_knowledgesource
│   └── billing_subscription
└── tenant2 (isolated schema)
    ├── chatbot_chatsession
    ├── knowledge_knowledgesource
    └── billing_subscription
```

**After (single-domain):**
```
PostgreSQL Database: shoshchat
└── public (single schema)
    ├── auth_user
    ├── business_business
    ├── chatbot_chatsession (with business_id)
    ├── knowledge_knowledgesource (with business_id)
    └── billing_subscription (with business_id)
```

### Request Flow

**Before (django-tenants):**
```
Request: tenant1.shoshchat.ai
    ↓
TenantMainMiddleware
    ↓ Parse subdomain "tenant1"
    ↓ Find Tenant with domain "tenant1.shoshchat.ai"
    ↓ Switch PostgreSQL schema to "tenant1"
    ↓ Set connection.tenant
    ↓
View
    ↓ Query ChatSession.objects.all()
    ↓ Returns only tenant1's sessions (schema-isolated)
```

**After (single-domain):**
```
Request: app.shoshchat.ai
    ↓
BusinessMiddleware
    ↓ Get request.user (AuthenticationMiddleware)
    ↓ Get request.user.business (one-to-one)
    ↓ Set request.business
    ↓
View
    ↓ Query ChatSession.objects.filter(business=request.business)
    ↓ Returns only user's business sessions (filter-isolated)
```

## Benefits of Phase 2 Changes

### 1. Simplified Configuration
- ✅ No more SHARED_APPS/TENANT_APPS complexity
- ✅ Standard Django settings
- ✅ Easier to understand and maintain
- ✅ No tenant-specific routing

### 2. Better Performance
- ✅ No schema switching overhead on every request
- ✅ Better query plan caching (single schema)
- ✅ Simpler database connections
- ✅ Standard PostgreSQL optimizations work

### 3. Easier Development
- ✅ Standard Django development workflow
- ✅ No special database backend
- ✅ Works with all Django tools out of the box
- ✅ Simpler debugging (no schema confusion)

### 4. Simpler Deployment
- ✅ No wildcard SSL needed
- ✅ Single domain configuration
- ✅ Standard PostgreSQL setup
- ✅ No subdomain DNS configuration

### 5. Better Scalability
- ✅ Can use standard read replicas
- ✅ Can shard by business_id if needed
- ✅ Standard PostgreSQL scaling patterns
- ✅ No schema-count limits

## Remaining Work

### Phase 3: Update API Endpoints
The following files still reference `request.tenant` and need to be updated:

**accounts/api/views.py:**
- Line 213: `tenant = self.request.tenant` (TenantMembersView)
- Line 234: `tenant = request.tenant` (InviteMemberView)
- Line 244: `tenant=tenant` (TenantMembership filter)
- Line 252: `tenant=tenant` (TenantMembership create)
- Line 270: `tenant = request.tenant` (UpdateMemberRoleView)
- Line 310: `tenant = request.tenant` (RemoveMemberView)

**Action Required:** Update these to use `request.business` and `Business`/`TeamMember` models.

### Phase 4: Data Migration
- Create migration script to copy Tenant → Business
- Add business_id to all tenant-scoped data
- Drop tenant schemas (keep only public)
- Remove tenant ForeignKey fields
- Update indexes

## Compatibility Notes

### ✅ Backward Compatible (for now)
- Tenancy app still installed (for data migration)
- Tenant models still exist
- Legacy code can still import from tenancy

### ⚠️ Breaking Changes
- django-tenants package removed from requirements
- Subdomain routing no longer works
- Schema switching no longer works
- request.tenant not set by middleware

### ❌ Not Yet Working
- API views that use `request.tenant` (Phase 3)
- Frontend subdomain routing (Phase 3)
- Tenant member management (Phase 3 - needs Business/TeamMember)

## Migration Path

### Current State (After Phase 2)
```python
# Settings configured for single-domain
INSTALLED_APPS = [..., "business", "tenancy", ...]  # Both exist
MIDDLEWARE = [..., "BusinessMiddleware"]            # Only BusinessMiddleware

# Models support both
class ChatSession(models.Model):
    tenant = ForeignKey("tenancy.Tenant", null=True)   # Legacy
    business = ForeignKey("business.Business", null=True)  # New
```

### Phase 3 (Next)
```python
# Update API views
# OLD:
tenant = request.tenant
sessions = ChatSession.objects.filter(tenant=tenant)

# NEW:
business = request.business
sessions = ChatSession.objects.filter(business=business)
```

### Phase 4 (Final)
```python
# Remove legacy fields
class ChatSession(models.Model):
    # tenant = ...  # REMOVED
    business = ForeignKey("business.Business")  # Required

# Remove tenancy app
INSTALLED_APPS = [..., "business", ...]  # No more tenancy
```

## Testing Checklist

Before moving to Phase 3:
- ✅ Django starts without errors
- ✅ Settings loaded correctly
- ✅ BusinessMiddleware sets request.business
- ⏳ User can register and create business
- ⏳ Business context works in API views
- ⏳ No schema-switching errors
- ⏳ Standard Django queries work

## Files Modified in Phase 2

**Modified Files:**
- `shoshchat/core/settings/base.py`
  - Removed django_tenants from INSTALLED_APPS
  - Unified SHARED_APPS/TENANT_APPS → INSTALLED_APPS
  - Removed TENANT_MODEL, TENANT_DOMAIN_MODEL
  - Removed PUBLIC_SCHEMA_URLCONF
  - Removed TenantMainMiddleware from MIDDLEWARE
  - Changed DATABASE engine to standard postgresql
  - Removed DATABASE_ROUTERS
  - Added connection pooling settings

- `shoshchat/requirements.txt`
  - Removed django-tenants>=3.5

**Unchanged (Intentionally):**
- `shoshchat/tenancy/models.py` - Kept for data migration
- `shoshchat/tenancy/routers.py` - Kept for reference
- `shoshchat/accounts/api/views.py` - Will update in Phase 3
- All model files with both tenant/business fields

## Success Criteria

Phase 2 is considered complete when:
- ✅ django-tenants removed from INSTALLED_APPS
- ✅ django-tenants removed from requirements.txt
- ✅ TenantMainMiddleware removed from MIDDLEWARE
- ✅ DATABASE engine changed to standard postgresql
- ✅ DATABASE_ROUTERS removed
- ✅ TENANT_MODEL and TENANT_DOMAIN_MODEL removed
- ✅ PUBLIC_SCHEMA_URLCONF removed
- ✅ Only BusinessMiddleware remains
- ✅ Configuration simplified and documented

## Next Steps

1. **Phase 3: Update API Endpoints**
   - Replace `request.tenant` with `request.business`
   - Update TenantMembership views to use TeamMember
   - Update all queries to filter by business
   - Remove subdomain routing from frontend
   - Test API endpoints work with business context

2. **Phase 4: Data Migration**
   - Create Tenant → Business migration script
   - Copy existing tenant data to business
   - Update all tenant foreign keys to business
   - Drop tenant schemas
   - Remove legacy tenant fields
   - Remove tenancy app

---

**Date:** 2025-11-16
**Status:** Phase 2 Complete ✅
**Next:** Phase 3 - Update API & Frontend
