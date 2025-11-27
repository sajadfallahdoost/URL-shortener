# Deployment Guide

Production deployment guide for the URL Shortener service.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Docker Deployment](#docker-deployment)
4. [Database Setup](#database-setup)
5. [Configuration](#configuration)
6. [Monitoring & Logging](#monitoring--logging)
7. [Backup & Recovery](#backup--recovery)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended) or Docker
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- (Optional) PostgreSQL 15+
- (Optional) Redis 7+

---

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd URL-shortener
```

### 2. Configure Environment

Create `.env` file from example:

```bash
cp .env.example .env
```

Edit `.env` with production values:

```bash
# Application
ENVIRONMENT=production
DEBUG=False
BASE_URL=https://your-domain.com

# Database
DATABASE_URL=postgresql+asyncpg://url_shortner_user:STRONG_PASSWORD@postgres:5432/url_shortner
POSTGRES_PASSWORD=STRONG_PASSWORD

# Redis
REDIS_URL=redis://redis:6379/0

# Security
RATE_LIMIT_PER_MINUTE=100

# Logging
LOG_LEVEL=INFO

# CORS
CORS_ORIGINS=https://your-frontend.com
```

**Important**: Change all default passwords!

---

## Docker Deployment

### Quick Start

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Check health
curl http://localhost:8000/api/v1/health
```

### Production Configuration

Edit `docker-compose.yml` for production:

```yaml
services:
  app:
    # Use specific version tag
    image: url-shortener:1.0.0
    
    # Restart policy
    restart: always
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Build Custom Image

```bash
# Build image
docker build -t url-shortener:1.0.0 .

# Tag for registry
docker tag url-shortener:1.0.0 your-registry/url-shortener:1.0.0

# Push to registry
docker push your-registry/url-shortener:1.0.0
```

---

## Database Setup

### Initial Setup

The database is automatically initialized using `docs/database/database.sql` when using Docker Compose.

### Manual Setup (Without Docker)

```bash
# Connect to PostgreSQL
psql -U postgres

# Run initialization script
\i docs/database/database.sql

# Verify
\c url_shortner
\dt
```

### Run Migrations

```bash
# Check current version
alembic current

# Upgrade to latest
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

### Database Backups

```bash
# Backup
docker-compose exec postgres pg_dump -U url_shortner_user url_shortner > backup.sql

# Restore
docker-compose exec -T postgres psql -U url_shortner_user url_shortner < backup.sql
```

---

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | Yes | development | Environment mode |
| `DATABASE_URL` | Yes | - | PostgreSQL connection |
| `REDIS_URL` | Yes | - | Redis connection |
| `BASE_URL` | Yes | - | Public base URL |
| `POSTGRES_PASSWORD` | Yes | - | Database password |
| `RATE_LIMIT_PER_MINUTE` | No | 100 | Rate limit |
| `LOG_LEVEL` | No | INFO | Logging level |
| `CORS_ORIGINS` | No | localhost | Allowed origins |

### Production Settings

**Database Connection Pool:**
```
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10
```

**Redis Cache:**
```
REDIS_CACHE_TTL=86400  # 24 hours
REDIS_MAX_CONNECTIONS=50
```

**Security:**
```
RATE_LIMIT_PER_MINUTE=100
REQUEST_TIMEOUT=30
```

---

## SSL/TLS Setup

### Using Nginx Reverse Proxy

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Using Traefik

```yaml
services:
  app:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.urlshortener.rule=Host(`your-domain.com`)"
      - "traefik.http.routers.urlshortener.tls=true"
      - "traefik.http.routers.urlshortener.tls.certresolver=letsencrypt"
```

---

## Monitoring & Logging

### Health Checks

**Application Health:**
```bash
curl http://localhost:8000/api/v1/health
```

**Docker Health:**
```bash
docker-compose ps
```

### Logging

**View Logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app
```

**Log Files:**
- Application logs: stdout/stderr (captured by Docker)
- PostgreSQL logs: `/var/lib/postgresql/data/log/`
- Redis logs: `/var/log/redis/`

### Metrics (Future Enhancement)

Recommended tools:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Sentry**: Error tracking

---

## Backup & Recovery

### Automated Backups

Create a backup script:

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup database
docker-compose exec -T postgres pg_dump \
  -U url_shortner_user url_shortner \
  | gzip > "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Backup Redis (optional)
docker-compose exec redis redis-cli SAVE
docker cp url-shortener-redis:/data/dump.rdb "$BACKUP_DIR/redis_backup_$DATE.rdb"

# Keep only last 7 days
find "$BACKUP_DIR" -name "*.gz" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +7 -delete
```

**Cron Job:**
```bash
# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh
```

### Disaster Recovery

```bash
# Stop services
docker-compose down

# Restore database
gunzip -c /backups/db_backup_YYYYMMDD.sql.gz | \
  docker-compose exec -T postgres psql -U url_shortner_user url_shortner

# Restore Redis
docker cp /backups/redis_backup_YYYYMMDD.rdb url-shortener-redis:/data/dump.rdb

# Start services
docker-compose up -d
```

---

## Scaling Deployment

### Horizontal Scaling

**Multiple App Instances:**

```yaml
services:
  app:
    deploy:
      replicas: 3
    
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "80:80"
    depends_on:
      - app
```

**Nginx Load Balancer:**

```nginx
upstream app_servers {
    least_conn;
    server app1:8000;
    server app2:8000;
    server app3:8000;
}

server {
    listen 80;
    
    location / {
        proxy_pass http://app_servers;
    }
}
```

### Database Read Replicas

```yaml
services:
  postgres-primary:
    image: postgres:15-alpine
    # Primary configuration
  
  postgres-replica:
    image: postgres:15-alpine
    environment:
      POSTGRES_PRIMARY_HOST: postgres-primary
    # Replica configuration
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Failed**

```bash
# Check database is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U url_shortner_user -d url_shortner
```

**2. Redis Connection Failed**

```bash
# Check Redis is running
docker-compose ps redis

# Test connection
docker-compose exec redis redis-cli ping
```

**3. Application Won't Start**

```bash
# Check logs
docker-compose logs app

# Rebuild image
docker-compose build --no-cache app
docker-compose up -d
```

**4. High Memory Usage**

```bash
# Check resource usage
docker stats

# Adjust limits in docker-compose.yml
```

**5. Slow Performance**

- Check cache hit ratio
- Monitor database query times
- Verify indexes are present
- Check network latency

### Debug Mode

Enable debug logging:

```bash
# In .env
DEBUG=True
LOG_LEVEL=DEBUG

# Restart
docker-compose restart app
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Configure CORS for your domain
- [ ] Enable SSL/TLS
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Set up automated backups
- [ ] Test disaster recovery

---

## Maintenance

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose build
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head
```

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U url_shortner_user -d url_shortner -c "VACUUM ANALYZE;"

# Check table sizes
docker-compose exec postgres psql -U url_shortner_user -d url_shortner -c "\dt+"
```

---

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review [Architecture docs](../architecture/README.md)
- Check [Development guide](../development/README.md)

