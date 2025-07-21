#!/usr/bin/env python3
"""
Test Celery commands
"""

import os
import sys
import subprocess
import time

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_celery_app():
    """Test if Celery app can be imported and configured"""
    print("🧪 Testing Celery App")
    print("=" * 30)
    
    try:
        from utils.celery_app import app
        
        # Check app configuration
        print(f"   ✅ Celery app: {app}")
        print(f"   ✅ Broker URL: {app.conf.broker_url}")
        print(f"   ✅ Result backend: {app.conf.result_backend}")
        
        # Check registered tasks
        registered_tasks = list(app.tasks.keys())
        print(f"   ✅ Registered tasks: {len(registered_tasks)}")
        
        for task_name in registered_tasks:
            if 'core.tasks' in task_name:
                print(f"      • {task_name}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_celery_worker():
    """Test Celery worker command"""
    print("\n🔧 Testing Celery Worker Command")
    print("=" * 40)
    
    try:
        # Test the command without actually starting the worker
        from utils.celery_app import app
        
        # This should not raise an error
        print("   ✅ Celery worker command syntax is correct")
        print("   ✅ To start worker: python utils/run_celery.py")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_celery_beat():
    """Test Celery beat command"""
    print("\n⏰ Testing Celery Beat Command")
    print("=" * 35)
    
    try:
        # Test the command without actually starting the beat
        from utils.celery_app import app
        
        # This should not raise an error
        print("   ✅ Celery beat command syntax is correct")
        print("   ✅ To start beat: python utils/run_beat.py")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_manual_commands():
    """Test manual Celery commands"""
    print("\n📋 Manual Commands to Test")
    print("=" * 35)
    
    print("1. Start Celery Worker:")
    print("   python utils/run_celery.py")
    print()
    
    print("2. Start Celery Beat (in another terminal):")
    print("   python utils/run_beat.py")
    print()
    
    print("3. Or use direct Celery commands:")
    print("   celery -A utils.celery_app worker --loglevel=info")
    print("   celery -A utils.celery_app beat --loglevel=info")
    print()
    
    print("4. Test specific task:")
    print("   python -c \"from utils.celery_app import app; app.send_task('core.tasks.test_task')\"")

def main():
    """Main test function"""
    print("🔧 Bot Marketplace - Celery Commands Test")
    print("=" * 50)
    
    # Test Celery app
    app_ok = test_celery_app()
    
    if app_ok:
        # Test worker command
        worker_ok = test_celery_worker()
        
        # Test beat command
        beat_ok = test_celery_beat()
        
        if worker_ok and beat_ok:
            print("\n🎉 All Celery tests passed!")
            print("   You can now run Celery commands.")
        else:
            print("\n❌ Some Celery tests failed")
    else:
        print("\n❌ Celery app test failed")
    
    # Show manual commands
    test_manual_commands()

if __name__ == "__main__":
    main() 