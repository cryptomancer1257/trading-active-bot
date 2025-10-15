# 🚀 Production Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the Bot Trading Marketplace system to production environments. The deployment supports high availability, scalability, and security requirements for financial trading applications.

## 🏗️ Infrastructure Requirements

### Minimum System Specifications

**API Server (per instance):**
- CPU: 4 vCPU cores
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 1 Gbps

**Database Server:**
- CPU: 8 vCPU cores  
- RAM: 16 GB
- Storage: 500 GB SSD (with IOPS provisioned)
- Network: 2 Gbps

**Redis Server:**
- CPU: 2 vCPU cores
- RAM: 4 GB
- Storage: 20 GB SSD
- Network: 1 Gbps

**Celery Workers (per instance):**
- CPU: 2 vCPU cores
- RAM: 4 GB
- Storage: 20 GB SSD
- Network: 1 Gbps

### Recommended Production Architecture

```
Internet → Load Balancer → API Servers (2-3 instances)
                              ↓
                         Database Cluster (Master/Slave)
                              ↓
                         Redis Cluster (3 nodes)
                              ↓
                         Celery Workers (3-5 instances)
```

---

## 🐳 Docker Production Setup

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - api
    restart: always
    networks:
      - trading-network

  api:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=mysql+pymysql://botuser:${MYSQL_PASSWORD}@db-master:3306/bot_marketplace
      - REDIS_URL=redis://redis-cluster:6379/0
      - CELERY_BROKER_URL=redis://redis-cluster:6379/1
      - SECRET_KEY=${SECRET_KEY}
      - API_KEY_ENCRYPTION_KEY=${API_KEY_ENCRYPTION_KEY}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./logs/api:/app/logs
    depends_on:
      - db-master
      - redis-cluster
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
    networks:
      - trading-network

  db-master:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=bot_marketplace
      - MYSQL_USER=botuser
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - mysql-master-data:/var/lib/mysql
      - ./mysql/master.cnf:/etc/mysql/conf.d/master.cnf
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
      - ./logs/mysql:/var/log/mysql
    ports:
      - "3306:3306"
    restart: always
    command: --server-id=1 --log-bin=mysql-bin --binlog-do-db=bot_marketplace
    networks:
      - trading-network

  db-slave:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=bot_marketplace
      - MYSQL_USER=botuser
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
    volumes:
      - mysql-slave-data:/var/lib/mysql
      - ./mysql/slave.cnf:/etc/mysql/conf.d/slave.cnf
      - ./logs/mysql-slave:/var/log/mysql
    depends_on:
      - db-master
    restart: always
    command: --server-id=2 --relay-log=relay-bin --read-only=1
    networks:
      - trading-network

  redis-cluster:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
      - ./redis/redis.conf:/etc/redis/redis.conf
    command: redis-server /etc/redis/redis.conf
    restart: always
    networks:
      - trading-network

  celery-worker:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=mysql+pymysql://botuser:${MYSQL_PASSWORD}@db-master:3306/bot_marketplace
      - REDIS_URL=redis://redis-cluster:6379/0
      - CELERY_BROKER_URL=redis://redis-cluster:6379/1
      - API_KEY_ENCRYPTION_KEY=${API_KEY_ENCRYPTION_KEY}
    command: celery -A utils.celery_app worker --loglevel=info --queues=default,bot_execution,futures_trading,maintenance,notifications --concurrency=4
    volumes:
      - ./logs/celery:/app/logs
    depends_on:
      - db-master
      - redis-cluster
    restart: always
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
    networks:
      - trading-network

  celery-beat:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=mysql+pymysql://botuser:${MYSQL_PASSWORD}@db-master:3306/bot_marketplace
      - REDIS_URL=redis://redis-cluster:6379/0
      - CELERY_BROKER_URL=redis://redis-cluster:6379/1
    command: celery -A utils.celery_app beat --loglevel=info
    volumes:
      - ./logs/celery-beat:/app/logs
    depends_on:
      - db-master
      - redis-cluster
    restart: always
    networks:
      - trading-network

  monitoring:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    restart: always
    networks:
      - trading-network

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    restart: always
    networks:
      - trading-network

volumes:
  mysql-master-data:
  mysql-slave-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  trading-network:
    driver: bridge
```

### 2. Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.9-slim

# Security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r trading && useradd -r -g trading trading

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs && \
    chown -R trading:trading /app

# Switch to non-root user
USER trading

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "core.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

## 🌐 Nginx Configuration

### Production Nginx Config

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream api_backend {
        least_conn;
        server api:8000 max_fails=3 fail_timeout=30s;
        server api:8000 max_fails=3 fail_timeout=30s;
        server api:8000 max_fails=3 fail_timeout=30s;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=trading:10m rate=5r/s;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'";

    # Logging
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    server {
        listen 80;
        server_name api.bot-marketplace.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.bot-marketplace.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # API Routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Trading Routes (Lower rate limit)
        location /api/futures-bot/ {
            limit_req zone=trading burst=10 nodelay;
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 120s;
            proxy_send_timeout 120s;
            proxy_read_timeout 120s;
        }

        # Health Check
        location /health {
            proxy_pass http://api_backend;
            access_log off;
        }

        # Documentation
        location /docs {
            proxy_pass http://api_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

## 🗄️ Database Setup

### MySQL Master-Slave Configuration

**Master Configuration (`mysql/master.cnf`):**
```ini
[mysqld]
log-bin=mysql-bin
server-id=1
binlog-do-db=bot_marketplace
expire_logs_days=7
max_binlog_size=100M

# Performance tuning
innodb_buffer_pool_size=8G
innodb_log_file_size=1G
innodb_flush_log_at_trx_commit=2
innodb_flush_method=O_DIRECT
query_cache_type=1
query_cache_size=256M

# Connection limits
max_connections=500
max_user_connections=450

# Security
bind-address=0.0.0.0
```

**Slave Configuration (`mysql/slave.cnf`):**
```ini
[mysqld]
server-id=2
relay-log=relay-bin
read-only=1
log-slave-updates=1

# Performance tuning
innodb_buffer_pool_size=4G
innodb_log_file_size=512M
innodb_flush_log_at_trx_commit=2

# Replication settings
slave-skip-errors=1062
```

### Database Initialization Script

```bash
#!/bin/bash
# setup_replication.sh

# Wait for master to be ready
until docker exec -it bot-trading-db-master mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "SHOW MASTER STATUS;"
do
  echo "Waiting for master database..."
  sleep 5
done

# Get master log position
MASTER_STATUS=$(docker exec -it bot-trading-db-master mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "SHOW MASTER STATUS;" | tail -n 1)
MASTER_LOG_FILE=$(echo $MASTER_STATUS | awk '{print $1}')
MASTER_LOG_POS=$(echo $MASTER_STATUS | awk '{print $2}')

# Configure slave
docker exec -it bot-trading-db-slave mysql -uroot -p${MYSQL_ROOT_PASSWORD} -e "
CHANGE MASTER TO
  MASTER_HOST='db-master',
  MASTER_USER='root',
  MASTER_PASSWORD='${MYSQL_ROOT_PASSWORD}',
  MASTER_LOG_FILE='${MASTER_LOG_FILE}',
  MASTER_LOG_POS=${MASTER_LOG_POS};
START SLAVE;"

echo "Replication setup complete!"
```

---

## 🔐 Environment Configuration

### Production Environment Variables

Create `.env.prod`:

```bash
# Application
ENVIRONMENT=production
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
MYSQL_ROOT_PASSWORD=secure-root-password
MYSQL_PASSWORD=secure-bot-password
DATABASE_URL=mysql+pymysql://botuser:secure-bot-password@db-master:3306/bot_marketplace

# Redis & Celery
REDIS_URL=redis://redis-cluster:6379/0
CELERY_BROKER_URL=redis://redis-cluster:6379/1
CELERY_RESULT_BACKEND=redis://redis-cluster:6379/2

# API Security
API_KEY_ENCRYPTION_KEY=your-32-byte-encryption-key-here
MARKETPLACE_API_KEY=production-marketplace-api-key

# External Services
SENDGRID_API_KEY=your-sendgrid-api-key
FROM_EMAIL=noreply@bot-marketplace.com
OPENAI_API_KEY=your-openai-api-key
CLAUDE_API_KEY=your-claude-api-key

# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=bot-marketplace-production

# Monitoring
GRAFANA_PASSWORD=secure-grafana-password

# SSL
SSL_CERT_PATH=/etc/nginx/ssl/fullchain.pem
SSL_KEY_PATH=/etc/nginx/ssl/privkey.pem
```

### Secret Management

Use AWS Secrets Manager or similar:

```bash
# Store secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name "bot-marketplace/production" \
  --secret-string '{
    "database_password": "secure-bot-password",
    "encryption_key": "your-32-byte-encryption-key",
    "sendgrid_api_key": "your-sendgrid-key",
    "openai_api_key": "your-openai-key"
  }'

# Retrieve in startup script
export MYSQL_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id "bot-marketplace/production" \
  --query 'SecretString' --output text | jq -r '.database_password')
```

---

## 🚀 Deployment Process

### 1. Pre-deployment Checklist

```bash
#!/bin/bash
# pre_deploy_check.sh

echo "Running pre-deployment checks..."

# Check environment variables
required_vars=("MYSQL_PASSWORD" "SECRET_KEY" "API_KEY_ENCRYPTION_KEY" "SENDGRID_API_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Missing required environment variable: $var"
        exit 1
    fi
done

# Check SSL certificates
if [ ! -f "nginx/ssl/fullchain.pem" ] || [ ! -f "nginx/ssl/privkey.pem" ]; then
    echo "❌ SSL certificates not found"
    exit 1
fi

# Test database connection
python -c "
import pymysql
try:
    conn = pymysql.connect(host='localhost', port=3306, user='botuser', password='$MYSQL_PASSWORD', database='bot_marketplace')
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

echo "✅ All pre-deployment checks passed"
```

### 2. Blue-Green Deployment Script

```bash
#!/bin/bash
# deploy.sh

set -e

CURRENT_VERSION=$(docker ps --format "table {{.Names}}\t{{.Image}}" | grep api | head -1 | awk '{print $2}' | cut -d: -f2)
NEW_VERSION="v$(date +%Y%m%d_%H%M%S)"

echo "🚀 Starting deployment..."
echo "Current version: $CURRENT_VERSION"
echo "New version: $NEW_VERSION"

# Build new images
echo "📦 Building new Docker images..."
docker build -t bot-marketplace-api:$NEW_VERSION -f Dockerfile.prod .

# Run database migrations
echo "🗄️ Running database migrations..."
docker run --rm --network=trading-network \
  -e DATABASE_URL="mysql+pymysql://botuser:$MYSQL_PASSWORD@db-master:3306/bot_marketplace" \
  bot-marketplace-api:$NEW_VERSION \
  python migrations/migration_runner.py

# Health check function
health_check() {
    local service_url=$1
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$service_url/health" > /dev/null; then
            echo "✅ Health check passed for $service_url"
            return 0
        fi
        echo "⏳ Health check attempt $attempt/$max_attempts for $service_url"
        sleep 10
        ((attempt++))
    done
    
    echo "❌ Health check failed for $service_url"
    return 1
}

# Deploy new version
echo "🔄 Deploying new version..."
export NEW_VERSION=$NEW_VERSION
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to be healthy
echo "🏥 Performing health checks..."
health_check "http://localhost"

# Run smoke tests
echo "🧪 Running smoke tests..."
./scripts/smoke_tests.sh

echo "✅ Deployment completed successfully!"
echo "🎉 Version $NEW_VERSION is now live"

# Clean up old images
echo "🧹 Cleaning up old images..."
docker image prune -f
```

### 3. Rollback Script

```bash
#!/bin/bash
# rollback.sh

if [ -z "$1" ]; then
    echo "Usage: $0 <version>"
    echo "Available versions:"
    docker images bot-marketplace-api --format "table {{.Tag}}\t{{.CreatedAt}}"
    exit 1
fi

ROLLBACK_VERSION=$1

echo "⏪ Rolling back to version: $ROLLBACK_VERSION"

# Update docker-compose to use rollback version
export NEW_VERSION=$ROLLBACK_VERSION
docker-compose -f docker-compose.prod.yml up -d

# Health check
sleep 30
if curl -f -s "http://localhost/health" > /dev/null; then
    echo "✅ Rollback successful!"
else
    echo "❌ Rollback failed - manual intervention required"
    exit 1
fi
```

---

## 📊 Monitoring Setup

### Prometheus Configuration

Create `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'trading-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'mysql'
    static_configs:
      - targets: ['db-master:9104']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-cluster:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

### Alert Rules

Create `monitoring/alert_rules.yml`:

```yaml
groups:
  - name: trading-api
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"

      - alert: DatabaseConnectionFailure
        expr: mysql_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failure"

      - alert: HighTradingLatency
        expr: histogram_quantile(0.95, rate(trading_request_duration_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High trading request latency"
```

### Grafana Dashboards

Create `monitoring/grafana/dashboards/trading-overview.json`:

```json
{
  "dashboard": {
    "title": "Trading Bot Marketplace Overview",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{ method }} {{ endpoint }}"
          }
        ]
      },
      {
        "title": "Active Trading Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "active_trading_sessions",
            "legendFormat": "Active Sessions"
          }
        ]
      },
      {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "mysql_global_status_threads_connected",
            "legendFormat": "Connected Threads"
          }
        ]
      }
    ]
  }
}
```

---

## 🔧 Maintenance Procedures

### Daily Maintenance Script

```bash
#!/bin/bash
# daily_maintenance.sh

echo "🛠️ Starting daily maintenance..."

# Database maintenance
echo "📊 Running database maintenance..."
docker exec bot-trading-db-master mysql -uroot -p$MYSQL_ROOT_PASSWORD bot_marketplace -e "
OPTIMIZE TABLE users, bots, subscriptions, trades, performance_logs;
ANALYZE TABLE users, bots, subscriptions, trades, performance_logs;
DELETE FROM performance_logs WHERE timestamp < DATE_SUB(NOW(), INTERVAL 90 DAY);
"

# Log rotation
echo "📝 Rotating logs..."
find ./logs -name "*.log" -size +100M -exec gzip {} \;
find ./logs -name "*.gz" -mtime +30 -delete

# Docker cleanup
echo "🐳 Cleaning up Docker..."
docker system prune -f
docker volume prune -f

# Backup database
echo "💾 Creating database backup..."
docker exec bot-trading-db-master mysqldump --single-transaction --routines --triggers \
  -uroot -p$MYSQL_ROOT_PASSWORD bot_marketplace | gzip > "backups/bot_marketplace_$(date +%Y%m%d).sql.gz"

# Upload to S3
aws s3 cp "backups/bot_marketplace_$(date +%Y%m%d).sql.gz" s3://bot-marketplace-backups/daily/

echo "✅ Daily maintenance completed"
```

### Weekly Performance Review

```bash
#!/bin/bash
# weekly_review.sh

echo "📈 Generating weekly performance report..."

# Database performance metrics
docker exec bot-trading-db-master mysql -uroot -p$MYSQL_ROOT_PASSWORD bot_marketplace -e "
SELECT 
    'Total Users' as metric, 
    COUNT(*) as value 
FROM users WHERE is_active = 1
UNION ALL
SELECT 
    'Active Subscriptions' as metric, 
    COUNT(*) as value 
FROM subscriptions WHERE status = 'ACTIVE'
UNION ALL
SELECT 
    'Total Trades This Week' as metric, 
    COUNT(*) as value 
FROM trades WHERE entry_time > DATE_SUB(NOW(), INTERVAL 7 DAY)
UNION ALL
SELECT 
    'Total P&L This Week' as metric, 
    ROUND(SUM(pnl), 2) as value 
FROM trades WHERE entry_time > DATE_SUB(NOW(), INTERVAL 7 DAY);
"

# System resource usage
echo "💻 System Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

echo "📊 Report completed"
```

---

## 🚨 Disaster Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup_strategy.sh

# Full database backup
create_full_backup() {
    local backup_date=$(date +%Y%m%d_%H%M%S)
    local backup_file="full_backup_${backup_date}.sql.gz"
    
    docker exec bot-trading-db-master mysqldump \
        --single-transaction \
        --routines \
        --triggers \
        --all-databases \
        -uroot -p$MYSQL_ROOT_PASSWORD | gzip > "backups/${backup_file}"
    
    # Upload to multiple S3 regions
    aws s3 cp "backups/${backup_file}" s3://bot-marketplace-backups-us-east-1/full/
    aws s3 cp "backups/${backup_file}" s3://bot-marketplace-backups-eu-west-1/full/
    
    echo "Full backup created: ${backup_file}"
}

# Incremental backup
create_incremental_backup() {
    local backup_date=$(date +%Y%m%d_%H%M%S)
    local log_file="incremental_${backup_date}.sql"
    
    # Get binary log files since last backup
    docker exec bot-trading-db-master mysql -uroot -p$MYSQL_ROOT_PASSWORD -e "FLUSH LOGS;"
    docker exec bot-trading-db-master mysqlbinlog /var/lib/mysql/mysql-bin.* > "backups/${log_file}"
    
    gzip "backups/${log_file}"
    aws s3 cp "backups/${log_file}.gz" s3://bot-marketplace-backups-us-east-1/incremental/
    
    echo "Incremental backup created: ${log_file}.gz"
}

# Schedule: Full backup weekly, incremental daily
if [ "$(date +%u)" -eq 7 ]; then
    create_full_backup
else
    create_incremental_backup
fi
```

### Recovery Procedures

```bash
#!/bin/bash
# disaster_recovery.sh

recover_from_backup() {
    local backup_file=$1
    local target_db=${2:-bot_marketplace}
    
    echo "🚨 Starting disaster recovery from backup: $backup_file"
    
    # Stop all services
    docker-compose -f docker-compose.prod.yml down
    
    # Start only database
    docker-compose -f docker-compose.prod.yml up -d db-master
    
    # Wait for database to be ready
    sleep 30
    
    # Restore backup
    echo "📥 Restoring database from backup..."
    gunzip -c "$backup_file" | docker exec -i bot-trading-db-master mysql -uroot -p$MYSQL_ROOT_PASSWORD
    
    # Start all services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Verify restoration
    sleep 60
    if curl -f -s "http://localhost/health" > /dev/null; then
        echo "✅ Disaster recovery completed successfully"
    else
        echo "❌ Disaster recovery failed - manual intervention required"
        exit 1
    fi
}

# Usage: ./disaster_recovery.sh backups/full_backup_20250803_120000.sql.gz
recover_from_backup "$1"
```

---

## 📋 Production Checklist

### Pre-Launch Checklist

- [ ] SSL certificates installed and valid
- [ ] Database master-slave replication configured
- [ ] Redis cluster setup with persistence
- [ ] All environment variables configured
- [ ] Secret management system implemented
- [ ] Monitoring and alerting configured
- [ ] Backup strategy implemented
- [ ] Load balancer configured
- [ ] Rate limiting enabled
- [ ] Security headers configured
- [ ] Performance testing completed
- [ ] Disaster recovery procedures tested

### Security Checklist

- [ ] Database credentials encrypted
- [ ] API keys stored securely
- [ ] HTTPS enforced everywhere
- [ ] SQL injection protection enabled
- [ ] XSS protection configured
- [ ] CORS properly configured
- [ ] Input validation implemented
- [ ] Authentication and authorization working
- [ ] Audit logging enabled
- [ ] Regular security scans scheduled

### Performance Checklist

- [ ] Database indexes optimized
- [ ] Query performance analyzed
- [ ] Caching strategy implemented
- [ ] CDN configured for static assets
- [ ] Application metrics collected
- [ ] Load testing completed
- [ ] Auto-scaling configured
- [ ] Resource limits set
- [ ] Connection pooling optimized
- [ ] Background job processing tuned

---

*This deployment guide ensures a production-ready, secure, and scalable deployment of the Bot Trading Marketplace system with comprehensive monitoring, backup, and disaster recovery capabilities.*