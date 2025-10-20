# 🐳 Docker Deployment Guide

## 📋 Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- Ports available: 3001, 8000, 3307, 6379

## 🚀 Quick Start

### 1. Build and Start All Services

```bash
docker-compose up -d --build
```

This will start:
- **Frontend** (Next.js) on `http://localhost:3001`
- **Backend API** (FastAPI) on `http://localhost:8000`
- **MySQL Database** on `localhost:3307`
- **Redis** on `localhost:6379`
- **Celery Worker** (background tasks)
- **Celery Beat** (scheduler)

### 2. Check Service Status

```bash
docker-compose ps
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f api
docker-compose logs -f celery
```

### 4. Stop Services

```bash
docker-compose down
```

### 5. Stop and Remove Volumes (Clean Reset)

```bash
docker-compose down -v
```

## 🔧 Service Details

### Frontend Service

- **Container:** `app_frontend`
- **Port:** 3001 (host) → 3000 (container)
- **Build Context:** `./frontend`
- **Environment:**
  - `NEXT_PUBLIC_API_URL=http://api:8000` (internal Docker network)
  - `NODE_ENV=production`

### API Service

- **Container:** `app_api`
- **Port:** 8000 (host) → 8000 (container)
- **Dependencies:** MySQL, Redis, Migration
- **Volumes:** `./logs:/app/logs`

### Database Service

- **Container:** `mysql_db`
- **Port:** 3307 (host) → 3306 (container)
- **Credentials:**
  - Root: `rootpassword123`
  - User: `botuser`
  - Password: `botpassword123`
  - Database: `bot_marketplace`
- **Volume:** `mysql_data` (persistent storage)

### Redis Service

- **Container:** `redis_db`
- **Port:** 6379 (host) → 6379 (container)

### Celery Worker

- **Queues:** `default`, `bot_execution`, `futures_trading`, `maintenance`, `notifications`, `bot_execution_signal`
- **Development Mode:** Enabled (loads bots from local files)
- **Volumes:**
  - `./logs:/app/logs`
  - `./bot_files:/app/bot_files`
  - `./services:/app/services`

### Celery Beat

- **Purpose:** Scheduler for periodic tasks
- **Dependencies:** MySQL, Redis

## 🛠️ Development Commands

### Rebuild Specific Service

```bash
# Rebuild frontend only
docker-compose up -d --build frontend

# Rebuild API only
docker-compose up -d --build api
```

### Access Container Shell

```bash
# Frontend
docker exec -it app_frontend sh

# API
docker exec -it app_api bash

# Database
docker exec -it mysql_db mysql -u botuser -p
```

### Run Migrations Manually

```bash
docker-compose run --rm migration
```

### Check Database

```bash
docker exec -it mysql_db mysql -u botuser -pbotpassword123 bot_marketplace
```

## 🔒 Environment Variables

Create a `.env` file in the root directory:

```env
# Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_WEBHOOK_URL=your_webhook_url

# Discord
DISCORD_BOT_TOKEN=your_discord_bot_token

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Development
MODE=dev
DEVELOPMENT_MODE=true
DEV_BOT_IDS=55
```

## 📊 Monitoring

### View Resource Usage

```bash
docker stats
```

### Check Service Health

```bash
# API Health
curl http://localhost:8000/health

# Frontend
curl http://localhost:3001
```

## 🐛 Troubleshooting

### Frontend Can't Connect to API

**Problem:** Browser shows CORS errors or connection refused

**Solution:**
- Check if API container is running: `docker-compose ps`
- Verify API is accessible: `curl http://localhost:8000/health`
- Check frontend logs: `docker-compose logs frontend`

### Database Connection Failed

**Problem:** API can't connect to MySQL

**Solution:**
- Wait for MySQL to be ready (takes ~30 seconds on first start)
- Check database logs: `docker-compose logs db`
- Restart API: `docker-compose restart api`

### Port Already in Use

**Problem:** `Bind for 0.0.0.0:3001 failed: port is already allocated`

**Solution:**
- Find process using the port: `lsof -i :3001`
- Kill the process or change port in `docker-compose.yml`

### Celery Worker Not Processing Tasks

**Problem:** Tasks stuck in queue

**Solution:**
- Check Redis connection: `docker-compose logs redis`
- Restart Celery worker: `docker-compose restart celery`
- Check worker logs: `docker-compose logs celery`

### Migration Failed

**Problem:** Database schema errors

**Solution:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d db
sleep 30
docker-compose up migration
docker-compose up -d
```

## 📦 Production Deployment

For production, update:

1. **Security:**
   - Change all default passwords
   - Use secrets management
   - Enable SSL/TLS

2. **Performance:**
   - Use production-grade database (AWS RDS, etc.)
   - Add reverse proxy (Nginx)
   - Enable caching

3. **Scalability:**
   - Scale Celery workers: `docker-compose up -d --scale celery=3`
   - Use managed Redis (AWS ElastiCache)
   - Add load balancer

## 🔄 Update Deployment

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build

# Run new migrations
docker-compose run --rm migration
```

## 🧹 Cleanup

```bash
# Remove stopped containers
docker-compose rm

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

## 📝 Notes

- First startup takes 2-3 minutes for database initialization
- Frontend build takes ~5 minutes
- Logs are stored in `./logs` directory
- Database data persists in `mysql_data` volume
- Development mode is enabled for Celery (loads local bot files)

## 🆘 Support

For issues:
1. Check logs: `docker-compose logs [service]`
2. Verify environment variables
3. Ensure all ports are available
4. Check Docker resources (memory, disk space)

