#!/usr/bin/env python3
"""
Simple test for the 3 marketplace bot registration APIs without database
"""

import sys
import os
from datetime import datetime, timedelta
import json

# Add project root to path
sys.path.append('.')

def test_api_schemas():
    """Test if the schemas are properly defined"""
    print("🧪 Testing API Schemas...")
    
    try:
        from core import schemas
        
        # Test BotRegistrationRequest schema
        registration_data = {
            "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
            "bot_id": 1,
            "symbol": "BTC/USDT",
            "timeframes": ["1h", "4h", "1d"],
            "trade_evaluation_period": 60,
            "starttime": datetime.now(),
            "endtime": datetime.now() + timedelta(days=30),
            "exchange_name": schemas.ExchangeType.BINANCE,
            "network_type": schemas.NetworkType.TESTNET,
            "trade_mode": schemas.TradeMode.SPOT
        }
        
        # Create schema instance
        request_schema = schemas.BotRegistrationRequest(**registration_data)
        print(f"   ✅ BotRegistrationRequest schema: OK")
        print(f"      - User Principal ID: {request_schema.user_principal_id}")
        print(f"      - Symbol: {request_schema.symbol}")
        print(f"      - Timeframes: {request_schema.timeframes}")
        print(f"      - Exchange: {request_schema.exchange_name}")
        print(f"      - Network: {request_schema.network_type}")
        print(f"      - Trade Mode: {request_schema.trade_mode}")
        
        # Test BotRegistrationUpdate schema
        update_data = {
            "timeframes": ["2h", "6h"],
            "trade_evaluation_period": 120,
            "network_type": schemas.NetworkType.MAINNET,
            "trade_mode": schemas.TradeMode.FUTURES
        }
        
        update_schema = schemas.BotRegistrationUpdate(**update_data)
        print(f"   ✅ BotRegistrationUpdate schema: OK")
        print(f"      - New Timeframes: {update_schema.timeframes}")
        print(f"      - New Evaluation Period: {update_schema.trade_evaluation_period}")
        print(f"      - New Network: {update_schema.network_type}")
        print(f"      - New Trade Mode: {update_schema.trade_mode}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_enums():
    """Test if the new enums are properly defined"""
    print("\n🧪 Testing New Enums...")
    
    try:
        from core import schemas
        
        # Test NetworkType enum
        print(f"   NetworkType enum:")
        print(f"      - TESTNET: {schemas.NetworkType.TESTNET}")
        print(f"      - MAINNET: {schemas.NetworkType.MAINNET}")
        
        # Test TradeMode enum
        print(f"   TradeMode enum:")
        print(f"      - SPOT: {schemas.TradeMode.SPOT}")
        print(f"      - MARGIN: {schemas.TradeMode.MARGIN}")
        print(f"      - FUTURES: {schemas.TradeMode.FUTURES}")
        
        # Test ExchangeType enum
        print(f"   ExchangeType enum:")
        print(f"      - BINANCE: {schemas.ExchangeType.BINANCE}")
        print(f"      - COINBASE: {schemas.ExchangeType.COINBASE}")
        print(f"      - KRAKEN: {schemas.ExchangeType.KRAKEN}")
        
        print(f"   ✅ All enums: OK")
        return True
        
    except Exception as e:
        print(f"   ❌ Enum test failed: {e}")
        return False

def test_validation():
    """Test schema validation"""
    print("\n🧪 Testing Schema Validation...")
    
    try:
        from core import schemas
        
        # Test invalid timeframe
        try:
            invalid_data = {
                "user_principal_id": "test-principal",
                "bot_id": 1,
                "symbol": "BTC/USDT",
                "timeframes": ["1h", "invalid_timeframe"],  # Invalid timeframe
                "trade_evaluation_period": 60,
                "starttime": datetime.now(),
                "endtime": datetime.now() + timedelta(days=30),
                "exchange_name": schemas.ExchangeType.BINANCE,
                "network_type": schemas.NetworkType.TESTNET,
                "trade_mode": schemas.TradeMode.SPOT
            }
            
            schemas.BotRegistrationRequest(**invalid_data)
            print(f"   ❌ Validation should have failed for invalid timeframe")
            return False
            
        except Exception as e:
            print(f"   ✅ Timeframe validation: OK (correctly rejected invalid timeframe)")
        
        # Test invalid symbol format
        try:
            invalid_symbol_data = {
                "user_principal_id": "test-principal",
                "bot_id": 1,
                "symbol": "INVALID_SYMBOL",  # Invalid format
                "timeframes": ["1h", "4h"],
                "trade_evaluation_period": 60,
                "starttime": datetime.now(),
                "endtime": datetime.now() + timedelta(days=30),
                "exchange_name": schemas.ExchangeType.BINANCE,
                "network_type": schemas.NetworkType.TESTNET,
                "trade_mode": schemas.TradeMode.SPOT
            }
            
            schemas.BotRegistrationRequest(**invalid_symbol_data)
            print(f"   ❌ Validation should have failed for invalid symbol")
            return False
            
        except Exception as e:
            print(f"   ✅ Symbol validation: OK (correctly rejected invalid symbol format)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Validation test failed: {e}")
        return False

def test_crud_functions():
    """Test if CRUD functions are properly defined"""
    print("\n🧪 Testing CRUD Functions...")
    
    try:
        from core import crud
        
        # Check if functions exist
        functions_to_check = [
            'create_bot_registration',
            'update_bot_registration', 
            'get_bot_registration_by_principal_id',
            'get_user_by_api_key'
        ]
        
        for func_name in functions_to_check:
            if hasattr(crud, func_name):
                print(f"   ✅ {func_name}: Function exists")
            else:
                print(f"   ❌ {func_name}: Function missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ CRUD test failed: {e}")
        return False

def test_security_functions():
    """Test if security functions are properly defined"""
    print("\n🧪 Testing Security Functions...")
    
    try:
        from core import security
        
        # Check if functions exist
        functions_to_check = [
            'get_user_by_api_key',
            'get_marketplace_user'
        ]
        
        for func_name in functions_to_check:
            if hasattr(security, func_name):
                print(f"   ✅ {func_name}: Function exists")
            else:
                print(f"   ❌ {func_name}: Function missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Security test failed: {e}")
        return False

def test_api_endpoints():
    """Test if API endpoints are properly defined"""
    print("\n🧪 Testing API Endpoints...")
    
    try:
        from api.endpoints import bots
        from fastapi import FastAPI
        
        # Create test app
        app = FastAPI()
        app.include_router(bots.router, prefix="/api/bots", tags=["bots"])
        
        # Check routes
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            "/api/bots/register",
            "/api/bots/update-registration/{subscription_id}",
            "/api/bots/registrations/{user_principal_id}"
        ]
        
        for expected_route in expected_routes:
            # Check if any route matches the pattern
            found = any(expected_route.replace("{subscription_id}", "{path}").replace("{user_principal_id}", "{path}") in route 
                       or expected_route in route for route in routes)
            
            if found:
                print(f"   ✅ {expected_route}: Route exists")
            else:
                print(f"   ❌ {expected_route}: Route missing")
                print(f"      Available routes: {routes}")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ API endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Marketplace Bot Registration Implementation")
    print("=" * 60)
    
    tests = [
        ("Enums", test_enums),
        ("Schemas", test_api_schemas),
        ("Validation", test_validation),
        ("CRUD Functions", test_crud_functions),
        ("Security Functions", test_security_functions),
        ("API Endpoints", test_api_endpoints)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test: PASSED")
        else:
            print(f"❌ {test_name} test: FAILED")
    
    print("\n" + "=" * 60)
    print(f"🏁 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The implementation is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
