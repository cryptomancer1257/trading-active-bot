#!/usr/bin/env python3
"""
Fix all import paths in the project after reorganization
"""

import os
import sys
import re
from pathlib import Path

def fix_imports_in_file(file_path):
    """Fix imports in a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Import replacements for different file types
        replacements = [
            # Core imports
            (r'from models import', 'from core.models import'),
            (r'from schemas import', 'from core.schemas import'),
            (r'from crud import', 'from core.crud import'),
            (r'from database import', 'from core.database import'),
            (r'from security import', 'from core.security import'),
            (r'from bot_manager import', 'from core.bot_manager import'),
            (r'from bot_base_classes import', 'from core.bot_base_classes import'),
            
            # Services imports
            (r'from binance_integration import', 'from services.binance_integration import'),
            (r'from exchange_factory import', 'from services.exchange_factory import'),
            (r'from s3_manager import', 'from services.s3_manager import'),
            (r'from sendgrid_email_service import', 'from services.sendgrid_email_service import'),
            (r'from gmail_smtp_service import', 'from services.gmail_smtp_service import'),
            (r'from email_templates import', 'from services.email_templates import'),
            (r'from email_service import', 'from services.email_service import'),
            
            # Utils imports
            (r'from celery_app import', 'from utils.celery_app import'),
            (r'from run_celery import', 'from utils.run_celery import'),
            (r'from run_beat import', 'from utils.run_beat import'),
            
            # API imports
            (r'import core.crud, core.schemas, core.security', 'from core import crud, schemas, security'),
            (r'from database import get_db', 'from core.database import get_db'),
            
            # Tasks imports
            (r'import models', 'from core import models'),
            (r'import schemas', 'from core import schemas'),
            (r'import crud', 'from core import crud'),
        ]
        
        # Apply replacements
        for old_pattern, new_pattern in replacements:
            content = re.sub(old_pattern, new_pattern, content)
        
        # Add sys.path.insert for files that need it
        if 'from core import' in content or 'from services import' in content or 'from utils import' in content:
            if 'sys.path.insert' not in content:
                path_insert = """import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

"""
                # Insert after existing imports
                lines = content.split('\n')
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.startswith('import ') or line.startswith('from '):
                        insert_index = i + 1
                    else:
                        break
                
                lines.insert(insert_index, path_insert)
                content = '\n'.join(lines)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        else:
            return False
            
    except Exception as e:
        print(f"   ❌ Error fixing {file_path}: {e}")
        return False

def fix_all_imports():
    """Fix imports in all Python files"""
    print("🔧 Fixing All Import Paths")
    print("=" * 50)
    
    current_dir = Path(__file__).parent
    
    # Files to fix
    files_to_fix = [
        # Core files
        "core/main.py",
        "core/bot_manager.py",
        "core/bot_base_classes.py",
        
        # API endpoints
        "api/endpoints/auth.py",
        "api/endpoints/bots.py",
        "api/endpoints/subscriptions.py",
        "api/endpoints/admin.py",
        "api/endpoints/exchanges.py",
        "api/endpoints/subscriptions_simple.py",
        
        # Services files
        "services/binance_integration.py",
        "services/exchange_factory.py",
        "services/s3_manager.py",
        "services/sendgrid_email_service.py",
        "services/gmail_smtp_service.py",
        "services/email_templates.py",
    ]
    
    fixed_files = []
    errors = []
    
    for file_path in files_to_fix:
        full_path = current_dir / file_path
        if full_path.exists():
            print(f"🔧 Fixing: {file_path}")
            if fix_imports_in_file(full_path):
                fixed_files.append(file_path)
                print(f"   ✅ Fixed: {file_path}")
            else:
                print(f"   ⚠️  No changes needed: {file_path}")
        else:
            print(f"   ⚠️  Not found: {file_path}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Import Fix Summary:")
    print(f"   Files fixed: {len(fixed_files)}")
    print(f"   Errors: {len(errors)}")
    
    if fixed_files:
        print(f"\n✅ Fixed files:")
        for file_path in fixed_files:
            print(f"   • {file_path}")
    
    if errors:
        print(f"\n❌ Errors:")
        for error in errors:
            print(f"   • {error}")
    
    print(f"\n🎉 Import fix completed!")
    print(f"   All import paths should now be correct.")

def test_imports():
    """Test if imports work correctly"""
    print("\n🧪 Testing Imports")
    print("=" * 30)
    
    current_dir = Path(__file__).parent
    
    try:
        # Test core imports
        print("1. Testing core imports...")
        sys.path.insert(0, str(current_dir))
        from core import models, schemas, crud, database, security
        print("   ✅ Core imports successful")
        
        # Test services imports
        print("2. Testing services imports...")
        from services import binance_integration, exchange_factory, s3_manager
        from services import sendgrid_email_service, gmail_smtp_service, email_templates
        print("   ✅ Services imports successful")
        
        # Test utils imports
        print("3. Testing utils imports...")
        from utils import celery_app, run_celery, run_beat
        print("   ✅ Utils imports successful")
        
        # Test API imports
        print("4. Testing API imports...")
        from api.endpoints import auth, bots, subscriptions, admin
        print("   ✅ API imports successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🔧 Bot Marketplace - Import Path Fix")
    print("=" * 50)
    
    # Ask for confirmation
    print("This will fix all import paths in the project.")
    confirm = input("\nContinue with import fix? (y/N): ")
    
    if confirm.lower() not in ['y', 'yes']:
        print("❌ Import fix cancelled.")
        return
    
    try:
        # Fix imports
        fix_all_imports()
        
        # Test imports
        test_imports()
        
    except Exception as e:
        print(f"❌ Import fix failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 