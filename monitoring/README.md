# ShoshChat AI - Monitoring & Observability

This directory contains monitoring and observability configurations for the ShoshChat AI platform.

## Overview

The monitoring stack includes:
- **Prometheus**: Metrics collection and storage
- **Grafana**: Metrics visualization and dashboards
- **Alertmanager**: Alert routing and notification
- **Health Checks**: Built-in application health monitoring

## Architecture

```
┌─────────────┐
│  Grafana    │──────> Visualization & Dashboards
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Prometheus  │──────> Metrics Collection & Storage
└──────┬──────┘
       │
       ├──> Django Application (/metrics)
       ├──> PostgreSQL Exporter
       ├──> Redis Exporter
       ├──> Celery Exporter
       ├──> Nginx Exporter
       └──> Node Exporter
```

## Health Check Endpoints

The application provides two health check endpoints:

### `/healthz/` - Basic Health Check
Simple liveness probe that returns 200 if the application is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "service": "shoshchat-api"
}
```

**Use case:** Load balancer health checks, container orchestration liveness probes

### `/readyz/` - Readiness Check
Comprehensive readiness probe that checks all dependencies.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00Z",
  "service": "shoshchat-api",
  "checks": {
    "database": {
      "status": "healthy",
      "latency_ms": 2.5,
      "database": "shoshchat_prod"
    },
    "cache": {
      "status": "healthy",
      "latency_ms": 1.2,
      "backend": "redis"
    },
    "celery": {
      "status": "healthy",
      "latency_ms": 150.3,
      "workers": 4,
      "worker_names": ["celery@worker-1", "celery@worker-2"]
    }
  },
  "response_time_ms": 155.8
}
```

**Use case:** Kubernetes readiness probes, deployment verification

## Setting Up Monitoring

### 1. Install Prometheus

```bash
# Using Docker
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/monitoring/alerts:/etc/prometheus/alerts \
  prom/prometheus
```

### 2. Install Grafana

```bash
# Using Docker
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

Access Grafana at http://localhost:3000 (default credentials: admin/admin)

### 3. Configure Data Source

1. Log in to Grafana
2. Go to Configuration > Data Sources
3. Add Prometheus data source
4. Set URL to `http://prometheus:9090`
5. Save & Test

### 4. Import Dashboard

1. Go to Dashboards > Import
2. Upload `monitoring/grafana-dashboard.json`
3. Select Prometheus data source
4. Click Import

## Alerts

Alert rules are defined in `alerts/shoshchat-alerts.yml` and include:

### Application Alerts
- **HighErrorRate**: Error rate > 5% for 5 minutes
- **HighResponseTime**: P95 response time > 1s for 5 minutes
- **ServiceDown**: API unavailable for 2 minutes

### Database Alerts
- **PostgreSQLDown**: Database unavailable for 2 minutes
- **PostgreSQLTooManyConnections**: > 80% of max connections
- **PostgreSQLSlowQueries**: Queries taking > 60 seconds

### Cache Alerts
- **RedisDown**: Redis unavailable for 2 minutes
- **RedisHighMemoryUsage**: > 90% memory usage
- **RedisTooManyConnections**: > 100 connected clients

### Celery Alerts
- **CeleryNoWorkers**: No active workers for 5 minutes
- **CeleryHighQueueLength**: > 1000 tasks in queue
- **CeleryHighTaskFailureRate**: > 10% task failure rate

### Infrastructure Alerts
- **HighMemoryUsage**: > 90% memory usage for 5 minutes
- **HighCPUUsage**: > 80% CPU usage for 10 minutes

## Configuring Alertmanager

Create `alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@shoshchat.ai'
  smtp_auth_username: 'alerts@shoshchat.ai'
  smtp_auth_password: 'your-password'

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'team-emails'

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

receivers:
  - name: 'team-emails'
    email_configs:
      - to: 'team@shoshchat.ai'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'your-pagerduty-key'

  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
```

## Metrics Collected

### Application Metrics
- HTTP request rate (by method, endpoint, status)
- HTTP response time (histogram)
- Database query count and duration
- Cache hit/miss ratio
- Active sessions

### Database Metrics
- Connection count
- Query performance
- Table sizes
- Index usage
- Replication lag (if applicable)

### Cache Metrics
- Memory usage
- Hit/miss ratio
- Eviction rate
- Connection count

### Celery Metrics
- Task execution rate
- Task duration
- Queue length
- Worker count
- Task success/failure rate

### System Metrics
- CPU usage
- Memory usage
- Disk I/O
- Network I/O
- File descriptors

## Best Practices

### 1. Set Appropriate Alert Thresholds
- Start conservative and adjust based on actual behavior
- Use `for` duration to avoid alert fatigue from transient issues
- Set different severity levels (critical, warning, info)

### 2. Monitor What Matters
- Focus on metrics that indicate user impact
- Track both technical and business metrics
- Monitor the full request path (frontend → backend → database)

### 3. Use SLOs (Service Level Objectives)
Define and monitor:
- Availability: 99.9% uptime
- Latency: P95 < 500ms, P99 < 1s
- Error Rate: < 1% failed requests

### 4. Regular Review
- Review alerts weekly
- Adjust thresholds based on trends
- Remove noisy or irrelevant alerts
- Update runbooks based on incidents

## Troubleshooting

### Prometheus not scraping metrics

1. Check if Django metrics endpoint is accessible:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify Prometheus configuration:
   ```bash
   docker exec prometheus promtool check config /etc/prometheus/prometheus.yml
   ```

3. Check Prometheus targets: http://localhost:9090/targets

### Grafana not showing data

1. Verify Prometheus data source connection
2. Check time range in dashboard
3. Verify metrics exist in Prometheus: http://localhost:9090/graph

### Alerts not firing

1. Check alert rules in Prometheus: http://localhost:9090/alerts
2. Verify Alertmanager is running and configured
3. Check Alertmanager logs for delivery errors

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Django Prometheus](https://github.com/korfuri/django-prometheus)
- [PostgreSQL Exporter](https://github.com/prometheus-community/postgres_exporter)
- [Redis Exporter](https://github.com/oliver006/redis_exporter)
