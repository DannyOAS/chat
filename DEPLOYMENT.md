# ShoshChat AI - Production Deployment Guide

Complete guide for deploying ShoshChat AI to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Options](#deployment-options)
   - [Docker Deployment](#docker-deployment)
   - [DigitalOcean App Platform](#digitalocean-app-platform)
   - [AWS Deployment](#aws-deployment)
   - [Kubernetes Deployment](#kubernetes-deployment)
5. [Database Migration](#database-migration)
6. [SSL/TLS Configuration](#ssltls-configuration)
7. [Monitoring Setup](#monitoring-setup)
8. [Backup Strategy](#backup-strategy)
9. [Rollback Procedures](#rollback-procedures)
10. [Post-Deployment Verification](#post-deployment-verification)

## Prerequisites

- Docker 24.0+ and Docker Compose 2.0+
- SSL certificates (Let's Encrypt recommended)
- Domain name configured with DNS
- PostgreSQL 15+ database
- Redis 7+ instance
- SMTP server for email notifications
- API keys:
  - OpenAI API key
  - Pinecone API key
  - Stripe API keys
  - Sentry DSN (optional but recommended)

## Pre-Deployment Checklist

- [ ] All environment variables configured
- [ ] SSL certificates obtained
- [ ] Database backup strategy in place
- [ ] Monitoring and alerting configured
- [ ] DNS records configured
- [ ] Firewall rules configured
- [ ] Secrets management configured
- [ ] CI/CD pipeline tested
- [ ] Load testing completed
- [ ] Security audit completed
- [ ] Documentation reviewed

## Environment Configuration

### 1. Copy Environment Template

```bash
cp shoshchat/.env.production.example shoshchat/.env.production
```

### 2. Configure Critical Variables

Edit `shoshchat/.env.production`:

```bash
# Django
SECRET_KEY=<generate-with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
ALLOWED_HOSTS=shoshchat.ai,www.shoshchat.ai

# Database
POSTGRES_DB=shoshchat_prod
POSTGRES_USER=shoshchat
POSTGRES_PASSWORD=<generate-strong-password>
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_PASSWORD=<generate-strong-password>

# OpenAI
OPENAI_API_KEY=sk-...

# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### 3. Generate Strong Passwords

```bash
# Generate Django secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate random passwords (Linux/macOS)
openssl rand -base64 32
```

## Deployment Options

### Docker Deployment

#### Step 1: Prepare Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create deployment user
sudo useradd -m -s /bin/bash shoshchat
sudo usermod -aG docker shoshchat
```

#### Step 2: Clone Repository

```bash
sudo su - shoshchat
git clone https://github.com/yourusername/shoshchat.git
cd shoshchat
git checkout main
```

#### Step 3: Configure Environment

```bash
# Copy and edit environment file
cp shoshchat/.env.production.example shoshchat/.env.production
nano shoshchat/.env.production
```

#### Step 4: Obtain SSL Certificates

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot certonly --standalone -d shoshchat.ai -d www.shoshchat.ai

# Copy certificates to nginx directory
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/shoshchat.ai/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/shoshchat.ai/privkey.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/shoshchat.ai/chain.pem nginx/ssl/
```

#### Step 5: Build and Deploy

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Run database migrations
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml run --rm web python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml run --rm web python manage.py collectstatic --noinput

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

#### Step 6: Verify Deployment

```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl https://shoshchat.ai/healthz/
curl https://shoshchat.ai/readyz/
```

### DigitalOcean App Platform

#### Step 1: Create App Spec

Create `app.yaml`:

```yaml
name: shoshchat-ai
region: nyc

databases:
  - name: db
    engine: PG
    version: "15"
    size: db-s-1vcpu-1gb
    num_nodes: 1

  - name: redis
    engine: REDIS
    version: "7"
    size: db-s-1vcpu-1gb

services:
  - name: web
    github:
      repo: yourusername/shoshchat
      branch: main
      deploy_on_push: true
    dockerfile_path: shoshchat/Dockerfile.prod
    http_port: 8000
    instance_count: 2
    instance_size_slug: professional-xs
    envs:
      - key: DJANGO_SETTINGS_MODULE
        value: core.settings.production
      - key: DATABASE_URL
        scope: RUN_AND_BUILD_TIME
        type: SECRET
      - key: REDIS_URL
        scope: RUN_AND_BUILD_TIME
        type: SECRET
    health_check:
      http_path: /healthz/
      initial_delay_seconds: 30

  - name: celery-worker
    github:
      repo: yourusername/shoshchat
      branch: main
    dockerfile_path: shoshchat/Dockerfile.prod
    run_command: celery -A core worker -l info
    instance_count: 1
    instance_size_slug: professional-xs

  - name: celery-beat
    github:
      repo: yourusername/shoshchat
      branch: main
    dockerfile_path: shoshchat/Dockerfile.prod
    run_command: celery -A core beat -l info
    instance_count: 1
    instance_size_slug: basic-xxs
```

#### Step 2: Deploy

```bash
# Install doctl (DigitalOcean CLI)
brew install doctl  # macOS
# or
sudo snap install doctl  # Linux

# Authenticate
doctl auth init

# Create app
doctl apps create --spec app.yaml

# Monitor deployment
doctl apps list
doctl apps logs <app-id>
```

### AWS Deployment

#### Using AWS Elastic Beanstalk

##### Step 1: Install EB CLI

```bash
pip install awsebcli
```

##### Step 2: Initialize EB Application

```bash
cd shoshchat
eb init -p docker shoshchat-ai --region us-east-1
```

##### Step 3: Create Environment

```bash
# Create RDS PostgreSQL database
eb create shoshchat-prod \
  --database \
  --database.engine postgres \
  --database.version 15.3 \
  --database.size db.t3.micro \
  --instance-type t3.medium \
  --envvars SECRET_KEY=...,OPENAI_API_KEY=...
```

##### Step 4: Configure Environment

```bash
# Set environment variables
eb setenv \
  DJANGO_SETTINGS_MODULE=core.settings.production \
  SECRET_KEY=your-secret-key \
  OPENAI_API_KEY=your-api-key \
  ALLOWED_HOSTS=.elasticbeanstalk.com,shoshchat.ai
```

##### Step 5: Deploy

```bash
eb deploy
```

##### Step 6: Configure Custom Domain

```bash
# Add CNAME record in Route 53
# Point shoshchat.ai to your-env.elasticbeanstalk.com

# Configure SSL with ACM
eb ssl enable --certificate-arn arn:aws:acm:...
```

#### Using AWS ECS (Fargate)

See `deployment/aws-ecs/` for CloudFormation templates and detailed instructions.

### Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Helm 3+ installed

#### Step 1: Create Namespace

```bash
kubectl create namespace shoshchat
```

#### Step 2: Create Secrets

```bash
# Create secret for environment variables
kubectl create secret generic shoshchat-secrets \
  --from-env-file=shoshchat/.env.production \
  -n shoshchat

# Create secret for SSL certificates
kubectl create secret tls shoshchat-tls \
  --cert=nginx/ssl/fullchain.pem \
  --key=nginx/ssl/privkey.pem \
  -n shoshchat
```

#### Step 3: Deploy with Helm

```bash
# Add Bitnami repository for PostgreSQL and Redis
helm repo add bitnami https://charts.bitnami.com/bitnami

# Install PostgreSQL
helm install postgresql bitnami/postgresql \
  --set auth.username=shoshchat \
  --set auth.password=<password> \
  --set auth.database=shoshchat_prod \
  -n shoshchat

# Install Redis
helm install redis bitnami/redis \
  --set auth.password=<password> \
  -n shoshchat

# Deploy ShoshChat
kubectl apply -f deployment/kubernetes/ -n shoshchat
```

See `deployment/kubernetes/` for Kubernetes manifests.

## Database Migration

### Running Migrations

```bash
# Docker
docker-compose -f docker-compose.prod.yml run --rm web python manage.py migrate

# Kubernetes
kubectl exec -it deployment/web -n shoshchat -- python manage.py migrate

# DigitalOcean App Platform
doctl apps run <app-id> --component web --command "python manage.py migrate"
```

### Zero-Downtime Migrations

For production deployments with zero downtime:

1. **Backward Compatible Changes Only**
   - Add new columns as nullable
   - Don't remove columns immediately
   - Use database views for schema changes

2. **Multi-Step Deployment**
   ```bash
   # Step 1: Add new column (nullable)
   python manage.py migrate

   # Step 2: Deploy new code
   # Step 3: Backfill data
   python manage.py backfill_data

   # Step 4: Make column non-nullable
   python manage.py migrate

   # Step 5: Remove old column (in next release)
   ```

## SSL/TLS Configuration

### Let's Encrypt with Certbot

#### Initial Setup

```bash
# Install Certbot
sudo apt install certbot

# Obtain certificate (standalone mode)
sudo certbot certonly --standalone -d shoshchat.ai -d www.shoshchat.ai

# Or with Nginx plugin
sudo certbot --nginx -d shoshchat.ai -d www.shoshchat.ai
```

#### Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Add cron job for auto-renewal
sudo crontab -e

# Add this line:
0 3 * * * certbot renew --quiet --post-hook "docker-compose -f /home/shoshchat/shoshchat/docker-compose.prod.yml restart nginx"
```

### AWS Certificate Manager (ACM)

```bash
# Request certificate
aws acm request-certificate \
  --domain-name shoshchat.ai \
  --subject-alternative-names www.shoshchat.ai \
  --validation-method DNS

# Add DNS validation records to Route 53
# Certificate will auto-renew
```

## Monitoring Setup

See [monitoring/README.md](monitoring/README.md) for detailed instructions.

### Quick Setup

```bash
# Start monitoring stack
docker-compose -f monitoring/docker-compose.yml up -d

# Access Grafana
open http://localhost:3000

# Import dashboard
# Upload monitoring/grafana-dashboard.json
```

## Backup Strategy

### Database Backups

#### Automated Backups

```bash
# Create backup script
cat > backup-db.sh <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/shoshchat/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/shoshchat_db_$DATE.sql.gz"

# Create backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U shoshchat shoshchat_prod | gzip > "$BACKUP_FILE"

# Keep only last 30 days
find "$BACKUP_DIR" -name "shoshchat_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
EOF

chmod +x backup-db.sh

# Add to cron
crontab -e
# Add: 0 2 * * * /home/shoshchat/shoshchat/backup-db.sh
```

#### Restore from Backup

```bash
# Stop application
docker-compose -f docker-compose.prod.yml stop web celery_worker

# Restore database
gunzip -c backup.sql.gz | docker-compose -f docker-compose.prod.yml exec -T db psql -U shoshchat shoshchat_prod

# Start application
docker-compose -f docker-compose.prod.yml start web celery_worker
```

### Media Files Backup

```bash
# Backup media files to S3
aws s3 sync shoshchat/media/ s3://shoshchat-backups/media/ --delete

# Or use rsync to remote server
rsync -avz shoshchat/media/ backup-server:/backups/shoshchat/media/
```

## Rollback Procedures

### Docker Deployment

```bash
# Stop current version
docker-compose -f docker-compose.prod.yml down

# Checkout previous version
git checkout <previous-commit>

# Rebuild and restart
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# If database migration needed, restore from backup
```

### Kubernetes Deployment

```bash
# Rollback to previous deployment
kubectl rollout undo deployment/web -n shoshchat

# Rollback to specific revision
kubectl rollout history deployment/web -n shoshchat
kubectl rollout undo deployment/web --to-revision=2 -n shoshchat
```

### DigitalOcean App Platform

```bash
# List deployments
doctl apps deployment list <app-id>

# Rollback to previous deployment
doctl apps deployment create <app-id> --deployment-id <previous-deployment-id>
```

## Post-Deployment Verification

### 1. Health Checks

```bash
# Basic health check
curl https://shoshchat.ai/healthz/

# Detailed readiness check
curl https://shoshchat.ai/readyz/
```

### 2. Functional Tests

```bash
# Run smoke tests
cd shoshchat
python manage.py test tests.smoke --settings=core.settings.production

# Or use load tests
cd load-tests
k6 run --duration 1m --vus 10 chat-api.js
```

### 3. Monitor Logs

```bash
# Docker
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Kubernetes
kubectl logs -f deployment/web -n shoshchat

# Check for errors
docker-compose -f docker-compose.prod.yml logs | grep -i error
```

### 4. Performance Verification

- Check response times in Grafana dashboard
- Verify database query performance
- Check Celery task queue length
- Verify cache hit rates

### 5. Security Verification

```bash
# Check SSL configuration
curl -I https://shoshchat.ai

# Run security headers check
curl -I https://shoshchat.ai | grep -i "strict-transport-security\|x-frame-options\|x-content-type-options"

# Test rate limiting
for i in {1..100}; do curl -s https://shoshchat.ai/api/v1/chat/message/ & done
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs web

# Common issues:
# - Missing environment variables
# - Database connection failure
# - Port conflicts
```

### Database Connection Errors

```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Test connection
docker-compose -f docker-compose.prod.yml exec db psql -U shoshchat -d shoshchat_prod
```

### SSL Certificate Issues

```bash
# Verify certificate
openssl s_client -connect shoshchat.ai:443 -servername shoshchat.ai

# Check certificate expiry
echo | openssl s_client -connect shoshchat.ai:443 2>/dev/null | openssl x509 -noout -dates
```

### High Memory Usage

```bash
# Check container memory
docker stats

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Scale down if needed
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=2
```

## Support

For deployment issues:
- Check the [GitHub Issues](https://github.com/yourusername/shoshchat/issues)
- Review [monitoring/README.md](monitoring/README.md)
- Contact: support@shoshchat.ai
