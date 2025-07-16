#!/usr/bin/env python3
"""
Script to fix GitHub secrets push protection issue
"""

import os
import subprocess
import shutil

def backup_env_file():
    """Backup current .env file"""
    if os.path.exists('.env'):
        shutil.copy('.env', '.env.backup')
        print("✓ Backed up .env to .env.backup")

def remove_secrets_from_files():
    """Remove secrets from files that will be committed"""
    
    files_to_clean = [
        '.env',
        'config.env',
        'docker-compose.yml'
    ]
    
    print("Removing secrets from files...")
    
    for file in files_to_clean:
        if os.path.exists(file):
            print(f"  Removing {file}...")
            os.remove(file)
    
    print("✓ Removed files with secrets")

def create_safe_config_files():
    """Create safe configuration files with placeholders"""
    
    # Create .env.example
    env_example = """# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/bot_marketplace

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your-bot-marketplace-bucket

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password_here
EMAIL_USE_TLS=true

# Binance API Configuration (for testing)
BINANCE_API_KEY=your_binance_testnet_api_key
BINANCE_API_SECRET=your_binance_testnet_secret_key
BINANCE_TESTNET=true

# JWT Configuration
SECRET_KEY=your_super_secret_jwt_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Bot Configuration
BOT_EXECUTION_INTERVAL=300
MAX_CONCURRENT_BOTS=10
DEFAULT_STOP_LOSS=0.02
DEFAULT_TAKE_PROFIT=0.04

# Environment
ENVIRONMENT=development
DEBUG=true
"""
    
    with open('.env.example', 'w') as f:
        f.write(env_example)
    
    print("✓ Created .env.example")
    
    # Create safe docker-compose.yml
    docker_compose = """version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=\${DATABASE_NAME:-bot_marketplace}
      - POSTGRES_USER=\${DATABASE_USER:-admin}
      - POSTGRES_PASSWORD=\${DATABASE_PASSWORD:-password}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U \${DATABASE_USER:-admin} -d \${DATABASE_NAME:-bot_marketplace}"]
      interval: 5s
      timeout: 5s
      retries: 5

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      - DATABASE_URL=postgresql://\${DATABASE_USER:-admin}:\${DATABASE_PASSWORD:-password}@postgres:5432/\${DATABASE_NAME:-bot_marketplace}
      - REDIS_URL=redis://redis:6379/0
      - AWS_ACCESS_KEY_ID=\${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=\${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=\${AWS_REGION:-us-east-1}
      - AWS_S3_BUCKET=\${AWS_S3_BUCKET}
      - EMAIL_HOST=\${EMAIL_HOST}
      - EMAIL_PORT=\${EMAIL_PORT:-587}
      - EMAIL_HOST_USER=\${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=\${EMAIL_HOST_PASSWORD}
      - EMAIL_USE_TLS=\${EMAIL_USE_TLS:-true}
      - BINANCE_API_KEY=\${BINANCE_API_KEY}
      - BINANCE_API_SECRET=\${BINANCE_API_SECRET}
      - BINANCE_TESTNET=\${BINANCE_TESTNET:-true}
      - SECRET_KEY=\${SECRET_KEY}
      - ALGORITHM=\${ALGORITHM:-HS256}
      - ACCESS_TOKEN_EXPIRE_MINUTES=\${ACCESS_TOKEN_EXPIRE_MINUTES:-30}
      - ENVIRONMENT=\${ENVIRONMENT:-development}
      - DEBUG=\${DEBUG:-true}
    volumes:
      - ./:/app
    command: python main.py

  celery_worker:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      - DATABASE_URL=postgresql://\${DATABASE_USER:-admin}:\${DATABASE_PASSWORD:-password}@postgres:5432/\${DATABASE_NAME:-bot_marketplace}
      - REDIS_URL=redis://redis:6379/0
      - AWS_ACCESS_KEY_ID=\${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=\${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=\${AWS_REGION:-us-east-1}
      - AWS_S3_BUCKET=\${AWS_S3_BUCKET}
      - EMAIL_HOST=\${EMAIL_HOST}
      - EMAIL_PORT=\${EMAIL_PORT:-587}
      - EMAIL_HOST_USER=\${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=\${EMAIL_HOST_PASSWORD}
      - EMAIL_USE_TLS=\${EMAIL_USE_TLS:-true}
      - BINANCE_API_KEY=\${BINANCE_API_KEY}
      - BINANCE_API_SECRET=\${BINANCE_API_SECRET}
      - BINANCE_TESTNET=\${BINANCE_TESTNET:-true}
      - SECRET_KEY=\${SECRET_KEY}
      - ENVIRONMENT=\${ENVIRONMENT:-development}
    volumes:
      - ./:/app
    command: celery -A tasks worker --loglevel=info --concurrency=4

  celery_beat:
    build: .
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    environment:
      - DATABASE_URL=postgresql://\${DATABASE_USER:-admin}:\${DATABASE_PASSWORD:-password}@postgres:5432/\${DATABASE_NAME:-bot_marketplace}
      - REDIS_URL=redis://redis:6379/0
      - AWS_ACCESS_KEY_ID=\${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=\${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION=\${AWS_REGION:-us-east-1}
      - AWS_S3_BUCKET=\${AWS_S3_BUCKET}
      - EMAIL_HOST=\${EMAIL_HOST}
      - EMAIL_PORT=\${EMAIL_PORT:-587}
      - EMAIL_HOST_USER=\${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=\${EMAIL_HOST_PASSWORD}
      - EMAIL_USE_TLS=\${EMAIL_USE_TLS:-true}
      - BINANCE_API_KEY=\${BINANCE_API_KEY}
      - BINANCE_API_SECRET=\${BINANCE_API_SECRET}
      - BINANCE_TESTNET=\${BINANCE_TESTNET:-true}
      - SECRET_KEY=\${SECRET_KEY}
      - ENVIRONMENT=\${ENVIRONMENT:-development}
    volumes:
      - ./:/app
    command: celery -A tasks beat --loglevel=info

volumes:
  postgres_data:
  redis_data:
"""
    
    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    
    print("✓ Created safe docker-compose.yml")

def update_gitignore():
    """Update .gitignore to prevent future secrets"""
    
    gitignore_additions = """
# Environment files with secrets
.env
.env.local
.env.*.local
config.env
docker.env

# Backup files
*.backup
*.bak

# AWS credentials
.aws/
aws_credentials.json

# API keys
api_keys.json
credentials.json
"""
    
    with open('.gitignore', 'a') as f:
        f.write(gitignore_additions)
    
    print("✓ Updated .gitignore")

def git_cleanup():
    """Clean up git history"""
    
    print("Git cleanup options:")
    print("1. Soft reset (recommended): git reset --soft HEAD~1")
    print("2. Hard reset: git reset --hard HEAD~1")
    print("3. Remove from staging: git rm --cached .env config.env")
    
    print("\nRecommended git commands:")
    print("git reset --soft HEAD~1")
    print("git rm --cached .env config.env docker-compose.yml")
    print("git add .env.example docker-compose.yml .gitignore")
    print("git commit -m 'Remove secrets and add safe config files'")
    print("git push origin main")

def main():
    """Main function"""
    
    print("=== GitHub Secrets Fix Script ===\n")
    
    # Backup current files
    backup_env_file()
    
    # Remove files with secrets
    remove_secrets_from_files()
    
    # Create safe configuration files
    create_safe_config_files()
    
    # Update .gitignore
    update_gitignore()
    
    # Git cleanup instructions
    git_cleanup()
    
    print("\n=== Instructions ===")
    print("1. Copy your credentials from .env.backup to new .env file")
    print("2. Run git commands shown above")
    print("3. Never commit .env file again")
    print("4. Use .env.example as template for new developers")
    
    print("\n✓ Secrets fix completed!")

if __name__ == "__main__":
    main() 