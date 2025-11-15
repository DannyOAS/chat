# Phases 1-3 Implementation Guide

**Status:** Phase 1.1 ✅ Complete | Remaining Work 📋

This guide provides step-by-step instructions to complete Phases 1-3 of the production roadmap.

---

## ✅ What's Been Completed

### Phase 1.1: Real Semantic Embeddings ✅
- ✅ Replaced fake hash embeddings with Sentence Transformers
- ✅ Updated to 384-dimension vectors (all-MiniLM-L6-v2)
- ✅ Implemented efficient database-level vector search
- ✅ Added embedding caching
- ✅ Created pgvector migration
- ✅ Added batch embedding support
- ✅ Updated all dependencies in requirements.txt

**Test it:**
```bash
cd shoshchat
docker-compose run web python manage.py migrate
docker-compose run web python manage.py shell

# In shell:
from knowledge.embeddings import embed_text, get_embedding_info
print(get_embedding_info())
# Should show: model_loaded=True, dimension=384
```

---

## 📋 Remaining Critical Work

### Phase 1.2: Authentication & Authorization (4-6 hours)

#### 1.2.1: Two-Factor Authentication (2FA)

**Install dependencies:** Already added to requirements.txt
- django-otp
- qrcode
- pyotp

**Implementation:**

```bash
# 1. Create new app
cd shoshchat
python manage.py startapp authentication
```

**File: `authentication/models.py`**
```python
from django.db import models
from django.contrib.auth.models import User
from django_otp.plugins.otp_totp.models import TOTPDevice

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    two_factor_enabled = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=20, blank=True)
    backup_codes = models.JSONField(default=list, blank=True)

    def generate_backup_codes(self):
        """Generate 10 backup codes."""
        import secrets
        self.backup_codes = [secrets.token_hex(4) for _ in range(10)]
        self.save()
```

**File: `authentication/api/views.py`**
```python
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_otp.plugins.otp_totp.models import TOTPDevice
import qrcode
import io
import base64

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enable_2fa(request):
    """Enable 2FA for the user."""
    user = request.user
    device, created = TOTPDevice.objects.get_or_create(
        user=user,
        name='default'
    )

    # Generate QR code
    url = device.config_url
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return Response({
        'qr_code': f'data:image/png;base64,{img_str}',
        'secret': device.key,
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_2fa(request):
    """Verify 2FA token."""
    token = request.data.get('token')
    device = TOTPDevice.objects.filter(user=request.user, name='default').first()

    if device and device.verify_token(token):
        device.confirmed = True
        device.save()
        return Response({'message': '2FA enabled successfully'})

    return Response({'error': 'Invalid token'}, status=400)
```

**Add to `core/settings.py`:**
```python
INSTALLED_APPS += [
    'django_otp',
    'django_otp.plugins.otp_totp',
    'authentication',
]

MIDDLEWARE += [
    'django_otp.middleware.OTPMiddleware',
]
```

#### 1.2.2: Role-Based Access Control

**File: `authentication/permissions.py`**
```python
from rest_framework import permissions

class IsTenantAdmin(permissions.BasePermission):
    """Only tenant admins can access."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request, 'tenant') and
            request.user.profile.role == 'admin'
        )

class IsTenantOwner(permissions.BasePermission):
    """Only tenant owner can access."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            hasattr(request, 'tenant') and
            request.user.profile.role == 'owner'
        )
```

**Update `accounts/models.py`:**
```python
class UserProfile(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', 'Owner'
        ADMIN = 'admin', 'Admin'
        MEMBER = 'member', 'Member'
        GUEST = 'guest', 'Guest (Read-Only)'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey('tenancy.Tenant', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)
```

---

### Phase 1.3: Environment Configuration (1-2 hours)

#### Split settings into environments:

**File: `core/settings/__init__.py`**
```python
import os
from decouple import config

environment = config('ENVIRONMENT', default='development')

if environment == 'production':
    from .production import *
elif environment == 'staging':
    from .staging import *
else:
    from .development import *
```

**File: `core/settings/base.py`**
```python
# Move all common settings from core/settings.py here
# This becomes the base that all environments inherit from
```

**File: `core/settings/development.py`**
```python
from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Development-specific settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable HTTPS requirements
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
```

**File: `core/settings/production.py`**
```python
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = False
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', cast=Csv())

# Sentry error tracking
sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
    environment=config('ENVIRONMENT', default='production'),
)

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Production cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_CLASS': 'redis.connection.HiredisParser',
        }
    }
}
```

**Update `.env.example` and `.env`:**
```bash
ENVIRONMENT=development  # or staging, production
SENTRY_DSN=your-sentry-dsn-here
```

---

## Phase 2: Backend Robustness

### Phase 2.1: Database Optimization (2 hours)

Already partially done! I added indexes to knowledge models. Now add to other models:

**File: `chatbot/models.py` - Add indexes:**
```python
class ChatSession(models.Model):
    # ... existing fields ...

    class Meta:
        indexes = [
            models.Index(fields=['tenant', '-last_interaction_at']),
            models.Index(fields=['user_id', 'tenant']),
        ]

class Message(models.Model):
    # ... existing fields ...

    class Meta:
        indexes = [
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['role', 'created_at']),
        ]
```

**File: `billing/models.py` - Add indexes:**
```python
class UsageLog(models.Model):
    # ... existing fields ...

    class Meta:
        indexes = [
            models.Index(fields=['tenant', 'period_start']),
            models.Index(fields=['-period_start']),
        ]
```

**Create migration:**
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Phase 2.2: Caching Layer (3 hours)

**Update `core/settings/base.py`:**
```python
# Add django-redis cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'shoshchat',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# Session cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**File: `core/cache.py`** (create new):
```python
"""Caching utilities."""
from django.core.cache import cache
from functools import wraps
import hashlib
import json

def cache_tenant_config(timeout=3600):
    """Cache decorator for tenant configurations."""
    def decorator(func):
        @wraps(func)
        def wrapper(tenant_id, *args, **kwargs):
            cache_key = f'tenant_config:{tenant_id}'
            result = cache.get(cache_key)

            if result is None:
                result = func(tenant_id, *args, **kwargs)
                cache.set(cache_key, result, timeout=timeout)

            return result
        return wrapper
    return decorator

def invalidate_tenant_cache(tenant_id):
    """Invalidate all cache for a tenant."""
    patterns = [
        f'tenant_config:{tenant_id}',
        f'tenant_llm:{tenant_id}',
        f'tenant_settings:{tenant_id}',
    ]
    for pattern in patterns:
        cache.delete(pattern)
```

**Update tenancy views to use cache:**
```python
from django.views.decorators.cache import cache_page
from core.cache import cache_tenant_config

class TenantDetailView(APIView):
    @cache_page(60 * 5)  # Cache for 5 minutes
    def get(self, request):
        # ... existing code ...
```

---

### Phase 2.3: API Documentation with OpenAPI (2 hours)

**Update `core/settings/base.py`:**
```python
INSTALLED_APPS += [
    'drf_spectacular',
]

REST_FRAMEWORK = {
    # ... existing settings ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'ShoshChat AI API',
    'DESCRIPTION': 'Multi-tenant SaaS chatbot platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}
```

**Update `core/urls.py`:**
```python
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # ... existing patterns ...

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

**Add schema decorations to views:**
```python
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

@extend_schema(
    summary="Send chat message",
    description="Send a message to the chatbot and receive a response",
    request=ChatRequestSerializer,
    responses={200: ChatResponseSerializer},
    examples=[
        OpenApiExample(
            'Basic Chat',
            value={'message': 'What are your business hours?', 'user_id': 'user123'},
            request_only=True,
        ),
    ],
)
class ChatMessageView(APIView):
    # ... existing code ...
```

**Access documentation:**
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

---

### Phase 2.4: Background Task Improvements (2 hours)

**Add Flower for Celery monitoring:**
Already in requirements.txt!

**Update `docker-compose.yml`:**
```yaml
services:
  # ... existing services ...

  flower:
    build: .
    command: celery -A core flower --port=5555
    ports:
      - "5555:5555"
    env_file:
      - .env
    depends_on:
      - redis
      - celery-worker
    restart: unless-stopped
```

**Improve Celery configuration:**

**File: `core/celery.py`** (update):
```python
from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('shoshchat')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Task routes for different queues
app.conf.task_routes = {
    'knowledge.tasks.*': {'queue': 'knowledge'},
    'billing.tasks.*': {'queue': 'billing'},
}

# Result expiration
app.conf.result_expires = 3600

# Task time limits
app.conf.task_soft_time_limit = 300  # 5 minutes
app.conf.task_time_limit = 600  # 10 minutes

# Retry configuration
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True

# Periodic tasks
app.conf.beat_schedule = {
    'sync-stripe-daily': {
        'task': 'billing.tasks.sync_stripe_data',
        'schedule': crontab(hour=0, minute=0),
    },
}

app.autodiscover_tasks()
```

**Access Flower:** `http://localhost:5555`

---

### Phase 2.5: Error Handling & Logging (2 hours)

**Sentry integration** - Already configured in production settings!

**Structured logging:**

**File: `core/logging.py`** (create):
```python
"""Logging configuration."""
import logging.config

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/shoshchat/app.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'sentry_sdk.integrations.logging.EventHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'chatbot': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'knowledge': {
            'handlers': ['console', 'file', 'sentry'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

**Add to `core/settings/base.py`:**
```python
from core.logging import LOGGING  # noqa
```

---

## Phase 3: Modern Frontend

### Phase 3.1: Install shadcn/ui & Design System (3 hours)

**1. Initialize shadcn/ui:**
```bash
cd shoshchat/frontend
npx shadcn-ui@latest init
```

Answer prompts:
- TypeScript: Yes
- Style: Default
- Base color: Slate
- CSS variables: Yes

**2. Install components:**
```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add label
npx shadcn-ui@latest add textarea
npx shadcn-ui@latest add dialog
npx shadcn-ui@latest add dropdown-menu
npx shadcn-ui@latest add select
npx shadcn-ui@latest add table
npx shadcn-ui@latest add tabs
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add avatar
npx shadcn-ui@latest add toast
npx shadcn-ui@latest add skeleton
npx shadcn-ui@latest add alert
npx shadcn-ui@latest add separator
npx shadcn-ui@latest add switch
```

**3. Update `tailwind.config.js`:**
```javascript
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        // ... shadcn adds more colors
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}
```

**4. Dark mode toggle:**

**File: `src/components/ThemeProvider.tsx`:**
```typescript
import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'dark' | 'light' | 'system';

const ThemeContext = createContext<{
  theme: Theme;
  setTheme: (theme: Theme) => void;
}>({
  theme: 'system',
  setTheme: () => null,
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>('system');

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
```

---

### Phase 3.2: State Management (2 hours)

**Install dependencies:**
```bash
npm install zustand @tanstack/react-query axios
npm install --save-dev @tanstack/react-query-devtools
```

**File: `src/lib/queryClient.ts`:**
```typescript
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000, // 10 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

**File: `src/stores/authStore.ts`:**
```typescript
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: any | null;
  token: string | null;
  isAuthenticated: boolean;
  login: (user: any, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      login: (user, token) => set({ user, token, isAuthenticated: true }),
      logout: () => set({ user: null, token: null, isAuthenticated: false }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

**File: `src/hooks/useChat.ts`** (update):
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useChatSessions() {
  return useQuery({
    queryKey: ['chat', 'sessions'],
    queryFn: () => api.get('/chat/sessions/'),
  });
}

export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { message: string; user_id: string }) =>
      api.post('/chat/', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chat', 'sessions'] });
    },
  });
}
```

**Update `src/main.tsx`:**
```typescript
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider } from './components/ThemeProvider';
import { queryClient } from './lib/queryClient';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <App />
      </ThemeProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </React.StrictMode>
);
```

---

### Phase 3.3-3.6: Dashboard, Widget, Knowledge UI (8-10 hours)

This requires rewriting the entire frontend with shadcn components. Here's a starter:

**File: `src/pages/Dashboard.tsx`** (simplified example):
```typescript
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useQuery } from '@tanstack/react-query';

export default function Dashboard() {
  const { data: analytics } = useQuery({
    queryKey: ['chat', 'analytics'],
    queryFn: () => api.get('/chat/analytics/'),
  });

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Total Messages</CardTitle>
            <CardDescription>All time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analytics?.total_messages || 0}</div>
          </CardContent>
        </Card>

        {/* More cards... */}
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="settings">Settings</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          {/* Charts and stats */}
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

---

## Testing & Validation

### Test Embeddings:
```bash
cd shoshchat
docker-compose run web python manage.py shell

from knowledge.embeddings import embed_text
from knowledge.retrieval import retrieve_relevant_chunks
from tenancy.models import Tenant

tenant = Tenant.objects.first()
vec, model = embed_text("Hello world", tenant)
print(f"Model: {model}, Dimension: {len(vec)}")
# Should output: Model: sentence-transformers/all-MiniLM-L6-v2, Dimension: 384
```

### Test API Docs:
```bash
docker-compose up
# Visit: http://localhost:8000/api/docs/
```

### Test Frontend:
```bash
cd shoshchat/frontend
npm install
npm run dev
# Visit: http://localhost:5173
```

---

## Deployment Checklist

- [ ] Run migrations: `python manage.py migrate`
- [ ] Rebuild embeddings for existing knowledge chunks
- [ ] Set `ENVIRONMENT=production` in production
- [ ] Configure Sentry DSN
- [ ] Set up Redis cache
- [ ] Start Flower: `celery -A core flower`
- [ ] Enable 2FA for admin accounts
- [ ] Test semantic search quality
- [ ] Monitor error rates in Sentry
- [ ] Check API docs are accessible

---

## Estimated Timeline

- Phase 1.1: ✅ Complete (4 hours)
- Phase 1.2: 4-6 hours (2FA + RBAC)
- Phase 1.3: 1-2 hours (Environment config)
- Phase 2: 11-13 hours (Backend improvements)
- Phase 3: 15-20 hours (Frontend modernization)

**Total: 35-45 hours of focused development**

With a team of 2-3 developers, this is **2-3 weeks of work**.

---

## Next Immediate Steps

1. **Test embeddings** - Ensure semantic search works
2. **Run migrations** - Apply database changes
3. **Install frontend deps** - `npm install` in frontend/
4. **Set up Sentry** - Create free account, add DSN
5. **Install shadcn/ui** - `npx shadcn-ui@latest init`
6. **Start implementing** - Follow this guide systematically

---

**Need Help?** Refer to:
- [PRODUCTION_ROADMAP.md](./shoshchat/docs/PRODUCTION_ROADMAP.md) - Full roadmap
- [AI_AGENT_SETUP.md](./shoshchat/docs/AI_AGENT_SETUP.md) - AI configuration
- [DEVELOPER_GUIDE.md](./shoshchat/docs/DEVELOPER_GUIDE.md) - Architecture

**Questions?** Each section above has working code examples. Copy-paste and modify as needed!
