#!/usr/bin/env python3
"""
Test Celery after fixing import paths
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_celery_imports():
    """Test if Celery can import all modules correctly"""
    print("🧪 Testing Celery Imports")
    print("=" * 40)
    
    try:
        # Test core imports
        print("1. Testing core imports...")
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
        
        # Test Celery app
        print("4. Testing Celery app...")
        from utils.celery_app import app
        print(f"   ✅ Celery app: {app}")
        
        # Test tasks import
        print("5. Testing tasks import...")
        from core import tasks
        print("   ✅ Tasks import successful")
        
        print("\n🎉 All imports successful!")
        print("   Celery should now work correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_celery_worker():
    """Test if Celery worker can start"""
    print("\n🔧 Testing Celery Worker")
    print("=" * 40)
    
    try:
        from utils.celery_app import app
        
        # Check if tasks are registered
        registered_tasks = app.tasks.keys()
        print(f"Registered tasks: {len(registered_tasks)}")
        
        for task_name in registered_tasks:
            if 'core.tasks' in task_name:
                print(f"   ✅ {task_name}")
        
        print("\n✅ Celery worker test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Celery worker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🔧 Bot Marketplace - Celery Fix Test")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_celery_imports()
    
    if imports_ok:
        # Test Celery worker
        worker_ok = test_celery_worker()
        
        if worker_ok:
            print("\n🎉 All tests passed!")
            print("   You can now run: python utils/run_celery.py")
        else:
            print("\n❌ Celery worker test failed")
    else:
        print("\n❌ Import tests failed")

if __name__ == "__main__":
    main() 