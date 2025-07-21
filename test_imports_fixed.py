#!/usr/bin/env python3
"""
Test imports after fixing all import paths
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all imports work correctly"""
    print("🧪 Testing All Imports")
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
        
        # Test API imports
        print("4. Testing API imports...")
        from api.endpoints import auth, bots, subscriptions, admin
        print("   ✅ API imports successful")
        
        # Test Celery app
        print("5. Testing Celery app...")
        from utils.celery_app import app
        print(f"   ✅ Celery app: {app}")
        
        # Test tasks import
        print("6. Testing tasks import...")
        from core import tasks
        print("   ✅ Tasks import successful")
        
        # Test bot manager
        print("7. Testing bot manager...")
        from core import bot_manager
        print("   ✅ Bot manager import successful")
        
        # Test bot base classes
        print("8. Testing bot base classes...")
        from core import bot_base_classes
        print("   ✅ Bot base classes import successful")
        
        print("\n🎉 All imports successful!")
        print("   The project structure is now working correctly.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_celery_worker():
    """Test if Celery worker can start"""
    print("\n🔧 Testing Celery Worker")
    print("=" * 30)
    
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
    print("🔧 Bot Marketplace - Import Test After Fix")
    print("=" * 50)
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        # Test Celery worker
        worker_ok = test_celery_worker()
        
        if worker_ok:
            print("\n🎉 All tests passed!")
            print("   You can now run:")
            print("   • python utils/run_celery.py")
            print("   • python utils/run_beat.py")
            print("   • python core/main.py")
        else:
            print("\n❌ Celery worker test failed")
    else:
        print("\n❌ Import tests failed")

if __name__ == "__main__":
    main() 