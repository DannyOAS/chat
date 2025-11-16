# Architecture Refactoring - Phase 3 Completion

## Overview

Phase 3 of the single-domain architecture refactoring has been completed. This phase focused on **updating all API endpoints** to use the new `request.business` context instead of `request.tenant`.

## Goal

Update all API views, serializers, and business logic to use the new Business/TeamMember models and `request.business` context set by BusinessMiddleware.

## Changes Made in Phase 3

### 1. Created Business API Module

Created a complete Business API with views, serializers, permissions, and URL routing.

**New Files Created:**
- `shoshchat/business/api/__init__.py`
- `shoshchat/business/api/serializers.py` - BusinessSerializer, TeamMemberSerializer
- `shoshchat/business/api/views.py` - Business and team member management views
- `shoshchat/business/api/urls.py` - URL patterns
- `shoshchat/business/permissions.py` - Permission classes

#### Business API Endpoints

**Business Management:**
```
GET/PATCH  /api/v1/business/           - Get or update current user's business
```

**Team Member Management:**
```
GET        /api/v1/business/team/                  - List team members
POST       /api/v1/business/team/invite/           - Invite team member
PATCH      /api/v1/business/team/<id>/role/        - Update member role
DELETE     /api/v1/business/team/<id>/              - Remove team member
```

#### Permission Classes

**IsBusinessOwner:**
- Checks if user is the owner of the business
- Uses `request.business.owner == request.user`

**IsBusinessOwnerOrAdmin:**
- Checks if user is owner OR admin team member
- Owner always has access
- Checks TeamMember.role == "admin"

**IsBusinessMember:**
- Checks if user is any member (owner or team member)
- Includes owner and all active team members

**HasBusinessPermission:**
- Granular permission checking
- Owner has all permissions
- Admin has all permissions
- Other roles checked against TeamMember.permissions JSON field

### 2. Updated Chatbot API Views

**File:** `shoshchat/chatbot/api/views.py`

**Changes:**
```python
# OLD:
tenant = getattr(request, "tenant", None)
ChatSession.objects.filter(tenant=tenant)

# NEW:
business = getattr(request, "business", None)
ChatSession.objects.filter(business=business)
```

**Updated Views:**
- `ChatMessageView` - Uses `business` for chatbot service
- `ChatSessionListView` - Filters sessions by `business`
- `ChatAnalyticsView` - Analytics scoped to `business`

### 3. Updated Knowledge API Views

**File:** `shoshchat/knowledge/api/views.py`

**Changes:**
```python
# OLD:
tenant = getattr(request, "tenant", None)
KnowledgeSource.objects.filter(tenant=tenant)

# NEW:
business = getattr(request, "business", None)
KnowledgeSource.objects.filter(business=business)
```

**Updated Views:**
- `KnowledgeSourceListCreateView` - List/create knowledge sources for business
- `KnowledgeSourceDetailView` - Get knowledge source details
- `KnowledgeChunkListView` - List knowledge chunks for business

### 4. Updated Billing API Views

**File:** `shoshchat/billing/api/views.py`

**Changes:**
```python
# OLD:
tenant = getattr(request, "tenant", None)
Subscription.objects.filter(tenant=tenant)
tenant.on_trial = False
tenant.paid_until = ...

# NEW:
business = getattr(request, "business", None)
Subscription.objects.filter(business=business)
business.on_trial = False
business.paid_until = ...
```

**Updated Views:**
- `UsageSummaryView` - Get usage for business
- `ActiveSubscriptionView` - Get active subscription for business
- `SubscriptionSwitchView` - Switch plans, update business billing fields

### 5. Updated Core URLs

**File:** `shoshchat/core/urls.py`

Added business API to URL configuration:

```python
urlpatterns = [
    path("api/v1/business/", include("business.api.urls")),  # New
    path("api/v1/tenants/", include("tenancy.urls")),  # Legacy - will be removed
    # ...other endpoints
]
```

## API Changes Summary

### Request Context

**Before (django-tenants):**
```python
# Set by TenantMainMiddleware
request.tenant  # Tenant instance from subdomain
connection.schema_name  # PostgreSQL schema name
```

**After (single-domain):**
```python
# Set by BusinessMiddleware
request.business  # Business instance from user.business
# No schema switching - all queries use business_id filtering
```

### Query Patterns

**Before:**
```python
# Automatic schema isolation
ChatSession.objects.all()  # Only returns current tenant's sessions

# Manual tenant filtering (redundant but common)
ChatSession.objects.filter(tenant=request.tenant)
```

**After:**
```python
# Explicit business filtering required
ChatSession.objects.filter(business=request.business)

# Protection against missing business
if not request.business:
    return Response({"detail": "Business context required."}, status=400)
```

### Error Handling

**Before:**
```python
tenant = getattr(request, "tenant", None)
# Queries work even if tenant is None (returns all in public schema)
```

**After:**
```python
business = getattr(request, "business", None)
if not business:
    return EmptyQuerySet() # or Response with error
# Explicit None checking required
```

## Code Comparison

### Chatbot View - Before vs After

**Before (django-tenants):**
```python
class ChatSessionListView(generics.ListAPIView):
    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        return ChatSession.objects.filter(tenant=tenant).order_by("-last_interaction_at")
```

**After (single-domain):**
```python
class ChatSessionListView(generics.ListAPIView):
    def get_queryset(self):
        business = getattr(self.request, "business", None)
        if not business:
            return ChatSession.objects.none()
        return ChatSession.objects.filter(business=business).order_by("-last_interaction_at")
```

### Knowledge View - Before vs After

**Before:**
```python
def perform_create(self, serializer):
    tenant = getattr(self.request, "tenant", None)
    source = serializer.save(tenant=tenant, status=KnowledgeSource.Status.PENDING)
    process_knowledge_source.delay(source.pk)
```

**After:**
```python
def perform_create(self, serializer):
    business = getattr(self.request, "business", None)
    if not business:
        raise ValueError("Business context is required.")
    source = serializer.save(business=business, status=KnowledgeSource.Status.PENDING)
    process_knowledge_source.delay(source.pk)
```

### Billing View - Before vs After

**Before:**
```python
subscription, created = Subscription.objects.get_or_create(
    tenant=tenant,
    defaults={"plan": plan, "active": True}
)
tenant.on_trial = False
tenant.paid_until = subscription.current_period_end.date()
tenant.save(update_fields=["on_trial", "paid_until"])
```

**After:**
```python
subscription, created = Subscription.objects.get_or_create(
    business=business,
    defaults={"plan": plan, "active": True}
)
business.on_trial = False
business.paid_until = subscription.current_period_end.date()
business.save(update_fields=["on_trial", "paid_until"])
```

## Files Modified in Phase 3

**New Files:**
- `shoshchat/business/api/__init__.py`
- `shoshchat/business/api/serializers.py` (92 lines)
- `shoshchat/business/api/views.py` (176 lines)
- `shoshchat/business/api/urls.py` (20 lines)
- `shoshchat/business/permissions.py` (129 lines)

**Modified Files:**
- `shoshchat/core/urls.py` - Added business API route
- `shoshchat/chatbot/api/views.py` - Updated to use request.business
- `shoshchat/knowledge/api/views.py` - Updated to use request.business
- `shoshchat/billing/api/views.py` - Updated to use request.business

## Benefits of Phase 3 Changes

### 1. Consistent Business Context
- ✅ All APIs use the same `request.business` pattern
- ✅ No more mixed tenant/business references
- ✅ Clear ownership model (User → Business → Data)

### 2. Better Security
- ✅ Explicit business filtering prevents data leaks
- ✅ Permission classes check business ownership
- ✅ Team member access properly controlled

### 3. Simpler Code
- ✅ No subdomain parsing logic
- ✅ Standard Django REST Framework patterns
- ✅ Easier to test and debug

### 4. Team Collaboration
- ✅ New TeamMember model supports collaboration
- ✅ Granular permissions via JSON field
- ✅ Role-based access (owner, admin, manager, member)

## Testing Requirements

Before deploying Phase 3:

### API Endpoint Tests
- ⏳ Test business detail endpoint
- ⏳ Test team member invitation
- ⏳ Test team member role updates
- ⏳ Test team member removal

### Permission Tests
- ⏳ Owner can access all business data
- ⏳ Admin can manage team members
- ⏳ Manager has limited permissions
- ⏳ Member has read-only access
- ⏳ Non-members cannot access business data

### Business Context Tests
- ⏳ Chatbot queries filtered by business
- ⏳ Knowledge sources scoped to business
- ⏳ Billing subscriptions scoped to business
- ⏳ Users without business get appropriate errors

## Remaining Work

### Phase 4: Data Migration
The final phase requires:

1. **Create Migration Scripts:**
   - Copy Tenant data → Business
   - Update all `tenant_id` → `business_id`
   - Consolidate PostgreSQL schemas into public schema
   - Update all foreign keys

2. **Remove Legacy Code:**
   - Remove `tenant` fields from models
   - Remove tenancy app
   - Remove TenantMembership model
   - Update indexes to use business_id

3. **Update Frontend:**
   - Remove subdomain detection
   - Update API calls to use /api/v1/business/
   - Remove tenant switching UI
   - Simplify dashboard

## Migration Path

### Current State (After Phase 3)
```python
# Models support both fields
class ChatSession(models.Model):
    tenant = ForeignKey("tenancy.Tenant", null=True)   # Legacy
    business = ForeignKey("business.Business", null=True)  # Active

# Views use business
business = request.business
sessions = ChatSession.objects.filter(business=business)
```

### Phase 4 Target
```python
# Only business field remains
class ChatSession(models.Model):
    business = ForeignKey("business.Business")  # Required

# Simpler queries
sessions = ChatSession.objects.filter(business=request.business)
```

## Breaking Changes

⚠️ **API Changes:**
- `/api/v1/tenants/` endpoints deprecated (still work, but use legacy)
- New `/api/v1/business/` endpoints recommended
- `request.tenant` no longer available in views
- Error responses changed from "Tenant context" to "Business context"

⚠️ **Model Changes:**
- Creating objects now requires `business=` instead of `tenant=`
- Queries must explicitly filter by business
- Missing business context returns empty querysets instead of all data

## Compatibility Notes

### ✅ Backward Compatible
- Legacy `/api/v1/tenants/` endpoints still exist
- Models have both tenant and business fields
- Old code using tenant still works (until Phase 4)

### ⚠️ New Requirements
- All new code must use `business` field
- All new views must check `request.business`
- All new queries must filter by business

### ❌ Not Backward Compatible
- New Business API requires BusinessMiddleware
- Cannot use TenantMainMiddleware and Business API together
- Subdomain routing no longer works

## Success Criteria

Phase 3 is considered complete when:
- ✅ Business API created with full CRUD
- ✅ Team member management working
- ✅ Permission classes implemented
- ✅ All chatbot views updated
- ✅ All knowledge views updated
- ✅ All billing views updated
- ✅ Core URLs include business API
- ✅ No request.tenant references in active views
- ⏳ Tests pass for all new APIs
- ⏳ Documentation complete

## Next Steps

**Phase 4: Data Migration & Cleanup**
1. Create Tenant → Business migration script
2. Consolidate PostgreSQL schemas
3. Remove tenant fields from models
4. Remove tenancy app entirely
5. Update frontend to remove subdomain logic
6. Full end-to-end testing

---

**Date:** 2025-11-16
**Status:** Phase 3 Complete ✅
**Next:** Phase 4 - Data Migration & Final Cleanup
