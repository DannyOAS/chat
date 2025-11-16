# Performance Optimization Guide

**ShoshChat AI - Performance & Scalability Documentation**

This guide covers performance optimization techniques, scalability strategies, and best practices for running ShoshChat AI at scale.

---

## Table of Contents

1. [Performance Goals](#performance-goals)
2. [Frontend Performance](#frontend-performance)
3. [Backend Performance](#backend-performance)
4. [Database Optimization](#database-optimization)
5. [Caching Strategies](#caching-strategies)
6. [Scalability](#scalability)
7. [Monitoring & Profiling](#monitoring--profiling)
8. [Performance Checklist](#performance-checklist)

---

## Performance Goals

### Target Metrics

- **API Response Time**: p95 < 200ms, p99 < 500ms
- **Initial Page Load**: < 2 seconds
- **Time to Interactive**: < 3 seconds
- **Lighthouse Score**: > 90
- **Database Queries**: < 10 per request
- **Cache Hit Rate**: > 80%
- **Concurrent Users**: 10,000+
- **Messages per Day**: 100,000+

---

## Frontend Performance

### 1. Code Splitting and Lazy Loading

**Implemented in**: `shoshchat/frontend/vite.config.ts`

```typescript
// Lazy load routes
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Knowledge = lazy(() => import('./pages/Knowledge'));

// Wrap in Suspense
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/dashboard" element={<Dashboard />} />
  </Routes>
</Suspense>
```

**Benefits**:
- Reduces initial bundle size by 60-70%
- Faster initial load time
- Better caching strategy

### 2. Bundle Optimization

**Vite Configuration Features**:

- **Manual Chunking**: Separate vendor bundles for React, UI components, state management
- **Tree Shaking**: Removes unused code automatically
- **Minification**: Terser for production builds
- **Compression**: Gzip and Brotli compression
- **Console Removal**: Removes console.* calls in production

**Bundle Size Targets**:
- Main bundle: < 200 KB (gzipped)
- Vendor bundle: < 300 KB (gzipped)
- Total initial load: < 500 KB (gzipped)

### 3. Image Optimization

**Best Practices**:

```jsx
// Use WebP format
<img src="image.webp" alt="..." />

// Lazy load images
<img loading="lazy" src="..." alt="..." />

// Responsive images
<img
  srcSet="image-320.webp 320w, image-640.webp 640w, image-1280.webp 1280w"
  sizes="(max-width: 640px) 320px, (max-width: 1280px) 640px, 1280px"
  src="image-640.webp"
  alt="..."
/>
```

### 4. React Performance

**Optimization Techniques**:

```typescript
// 1. Memoization
const MemoizedComponent = React.memo(ExpensiveComponent);

// 2. useMemo for expensive calculations
const expensiveValue = useMemo(() => {
  return calculateExpensiveValue(data);
}, [data]);

// 3. useCallback for stable function references
const handleClick = useCallback(() => {
  doSomething(id);
}, [id]);

// 4. Virtual scrolling for long lists
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={1000}
  itemSize={50}
  width="100%"
>
  {Row}
</FixedSizeList>
```

### 5. Build Analysis

**Analyze Bundle Size**:

```bash
# Build with analysis
npm run build:analyze

# View report
npm run build:report

# Run Lighthouse
npm run lighthouse
```

---

## Backend Performance

### 1. Caching

**Implemented in**: `shoshchat/core/performance.py`

**Function-Level Caching**:

```python
from core.performance import cached

# Cache for 5 minutes
@cached(timeout=300, key_prefix='user_profile')
def get_user_profile(user_id):
    return UserProfile.objects.get(user_id=user_id)

# Invalidate cache
get_user_profile.invalidate(user_id=123)

# Pre-configured decorators
from core.performance import cache_5min, cache_15min, cache_1hour, cache_1day

@cache_1hour
def expensive_computation():
    return calculate_something()
```

**Cached Property**:

```python
from core.performance import cached_property_with_ttl

class MyModel(models.Model):
    @cached_property_with_ttl(ttl=600)
    def expensive_property(self):
        return expensive_calculation()
```

### 2. Query Optimization

**Implemented in**: `shoshchat/core/performance.py`

**Select Related / Prefetch Related**:

```python
from core.performance import QueryOptimizer

# Optimize queryset
users = QueryOptimizer.optimize_queryset(
    User.objects.all(),
    select_related=['profile', 'tenant'],
    prefetch_related=['permissions', 'groups']
)

# Count queries in a function
@QueryOptimizer.count_queries
def my_view(request):
    # This will log the number of queries executed
    users = User.objects.all()
    for user in users:
        print(user.profile.bio)  # Would cause N+1 without select_related
```

**Bulk Operations**:

```python
from core.performance import bulk_create_optimized, batch_update_optimized

# Bulk create with batching
objects = [{'name': f'Item {i}'} for i in range(10000)]
bulk_create_optimized(MyModel, objects, batch_size=1000)

# Batch update
queryset = MyModel.objects.filter(active=True)
batch_update_optimized(queryset, {'status': 'processed'}, batch_size=1000)
```

### 3. Async Views

**For I/O-Bound Operations**:

```python
from django.http import JsonResponse
from asgiref.sync import sync_to_async

async def chat_message_async(request):
    """Async view for better concurrency."""
    tenant = request.tenant

    # Run database operations in thread pool
    chat_service = await sync_to_async(ChatbotService)(tenant)
    response = await sync_to_async(chat_service.process_message)(
        request.data['message'],
        request.data['user_id']
    )

    return JsonResponse({'reply': response})
```

**Benefits**:
- Handle 2-3x more concurrent requests
- Better resource utilization
- Ideal for I/O-bound operations (API calls, file uploads)

### 4. Response Compression

**Django GZipMiddleware**:

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',  # Add at top
    # ... other middleware
]
```

**Or use Nginx compression** (recommended):

```nginx
# nginx.conf
gzip on;
gzip_vary on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;
```

### 5. Performance Monitoring

**Implemented in**: `shoshchat/core/middleware/performance.py`

**Track Slow Operations**:

```python
from core.performance import PerformanceMonitor

@PerformanceMonitor.monitor(threshold_ms=500)
def slow_function():
    # This will log if execution > 500ms
    expensive_operation()
```

**Middleware Features**:
- `QueryCountMiddleware`: Counts and logs database queries
- `DatabaseOptimizationMiddleware`: Logs slow queries
- `RequestPerformanceMiddleware`: Tracks request duration
- `MemoryUsageMiddleware`: Monitors memory consumption

---

## Database Optimization

### 1. Connection Pooling

**Implemented in**: `shoshchat/core/settings/database_performance.py`

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        # ... connection details
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30s timeout
        },
        'CONN_HEALTH_CHECKS': True,
    }
}
```

**Benefits**:
- Reuses database connections
- Reduces connection overhead
- Better performance under load

### 2. Read Replicas

**Implemented in**: `shoshchat/core/db_router.py`

```python
# settings.py
DATABASE_ROUTERS = ['core.db_router.ReadReplicaRouter']

DATABASES = {
    'default': {...},  # Primary (writes)
    'read_replica_1': {...},  # Read replica 1
    'read_replica_2': {...},  # Read replica 2
}
```

**Router Features**:
- Automatic read/write splitting
- Load balancing across replicas
- Fallback to primary if replicas unavailable

### 3. Database Indexes

**Add Indexes for Common Queries**:

```python
# models.py
class Message(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20)

    class Meta:
        indexes = [
            models.Index(fields=['session', '-created_at']),
            models.Index(fields=['role', 'created_at']),
            models.Index(fields=['-created_at']),  # For recent messages
        ]
        ordering = ['-created_at']
```

**Check Missing Indexes**:

```sql
-- PostgreSQL query to find missing indexes
SELECT
    schemaname,
    tablename,
    seq_scan,
    idx_scan,
    CASE WHEN seq_scan > 0 THEN idx_scan::float / seq_scan ELSE 0 END AS idx_scan_ratio
FROM pg_stat_user_tables
WHERE seq_scan > 100
ORDER BY seq_scan DESC;
```

### 4. Query Optimization

**Use Explain Analyze**:

```python
# In Django shell
queryset = User.objects.filter(active=True).select_related('profile')
print(queryset.explain(analyze=True))
```

**Common Optimizations**:

```python
# ❌ Bad: N+1 query problem
users = User.objects.all()
for user in users:
    print(user.profile.bio)  # Queries database for each user

# ✅ Good: Use select_related
users = User.objects.select_related('profile').all()
for user in users:
    print(user.profile.bio)  # No additional queries

# ❌ Bad: Loading all objects into memory
users = User.objects.all()
for user in users:
    process(user)

# ✅ Good: Use iterator for large querysets
users = User.objects.all().iterator(chunk_size=1000)
for user in users:
    process(user)

# ❌ Bad: Multiple queries
user_count = User.objects.count()
active_count = User.objects.filter(active=True).count()

# ✅ Good: Single aggregation query
from django.db.models import Count, Q
stats = User.objects.aggregate(
    total=Count('id'),
    active=Count('id', filter=Q(active=True))
)
```

---

## Caching Strategies

### 1. Cache Layers

**Multi-Level Caching**:

```
Browser Cache (Service Worker)
    ↓
CDN Cache (Cloudflare)
    ↓
Application Cache (Redis)
    ↓
Database Query Cache
    ↓
Database
```

### 2. Cache Configuration

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'shoshchat',
        'TIMEOUT': 300,  # 5 minutes default
    }
}
```

### 3. Cache Warming

**Implemented in**: `shoshchat/core/performance.py`

```python
from core.performance import CacheWarmer

# Warm cache on deployment
CacheWarmer.warm_tenant_configs()
CacheWarmer.warm_llm_configs()
```

### 4. Cache Invalidation

```python
from core.performance import invalidate_cache_pattern

# Invalidate all user caches
invalidate_cache_pattern('user:*')

# Invalidate specific tenant
invalidate_cache_pattern(f'tenant_config:{tenant_id}:*')
```

### 5. What to Cache

**Good Candidates**:
- ✅ Tenant configurations
- ✅ User profiles
- ✅ LLM configurations
- ✅ Static knowledge chunks
- ✅ API rate limit counters
- ✅ Session data

**Bad Candidates**:
- ❌ Real-time chat messages
- ❌ Constantly changing data
- ❌ User-specific volatile data
- ❌ Large binary files

---

## Scalability

### 1. Horizontal Scaling

**Application Servers**:

```yaml
# docker-compose.prod.yml
web:
  deploy:
    replicas: 4  # Run 4 instances
    resources:
      limits:
        cpus: '1'
        memory: 1G
```

**Load Balancer** (Nginx):

```nginx
upstream shoshchat_backend {
    least_conn;  # Route to server with fewest connections
    server web-1:8000 max_fails=3 fail_timeout=30s;
    server web-2:8000 max_fails=3 fail_timeout=30s;
    server web-3:8000 max_fails=3 fail_timeout=30s;
    server web-4:8000 max_fails=3 fail_timeout=30s;
}
```

### 2. Stateless Architecture

**Requirements**:
- ✅ No local file storage (use S3 or shared storage)
- ✅ Session data in Redis (not server memory)
- ✅ No server-specific state
- ✅ Distributed locks for critical sections

**Shared Storage**:

```python
# settings.py
# Use S3 for media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_STORAGE_BUCKET_NAME = 'shoshchat-media'

# Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### 3. Auto-Scaling

**Kubernetes HPA** (Horizontal Pod Autoscaler):

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: shoshchat-web
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: shoshchat-web
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### 4. Database Scalability

**Strategies**:

1. **Read Replicas** (implemented)
   - Route reads to replicas
   - Scale reads horizontally

2. **Connection Pooling** (implemented)
   - Reuse connections
   - Reduce overhead

3. **PgBouncer** (recommended)
   - Connection pooler for PostgreSQL
   - Supports 10,000+ connections

4. **Database Sharding** (future)
   - Split data across multiple databases
   - Tenant-based sharding

### 5. Celery Scaling

```yaml
# docker-compose.prod.yml
celery_worker:
  deploy:
    replicas: 4  # Multiple workers
  command: celery -A core worker -l info --concurrency=4 --max-tasks-per-child=1000
```

**Task Queues**:

```python
# Route tasks to specific queues
app.conf.task_routes = {
    'knowledge.tasks.process_knowledge_source': {'queue': 'knowledge'},
    'billing.tasks.sync_stripe_data': {'queue': 'billing'},
    'chatbot.tasks.generate_response': {'queue': 'chat'},
}
```

---

## Monitoring & Profiling

### 1. Application Monitoring

**Middleware Headers**:
- `X-DB-Query-Count`: Number of database queries
- `X-Request-Duration-Ms`: Total request duration
- `X-Cache-Hit-Rate`: Cache hit percentage
- `X-Memory-Usage-MB`: Memory consumption

### 2. Performance Profiling

**Django Debug Toolbar** (development):

```python
# settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
```

**cProfile** (production):

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### 3. Database Query Analysis

**Enable Query Logging**:

```python
# settings.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

**Slow Query Log** (PostgreSQL):

```sql
-- postgresql.conf
log_min_duration_statement = 100  -- Log queries > 100ms
```

### 4. Real User Monitoring (RUM)

**Web Vitals**:

```typescript
// src/lib/performance.ts
import { onCLS, onFID, onFCP, onLCP, onTTFB } from 'web-vitals';

function sendToAnalytics(metric) {
  // Send to analytics service
  console.log(metric);
}

onCLS(sendToAnalytics);
onFID(sendToAnalytics);
onFCP(sendToAnalytics);
onLCP(sendToAnalytics);
onTTFB(sendToAnalytics);
```

---

## Performance Checklist

### Frontend

- [ ] Code splitting implemented
- [ ] Lazy loading for routes
- [ ] Image optimization (WebP, lazy load)
- [ ] Bundle size < 500KB (gzipped)
- [ ] Lighthouse score > 90
- [ ] Service worker for caching
- [ ] Virtual scrolling for long lists
- [ ] Memoization for expensive components

### Backend

- [ ] Database connection pooling
- [ ] Query optimization (select_related, prefetch_related)
- [ ] Redis caching implemented
- [ ] Cache hit rate > 80%
- [ ] API response time p95 < 200ms
- [ ] Response compression enabled
- [ ] Async views for I/O-bound operations
- [ ] Rate limiting configured

### Database

- [ ] Indexes on frequently queried fields
- [ ] Query count < 10 per request
- [ ] Read replicas configured
- [ ] Connection health checks enabled
- [ ] Query timeout set (30s)
- [ ] Slow query logging enabled
- [ ] Regular VACUUM and ANALYZE

### Infrastructure

- [ ] Load balancer configured
- [ ] Horizontal scaling ready (stateless)
- [ ] Auto-scaling configured
- [ ] CDN for static assets
- [ ] Monitoring and alerting set up
- [ ] Performance budgets defined
- [ ] Regular load testing

---

## Performance Testing

### Load Testing with k6

```bash
cd load-tests
k6 run --duration 5m --vus 100 chat-api.js
```

### Benchmarking

```bash
# Django management command
python manage.py test_performance

# ab (Apache Benchmark)
ab -n 1000 -c 10 https://shoshchat.ai/api/v1/chat/

# wrk
wrk -t4 -c100 -d30s https://shoshchat.ai/api/v1/chat/
```

---

## Best Practices Summary

1. **Measure First**: Profile before optimizing
2. **Cache Aggressively**: But invalidate correctly
3. **Optimize Queries**: N+1 is the enemy
4. **Scale Horizontally**: Stateless > Stateful
5. **Monitor Everything**: You can't improve what you don't measure
6. **Set Budgets**: Performance budgets prevent regressions
7. **Test Under Load**: Load test before going live

---

**Last Updated**: 2025-01-15
**Version**: 1.0
