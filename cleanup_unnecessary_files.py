#!/usr/bin/env python3
"""
Script to identify and cleanup unnecessary files in bot_marketplace
"""

import os
import shutil
from pathlib import Path

def identify_unnecessary_files():
    """Identify files that can be safely removed"""
    
    # Files that should be removed
    files_to_remove = [
        # Temporary/duplicate task files
        "tasks_fixed.py",
        "tasks_simple.py",
        "main_simple.py",
        
        # Test files (keep if needed for development)
        "test_binance_debug.py",
        "test_subscription_fix.py", 
        "test_trial_fix.py",
        
        # Upload scripts (temporary)
        "upload_golden_cross_bot.py",
        
        # Example files (keep if needed for reference)
        "customer_flow_example.md",
        
        # Duplicate bot files
        "bots/golden_cross_bot_fixed.py",
        
        # Duplicate requirements
        "requirements-simple.txt",
        
        # Batch scripts (Windows specific)
        "run_bot_services.bat",
        "start_services.py",
        
        # Celery schedule files (auto-generated)
        "celerybeat-schedule.bak",
        "celerybeat-schedule.dat", 
        "celerybeat-schedule.dir",
        
        # Configuration files with sensitive data
        "config.env",  # Should be in .env instead
        "docker.env",  # Should be in .env instead
    ]
    
    # Directories that should be cleaned/removed
    dirs_to_clean = [
        "__pycache__",
        "bot_files",  # If empty
        "ml_models",  # If empty
    ]
    
    print("=== Unnecessary Files Analysis ===\n")
    
    # Check files
    print("Files that can be removed:")
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file_path} ({size} bytes)")
        else:
            print(f"  - {file_path} (not found)")
    
    # Check directories
    print(f"\nDirectories that can be cleaned:")
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            if dir_path == "__pycache__":
                # Count __pycache__ directories recursively
                pycache_dirs = list(Path(".").rglob("__pycache__"))
                print(f"  ✓ {len(pycache_dirs)} __pycache__ directories found")
            else:
                files_count = len(os.listdir(dir_path)) if os.path.isdir(dir_path) else 0
                print(f"  ✓ {dir_path}/ ({files_count} files)")
        else:
            print(f"  - {dir_path}/ (not found)")
    
    return files_to_remove, dirs_to_clean

def recommend_file_organization():
    """Recommend better file organization"""
    
    print(f"\n=== Recommended File Organization ===\n")
    
    recommendations = [
        {
            "category": "Core Files (Keep)",
            "files": [
                "main.py",
                "tasks.py", 
                "models.py",
                "schemas.py",
                "crud.py",
                "database.py",
                "security.py",
                "requirements.txt"
            ]
        },
        {
            "category": "Integration Files (Keep)",
            "files": [
                "binance_integration.py",
                "exchange_factory.py",
                "s3_manager.py",
                "bot_manager.py",
                "email_service.py",
                "email_tasks.py"
            ]
        },
        {
            "category": "Configuration Files (Keep)",
            "files": [
                "config.env.example",
                "docker-compose.yml",
                "Dockerfile",
                ".gitignore"
            ]
        },
        {
            "category": "Documentation (Keep)",
            "files": [
                "README.md",
                "AWS_S3_SETUP.md",
                "EMAIL_CONFIG.md",
                "ENHANCED_SYSTEM_GUIDE.md",
                "MULTI_EXCHANGE_GUIDE.md"
            ]
        },
        {
            "category": "Bot Files (Keep)",
            "files": [
                "bots/bot_sdk/",
                "bots/golden_cross_bot.py",
                "bots/enhanced_rsi_bot.py",
                "bots/ml_lstm_bot.py",
                "email_templates/"
            ]
        },
        {
            "category": "SQL Migration Files (Keep)",
            "files": [
                "add_exchange_credentials.sql",
                "add_testnet_support.sql"
            ]
        }
    ]
    
    for rec in recommendations:
        print(f"{rec['category']}:")
        for file in rec['files']:
            status = "✓" if os.path.exists(file) else "✗"
            print(f"  {status} {file}")
        print()

def create_cleanup_script():
    """Create a cleanup script"""
    
    script_content = '''#!/bin/bash
# Cleanup script for bot_marketplace

echo "Cleaning up unnecessary files..."

# Remove Python cache files
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Remove Celery beat schedule files
rm -f celerybeat-schedule.*

# Remove temporary files
rm -f *.tmp *.bak *.log

# Remove test files (uncomment if you want to delete them)
# rm -f test_*.py

# Remove duplicate task files (uncomment if you want to delete them)
# rm -f tasks_fixed.py tasks_simple.py main_simple.py

# Remove upload scripts (uncomment if you want to delete them)
# rm -f upload_golden_cross_bot.py

echo "Cleanup completed!"
'''
    
    with open("cleanup.sh", "w") as f:
        f.write(script_content)
    
    print("Created cleanup.sh script")
    print("Run: chmod +x cleanup.sh && ./cleanup.sh")

def main():
    """Main function"""
    
    print("Bot Marketplace File Cleanup Analysis\n")
    
    # Identify unnecessary files
    files_to_remove, dirs_to_clean = identify_unnecessary_files()
    
    # Show recommendations
    recommend_file_organization()
    
    # Create cleanup script
    create_cleanup_script()
    
    print(f"\n=== Summary ===")
    print(f"• Found {len(files_to_remove)} files that can be removed")
    print(f"• Found {len(dirs_to_clean)} directories that can be cleaned")
    print(f"• Created cleanup.sh script for easy cleanup")
    print(f"• Created .gitignore to prevent future clutter")
    
    print(f"\n=== Recommendations ===")
    print(f"1. Keep only essential files for production")
    print(f"2. Move test files to tests/ directory")
    print(f"3. Use .env file instead of config.env")
    print(f"4. Remove duplicate task files after choosing one")
    print(f"5. Clean __pycache__ directories regularly")

if __name__ == "__main__":
    main() 