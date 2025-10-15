# Dockerfile for QuantumForge Documentation Server

FROM python:3.11-slim

# Set working directory
WORKDIR /docs

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy documentation files
COPY . .

# Expose port
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3002/ || exit 1

# Start MkDocs server
CMD ["mkdocs", "serve", "--dev-addr=0.0.0.0:3002"]

