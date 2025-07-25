# Multi-stage Dockerfile for Bot Marketplace
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python packages
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy common application code
COPY core/ ./core/
COPY utils/ ./utils/
COPY services/ ./services/
COPY bots/ ./bots/

# ===== API Service =====
FROM base as api

# Copy API-specific files
COPY main.py .
COPY api/ ./api/

# Expose port for API
EXPOSE 8000

# Health check for API
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ===== Celery Worker =====
FROM base as celery-worker

# Copy worker-specific files
COPY tasks.py .
COPY core/tasks.py ./core/

# Create logs directory
RUN mkdir -p /app/logs

# Health check for Celery worker
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD celery -A utils.celery_app inspect ping || exit 1

# Run Celery worker
CMD ["celery", "-A", "utils.celery_app", "worker", "--loglevel=info", "--concurrency=2"]

# ===== Celery Beat =====
FROM base as celery-beat

# Copy beat-specific files
COPY utils/celery_app.py ./utils/

# Create logs directory
RUN mkdir -p /app/logs

# Health check for Celery beat
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD celery -A utils.celery_app inspect ping || exit 1

# Run Celery beat scheduler
CMD ["celery", "-A", "utils.celery_app", "beat", "--loglevel=info", "--scheduler=django_celery_beat.schedulers:DatabaseScheduler"]

# ===== Development =====
FROM base as dev

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio black flake8

# Copy all files for development
COPY . .

# Expose ports
EXPOSE 8000

# Run in development mode
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]