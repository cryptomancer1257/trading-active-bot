#!/usr/bin/env python3
"""
Fix reorganization and complete the process
"""

import os
import shutil
import sys
from pathlib import Path

def fix_encoding_issue():
    """Fix the encoding issue in README creation"""
    print("🔧 Fixing Encoding Issue")
    print("=" * 40)
    
    current_dir = Path(__file__).parent
    
    # Create new README.md without emoji to avoid encoding issues
    new_readme_content = '''# Trading Bot Marketplace

A comprehensive backend marketplace for trading bot rental.

## Project Structure

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
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Quick Start

```bash
# Start with Docker
docker-compose up -d

# Or run manually
pip install -r config/requirements.txt
python main.py
```

## Documentation

See `docs/` folder for detailed documentation.
'''
    
    try:
        with open(current_dir / "README.md", "w", encoding="utf-8") as f:
            f.write(new_readme_content)
        print("   ✅ Created: README.md (fixed encoding)")
    except Exception as e:
        print(f"   ❌ Error creating README.md: {e}")

def cleanup_cache_files():
    """Remove remaining cache files"""
    print("\n🧹 Cleaning remaining cache files:")
    
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

def update_imports():
    """Update import statements in moved files"""
    print("\n📝 Updating import statements:")
    
    current_dir = Path(__file__).parent
    
    # Files that need import updates
    files_to_update = [
        ("core/main.py", [
            ("from core.database import engine", "from database import engine"),
            ("from core.models import Base", "from models import Base"),
            ("from api.endpoints import auth, bots, subscriptions, admin", "from api.endpoints import auth, bots, subscriptions, admin"),
        ]),
        ("core/tasks.py", [
            ("from core.models import", "from models import"),
            ("from core.schemas import", "from schemas import"),
            ("from core.crud import", "from crud import"),
            ("from core.database import", "from database import"),
            ("from services.binance_integration import", "from binance_integration import"),
            ("from services.exchange_factory import", "from exchange_factory import"),
            ("from services.s3_manager import", "from s3_manager import"),
            ("from services.email_templates import", "from email_templates import"),
        ]),
        ("core/bot_manager.py", [
            ("from core.models import", "from models import"),
            ("from core.schemas import", "from schemas import"),
            ("from core.crud import", "from crud import"),
            ("from services.s3_manager import", "from s3_manager import"),
        ]),
    ]
    
    updated_files = []
    
    for file_path, replacements in files_to_update:
        full_path = current_dir / file_path
        if full_path.exists():
            try:
                # Read file content
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Apply replacements
                original_content = content
                for old_import, new_import in replacements:
                    content = content.replace(old_import, new_import)
                
                # Write back if changed
                if content != original_content:
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    updated_files.append(file_path)
                    print(f"   ✅ Updated: {file_path}")
                else:
                    print(f"   ⚠️  No changes needed: {file_path}")
                    
            except Exception as e:
                print(f"   ❌ Error updating {file_path}: {e}")
        else:
            print(f"   ⚠️  Not found: {file_path}")
    
    return updated_files

def create_init_files():
    """Create __init__.py files for Python packages"""
    print("\n📦 Creating __init__.py files:")
    
    current_dir = Path(__file__).parent
    
    init_dirs = [
        "core",
        "services", 
        "utils",
        "config",
        "scripts",
        "tests",
        "docs",
        "logs",
        "temp",
    ]
    
    created_files = []
    
    for dir_name in init_dirs:
        init_path = current_dir / dir_name / "__init__.py"
        if not init_path.exists():
            try:
                init_path.touch()
                created_files.append(f"{dir_name}/__init__.py")
                print(f"   ✅ Created: {dir_name}/__init__.py")
            except Exception as e:
                print(f"   ❌ Error creating {dir_name}/__init__.py: {e}")
        else:
            print(f"   ⚠️  Exists: {dir_name}/__init__.py")
    
    return created_files

def check_structure():
    """Check the final structure"""
    print("\n📋 Final Structure Check:")
    
    current_dir = Path(__file__).parent
    
    expected_structure = {
        "core": ["main.py", "tasks.py", "models.py", "schemas.py", "crud.py", "database.py", "security.py", "bot_manager.py", "bot_base_classes.py"],
        "services": ["binance_integration.py", "exchange_factory.py", "s3_manager.py", "sendgrid_email_service.py", "gmail_smtp_service.py", "email_templates.py"],
        "utils": ["celery_app.py", "run_beat.py", "run_celery.py"],
        "config": ["docker.env", "requirements.txt"],
        "tests": ["test_binance.py"],
        "docs": ["README.md"],
    }
    
    missing_files = []
    existing_files = []
    
    for dir_name, expected_files in expected_structure.items():
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/")
            for file_name in expected_files:
                file_path = dir_path / file_name
                if file_path.exists():
                    existing_files.append(f"{dir_name}/{file_name}")
                    print(f"      ✅ {file_name}")
                else:
                    missing_files.append(f"{dir_name}/{file_name}")
                    print(f"      ❌ Missing: {file_name}")
        else:
            print(f"   ❌ Missing directory: {dir_name}/")
    
    return existing_files, missing_files

def main():
    """Main fix function"""
    print("🔧 Bot Marketplace - Fix Reorganization")
    print("=" * 50)
    
    try:
        # Step 1: Fix encoding issue
        fix_encoding_issue()
        
        # Step 2: Clean up cache files
        deleted_items = cleanup_cache_files()
        
        # Step 3: Update imports
        updated_files = update_imports()
        
        # Step 4: Create __init__.py files
        created_files = create_init_files()
        
        # Step 5: Check final structure
        existing_files, missing_files = check_structure()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Fix Summary:")
        print(f"   Files updated: {len(updated_files)}")
        print(f"   Files created: {len(created_files)}")
        print(f"   Items deleted: {len(deleted_items)}")
        print(f"   Files existing: {len(existing_files)}")
        print(f"   Files missing: {len(missing_files)}")
        
        if updated_files:
            print(f"\n📝 Updated files:")
            for file_path in updated_files:
                print(f"   • {file_path}")
        
        if created_files:
            print(f"\n📦 Created files:")
            for file_path in created_files:
                print(f"   • {file_path}")
        
        if deleted_items:
            print(f"\n🗑️  Deleted items:")
            for item in deleted_items:
                print(f"   • {item}")
        
        if missing_files:
            print(f"\n❌ Missing files:")
            for file_path in missing_files:
                print(f"   • {file_path}")
        
        print(f"\n🎉 Reorganization completed!")
        print(f"   Project structure is now organized and clean.")
        print(f"   You can now run: python main.py")
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 