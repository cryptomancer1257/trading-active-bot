#!/usr/bin/env python3
"""
Reorganize project structure for better organization
"""

import os
import shutil
import sys
from pathlib import Path

def create_directory_structure():
    """Create new directory structure"""
    print("📁 Reorganizing Project Structure")
    print("=" * 50)
    
    current_dir = Path(__file__).parent
    
    # New directory structure
    directories = [
        "core",           # Core application files
        "services",       # External services
        "utils",          # Utility functions
        "config",         # Configuration files
        "scripts",        # Utility scripts
        "tests",          # Test files
        "docs",           # Documentation
        "logs",           # Log files
        "temp",           # Temporary files
    ]
    
    # Create directories
    for dir_name in directories:
        dir_path = current_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir()
            print(f"   ✅ Created: {dir_name}/")
        else:
            print(f"   ⚠️  Exists: {dir_name}/")

def move_files_to_new_structure():
    """Move files to new organized structure"""
    print("\n📦 Moving files to new structure:")
    
    current_dir = Path(__file__).parent
    
    # File movements: (source, destination)
    file_movements = [
        # Core files
        ("main.py", "core/main.py"),
        ("tasks.py", "core/tasks.py"),
        ("models.py", "core/models.py"),
        ("schemas.py", "core/schemas.py"),
        ("crud.py", "core/crud.py"),
        ("database.py", "core/database.py"),
        ("security.py", "core/security.py"),
        ("bot_manager.py", "core/bot_manager.py"),
        ("bot_base_classes.py", "core/bot_base_classes.py"),
        
        # Services
        ("binance_integration.py", "services/binance_integration.py"),
        ("exchange_factory.py", "services/exchange_factory.py"),
        ("s3_manager.py", "services/s3_manager.py"),
        ("sendgrid_email_service.py", "services/sendgrid_email_service.py"),
        ("gmail_smtp_service.py", "services/gmail_smtp_service.py"),
        ("email_templates.py", "services/email_templates.py"),
        
        # Utils
        ("celery_app.py", "utils/celery_app.py"),
        ("run_beat.py", "utils/run_beat.py"),
        ("run_celery.py", "utils/run_celery.py"),
        
        # Config
        ("docker.env", "config/docker.env"),
        ("requirements.txt", "config/requirements.txt"),
        
        # Scripts
        ("cleanup_remaining.py", "scripts/cleanup_remaining.py"),
        
        # Tests
        ("test.py", "tests/test_binance.py"),
        
        # Docs
        ("README.md", "docs/README.md"),
        
        # Temp
        ("alternating_bot_state_BTC_USDT.json", "temp/alternating_bot_state_BTC_USDT.json"),
    ]
    
    moved_files = []
    errors = []
    
    for source, destination in file_movements:
        source_path = current_dir / source
        dest_path = current_dir / destination
        
        if source_path.exists():
            try:
                # Create destination directory if needed
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move file
                shutil.move(str(source_path), str(dest_path))
                moved_files.append((source, destination))
                print(f"   ✅ Moved: {source} → {destination}")
            except Exception as e:
                errors.append(f"Failed to move {source}: {e}")
                print(f"   ❌ Error moving {source}: {e}")
        else:
            print(f"   ⚠️  Not found: {source}")
    
    return moved_files, errors

def create_new_main_files():
    """Create new main files with updated imports"""
    print("\n📝 Creating new main files:")
    
    current_dir = Path(__file__).parent
    
    # Create new main.py with updated imports
    new_main_content = '''#!/usr/bin/env python3
"""
Trading Bot Marketplace - Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import from new structure
from core.database import engine
from core.models import Base
from api.endpoints import auth, bots, subscriptions, admin

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Trading Bot Marketplace",
    description="A comprehensive marketplace for trading bot rental",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(bots.router, prefix="/bots", tags=["Bots"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

@app.get("/")
async def root():
    return {"message": "Trading Bot Marketplace API", "version": "2.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
'''
    
    with open(current_dir / "main.py", "w") as f:
        f.write(new_main_content)
    print("   ✅ Created: main.py (updated imports)")
    
    # Create new requirements.txt with organized structure
    new_requirements_content = '''# Core Dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pymysql==1.1.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Background Tasks
celery==5.3.4
redis==5.0.1

# External Services
boto3==1.34.0
sendgrid==6.10.0
ccxt==4.1.77
requests==2.31.0

# Data Processing
pandas==2.1.4
numpy==1.25.2

# Utilities
python-dotenv==1.0.0
jinja2==3.1.2
python-dateutil==2.8.2

# Development
pytest==7.4.3
pytest-asyncio==0.21.1
'''
    
    with open(current_dir / "requirements.txt", "w") as f:
        f.write(new_requirements_content)
    print("   ✅ Created: requirements.txt (organized)")
    
    # Create new docker-compose.yml
    new_docker_compose = '''version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@db/bot_marketplace
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  celery:
    build: .
    command: celery -A utils.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@db/bot_marketplace
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  beat:
    build: .
    command: celery -A utils.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=mysql+pymysql://user:password@db/bot_marketplace
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: bot_marketplace
      MYSQL_USER: user
      MYSQL_PASSWORD: password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  mysql_data:
'''
    
    with open(current_dir / "docker-compose.yml", "w") as f:
        f.write(new_docker_compose)
    print("   ✅ Created: docker-compose.yml (updated)")
    
    # Create new README.md
    new_readme_content = '''# 🤖 Trading Bot Marketplace

A comprehensive backend marketplace for trading bot rental.

## 📁 Project Structure

```
bot_marketplace/
├── core/                 # Core application files
│   ├── main.py          # FastAPI application
│   ├── tasks.py         # Celery background tasks
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   ├── database.py      # Database configuration
│   ├── security.py      # Authentication
│   ├── bot_manager.py   # Bot lifecycle management
│   └── bot_base_classes.py # Base classes loader
├── services/            # External services
│   ├── binance_integration.py
│   ├── exchange_factory.py
│   ├── s3_manager.py
│   ├── sendgrid_email_service.py
│   ├── gmail_smtp_service.py
│   └── email_templates.py
├── utils/               # Utility functions
│   ├── celery_app.py
│   ├── run_beat.py
│   └── run_celery.py
├── api/                 # API endpoints
│   └── endpoints/
├── bots/                # Bot SDK and examples
│   └── bot_sdk/
├── config/              # Configuration files
│   ├── docker.env
│   └── requirements.txt
├── scripts/             # Utility scripts
├── tests/               # Test files
├── docs/                # Documentation
├── logs/                # Log files
├── temp/                # Temporary files
└── docker-compose.yml
```

## 🚀 Quick Start

```bash
# Start with Docker
docker-compose up -d

# Or run manually
pip install -r config/requirements.txt
python main.py
```

## 📚 Documentation

See `docs/` folder for detailed documentation.
'''
    
    with open(current_dir / "README.md", "w") as f:
        f.write(new_readme_content)
    print("   ✅ Created: README.md (simplified)")

def cleanup_cache_files():
    """Remove cache files"""
    print("\n🧹 Cleaning cache files:")
    
    current_dir = Path(__file__).parent
    
    cache_dirs = [
        "__pycache__",
        "api/__pycache__",
        "bots/__pycache__",
        "bots/bot_sdk/__pycache__",
    ]
    
    celery_files = [
        "celerybeat-schedule.dat",
        "celerybeat-schedule.dir",
        "celerybeat-schedule.bak",
    ]
    
    deleted_items = []
    
    # Delete cache directories
    for cache_dir in cache_dirs:
        cache_path = current_dir / cache_dir
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                deleted_items.append(cache_dir)
                print(f"   ✅ Deleted: {cache_dir}/")
            except Exception as e:
                print(f"   ❌ Error deleting {cache_dir}: {e}")
    
    # Delete celery files
    for celery_file in celery_files:
        celery_path = current_dir / celery_file
        if celery_path.exists():
            try:
                celery_path.unlink()
                deleted_items.append(celery_file)
                print(f"   ✅ Deleted: {celery_file}")
            except Exception as e:
                print(f"   ❌ Error deleting {celery_file}: {e}")
    
    return deleted_items

def main():
    """Main reorganization function"""
    print("🔄 Bot Marketplace - Project Reorganization")
    print("=" * 60)
    
    # Ask for confirmation
    print("This will reorganize the project structure:")
    print("1. Create new organized directories")
    print("2. Move files to appropriate locations")
    print("3. Update import paths")
    print("4. Clean up cache files")
    print("5. Create new configuration files")
    
    confirm = input("\nContinue with reorganization? (y/N): ")
    
    if confirm.lower() not in ['y', 'yes']:
        print("❌ Reorganization cancelled.")
        return
    
    try:
        # Step 1: Create directory structure
        create_directory_structure()
        
        # Step 2: Move files
        moved_files, errors = move_files_to_new_structure()
        
        # Step 3: Create new main files
        create_new_main_files()
        
        # Step 4: Clean up cache
        deleted_items = cleanup_cache_files()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Reorganization Summary:")
        print(f"   Files moved: {len(moved_files)}")
        print(f"   Items deleted: {len(deleted_items)}")
        print(f"   Errors: {len(errors)}")
        
        if moved_files:
            print(f"\n📦 Moved files:")
            for source, destination in moved_files:
                print(f"   • {source} → {destination}")
        
        if deleted_items:
            print(f"\n🗑️  Deleted items:")
            for item in deleted_items:
                print(f"   • {item}")
        
        if errors:
            print(f"\n❌ Errors:")
            for error in errors:
                print(f"   • {error}")
        
        print(f"\n🎉 Reorganization completed!")
        print(f"   Project structure is now organized and clean.")
        print(f"   Check the new README.md for updated structure.")
        
    except Exception as e:
        print(f"❌ Reorganization failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 