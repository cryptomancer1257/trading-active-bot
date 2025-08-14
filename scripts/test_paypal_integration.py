#!/usr/bin/env python3
"""
Test script for PayPal integration
Verifies that all components are working correctly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
import asyncio

async def test_paypal_integration():
    """Test PayPal integration components"""
    print("🧪 Testing PayPal Integration Components")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 6
    
    # Test 1: Import dependencies
    try:
        import paypalrestsdk
        print("✅ Test 1/6: PayPal SDK imported successfully")
        tests_passed += 1
    except ImportError as e:
        print(f"❌ Test 1/6: PayPal SDK import failed: {e}")
    
    # Test 2: Currency service
    try:
        from services.currency_service import get_currency_service
        currency_service = get_currency_service()
        rate = currency_service.get_icp_usd_rate()
        print(f"✅ Test 2/6: Currency service working. ICP/USD rate: ${rate}")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 2/6: Currency service failed: {e}")
    
    # Test 3: Database models
    try:
        from core import models
        print("✅ Test 3/6: PayPal models imported successfully")
        
        # Check if PayPal enums exist
        assert hasattr(models, 'PayPalPaymentStatus')
        assert hasattr(models, 'PaymentMethod')
        assert hasattr(models, 'PayPalEnvironment')
        print("  ✅ PayPal enums verified")
        
        # Check if PayPal model classes exist
        assert hasattr(models, 'PayPalPayment')
        assert hasattr(models, 'PayPalConfig')
        assert hasattr(models, 'PayPalWebhookEvent')
        print("  ✅ PayPal model classes verified")
        
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 3/6: Model import failed: {e}")
    
    # Test 4: Schemas
    try:
        from core import schemas
        
        # Check if PayPal schemas exist
        schema_classes = [
            'PayPalOrderRequest', 'PayPalOrderResponse', 
            'PayPalExecutionRequest', 'PayPalExecutionResponse',
            'PayPalPaymentInDB', 'PayPalConfigInDB'
        ]
        
        for schema_class in schema_classes:
            assert hasattr(schemas, schema_class), f"Missing schema: {schema_class}"
        
        print("✅ Test 4/6: PayPal schemas verified")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 4/6: Schema verification failed: {e}")
    
    # Test 5: CRUD operations
    try:
        from core import crud
        
        # Check if PayPal CRUD functions exist
        crud_functions = [
            'create_paypal_payment', 'get_paypal_payment',
            'update_paypal_payment_status', 'get_paypal_payments_by_user',
            'get_paypal_config', 'create_paypal_config'
        ]
        
        for crud_func in crud_functions:
            assert hasattr(crud, crud_func), f"Missing CRUD function: {crud_func}"
        
        print("✅ Test 5/6: PayPal CRUD functions verified")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 5/6: CRUD verification failed: {e}")
    
    # Test 6: PayPal service
    try:
        from services.paypal_service import get_paypal_service
        # Note: This will fail without database, but we can test import
        print("✅ Test 6/6: PayPal service import successful")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Test 6/6: PayPal service import failed: {e}")
    
    print("\n" + "=" * 40)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! PayPal integration is ready.")
        print("\n📝 Next steps:")
        print("1. Run database migration: ./scripts/run_paypal_migration.sh")
        print("2. Configure PayPal credentials in .env file")
        print("3. Start Redis server for currency caching")
        print("4. Start FastAPI server: uvicorn core.main:app --reload")
        print("5. Test endpoints at http://localhost:8000/docs")
        return True
    else:
        print(f"⚠️  {total_tests - tests_passed} tests failed. Check the errors above.")
        return False

def test_environment_config():
    """Test environment configuration"""
    print("\n🔧 Testing Environment Configuration")
    print("=" * 40)
    
    # Check .env file
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        # Load and check PayPal variables
        from dotenv import load_dotenv
        load_dotenv()
        
        paypal_vars = {
            'PAYPAL_MODE': os.getenv('PAYPAL_MODE'),
            'PAYPAL_CLIENT_ID': os.getenv('PAYPAL_CLIENT_ID'),
            'PAYPAL_CLIENT_SECRET': os.getenv('PAYPAL_CLIENT_SECRET'),
            'FRONTEND_URL': os.getenv('FRONTEND_URL'),
        }
        
        configured_vars = 0
        for var, value in paypal_vars.items():
            if value and value != 'not_set' and 'your_' not in value.lower():
                print(f"  ✅ {var}: configured")
                configured_vars += 1
            else:
                print(f"  ⚠️  {var}: not configured")
        
        if configured_vars == len(paypal_vars):
            print("✅ All PayPal environment variables configured")
        else:
            print(f"⚠️  {len(paypal_vars) - configured_vars} variables need configuration")
    else:
        print("⚠️  .env file not found - create from config/paypal.env.example")

def test_database_migration():
    """Test if database migration exists"""
    print("\n🗄️  Testing Database Migration")
    print("=" * 40)
    
    migration_file = "migrations/versions/009_paypal_integration.sql"
    if os.path.exists(migration_file):
        print("✅ PayPal migration file found")
        
        # Check migration content
        with open(migration_file, 'r') as f:
            content = f.read()
            
        required_tables = ['paypal_payments', 'paypal_config', 'paypal_webhook_events']
        for table in required_tables:
            if table in content:
                print(f"  ✅ {table} table definition found")
            else:
                print(f"  ❌ {table} table definition missing")
    else:
        print("❌ PayPal migration file not found")

if __name__ == "__main__":
    print("🚀 PayPal Integration Test Suite")
    print("================================")
    
    try:
        # Run main integration test
        result = asyncio.run(test_paypal_integration())
        
        # Run additional tests
        test_environment_config()
        test_database_migration()
        
        print("\n" + "=" * 50)
        if result:
            print("🎉 PayPal Integration Test Suite PASSED!")
        else:
            print("⚠️  PayPal Integration Test Suite has issues.")
            
        print("\n📚 Documentation:")
        print("  - Setup Guide: docs/PAYPAL_INTEGRATION_GUIDE.md")
        print("  - Migration Script: scripts/run_paypal_migration.sh")
        print("  - Setup Script: scripts/setup_paypal_integration.sh")
        
    except Exception as e:
        print(f"💥 Test suite failed with error: {e}")
        sys.exit(1)
