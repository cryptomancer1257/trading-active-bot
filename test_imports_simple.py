#!/usr/bin/env python3
"""
Simple import test
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if imports work correctly"""
    print("🧪 Testing Imports")
    print("=" * 30)
    
    try:
        # Test core imports
        print("1. Testing core imports...")
        from core import models, schemas, crud, database, security
        print("   ✅ Core imports successful")
        
        # Test services imports
        print("2. Testing services imports...")
        from services import binance_integration, exchange_factory, s3_manager
        print("   ✅ Services imports successful")
        
        # Test email services
        print("3. Testing email services...")
        from services import sendgrid_email_service, gmail_smtp_service, email_templates
        print("   ✅ Email services imports successful")
        
        # Test utils imports
        print("4. Testing utils imports...")
        from utils import celery_app, run_celery, run_beat
        print("   ✅ Utils imports successful")
        
        # Test API imports
        print("5. Testing API imports...")
        from api.endpoints import auth, bots, subscriptions, admin
        print("   ✅ API imports successful")
        
        # Test Celery app
        print("6. Testing Celery app...")
        from utils.celery_app import app
        print(f"   ✅ Celery app: {app}")
        
        # Test tasks import
        print("7. Testing tasks import...")
        from core import tasks
        print("   ✅ Tasks import successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_imports() 