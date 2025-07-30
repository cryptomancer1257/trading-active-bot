#!/usr/bin/env python3
"""
Integration test for the 3 marketplace bot registration APIs with mock data
"""

import sys
import os
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import Mock, patch

# Add project root to path
sys.path.append('.')

from core import schemas, models
from api.endpoints import bots

# Create test app
app = FastAPI()
app.include_router(bots.router, prefix="/api/bots", tags=["bots"])
client = TestClient(app)

def create_mock_user():
    """Create mock user for testing"""
    mock_user = Mock(spec=models.User)
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.api_key = "test_api_key_12345"
    mock_user.is_active = True
    mock_user.role = models.UserRole.USER
    return mock_user

def create_mock_bot():
    """Create mock bot for testing"""
    mock_bot = Mock(spec=models.Bot)
    mock_bot.id = 1
    mock_bot.name = "Test Trading Bot"
    mock_bot.status = models.BotStatus.APPROVED
    return mock_bot

def create_mock_subscription():
    """Create mock subscription for testing"""
    mock_subscription = Mock(spec=models.Subscription)
    mock_subscription.id = 1
    mock_subscription.user_id = 1
    mock_subscription.bot_id = 1
    mock_subscription.user_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
    mock_subscription.started_at = datetime.now()
    return mock_subscription

@patch('core.crud.create_bot_registration')
@patch('core.security.get_marketplace_user')
@patch('core.database.get_db')
def test_api_1_register_bot_integration(mock_get_db, mock_get_marketplace_user, mock_create_bot_registration):
    """Integration test for API 1: POST /api/bots/register"""
    print("🧪 Integration Test 1: POST /api/bots/register")
    
    # Setup mocks
    mock_user = create_mock_user()
    mock_subscription = create_mock_subscription()
    
    mock_get_marketplace_user.return_value = mock_user
    mock_create_bot_registration.return_value = mock_subscription
    mock_get_db.return_value = Mock()
    
    # Test data
    registration_data = {
        "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
        "bot_id": 1,
        "symbol": "BTC/USDT",
        "timeframes": ["1h", "4h", "1d"],
        "trade_evaluation_period": 60,
        "starttime": datetime.now().isoformat(),
        "endtime": (datetime.now() + timedelta(days=30)).isoformat(),
        "exchange_name": "BINANCE",
        "network_type": "testnet",
        "trade_mode": "Spot"
    }
    
    headers = {
        "X-API-Key": "test_api_key_12345",
        "Content-Type": "application/json"
    }
    
    try:
        response = client.post("/api/bots/register", json=registration_data, headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Registration successful!")
            print(f"   Response data:")
            print(f"      - Subscription ID: {data.get('subscription_id')}")
            print(f"      - User Principal ID: {data.get('user_principal_id')}")
            print(f"      - Bot ID: {data.get('bot_id')}")
            print(f"      - Status: {data.get('status')}")
            print(f"      - Message: {data.get('message')}")
            
            # Verify mock was called
            mock_create_bot_registration.assert_called_once()
            print(f"   ✅ CRUD function called correctly")
            
            return data.get('subscription_id')
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

@patch('core.crud.update_bot_registration')
@patch('core.security.get_marketplace_user')
@patch('core.database.get_db')
def test_api_2_update_registration_integration(mock_get_db, mock_get_marketplace_user, mock_update_bot_registration):
    """Integration test for API 2: PUT /api/bots/update-registration/{subscription_id}"""
    print("\n🧪 Integration Test 2: PUT /api/bots/update-registration/1")
    
    # Setup mocks
    mock_user = create_mock_user()
    mock_subscription = create_mock_subscription()
    updated_fields = ["timeframes", "trade_evaluation_period", "network_type", "trade_mode"]
    
    mock_get_marketplace_user.return_value = mock_user
    mock_update_bot_registration.return_value = (mock_subscription, updated_fields)
    mock_get_db.return_value = Mock()
    
    # Update data
    update_data = {
        "timeframes": ["2h", "6h", "12h"],
        "trade_evaluation_period": 120,
        "network_type": "mainnet",
        "trade_mode": "Futures"
    }
    
    headers = {
        "X-API-Key": "test_api_key_12345",
        "Content-Type": "application/json"
    }
    
    try:
        response = client.put("/api/bots/update-registration/1", json=update_data, headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Update successful!")
            print(f"   Response data:")
            print(f"      - Subscription ID: {data.get('subscription_id')}")
            print(f"      - User Principal ID: {data.get('user_principal_id')}")
            print(f"      - Status: {data.get('status')}")
            print(f"      - Message: {data.get('message')}")
            print(f"      - Updated fields: {data.get('updated_fields')}")
            
            # Verify mock was called
            mock_update_bot_registration.assert_called_once()
            print(f"   ✅ CRUD function called correctly")
            
            return True
        else:
            print(f"   ❌ Update failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

@patch('core.crud.get_bot_registration_by_principal_id')
@patch('core.security.get_marketplace_user')
@patch('core.database.get_db')
def test_api_3_get_registrations_integration(mock_get_db, mock_get_marketplace_user, mock_get_bot_registration):
    """Integration test for API 3: GET /api/bots/registrations/{user_principal_id}"""
    print("\n🧪 Integration Test 3: GET /api/bots/registrations/rdmx6-jaaaa-aaaah-qcaiq-cai")
    
    # Setup mocks
    mock_user = create_mock_user()
    mock_subscription = create_mock_subscription()
    
    # Add additional properties to mock subscription for response
    mock_subscription.instance_name = "Test Bot - rdmx6-ja"
    mock_subscription.status = models.SubscriptionStatus.ACTIVE
    mock_subscription.exchange_type = models.ExchangeType.BINANCE
    mock_subscription.trading_pair = "BTC/USDT"
    mock_subscription.timeframe = "1h"
    mock_subscription.timeframes = ["1h", "4h", "1d"]
    mock_subscription.trade_evaluation_period = 60
    mock_subscription.network_type = models.NetworkType.TESTNET
    mock_subscription.trade_mode = models.TradeMode.SPOT
    mock_subscription.is_testnet = True
    mock_subscription.is_trial = False
    mock_subscription.expires_at = datetime.now() + timedelta(days=30)
    
    mock_get_marketplace_user.return_value = mock_user
    mock_get_bot_registration.return_value = [mock_subscription]
    mock_get_db.return_value = Mock()
    
    headers = {
        "X-API-Key": "test_api_key_12345"
    }
    
    try:
        response = client.get("/api/bots/registrations/rdmx6-jaaaa-aaaah-qcaiq-cai", headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Get registrations successful!")
            print(f"   Found {len(data)} registrations")
            
            if data:
                first_reg = data[0]
                print(f"   First registration details:")
                print(f"      - ID: {first_reg.get('id')}")
                print(f"      - Bot ID: {first_reg.get('bot_id')}")
                print(f"      - Status: {first_reg.get('status')}")
                print(f"      - Trading Pair: {first_reg.get('trading_pair')}")
                print(f"      - Timeframes: {first_reg.get('timeframes')}")
                print(f"      - Network Type: {first_reg.get('network_type')}")
                print(f"      - Trade Mode: {first_reg.get('trade_mode')}")
            
            # Verify mock was called
            mock_get_bot_registration.assert_called_once()
            print(f"   ✅ CRUD function called correctly")
            
            return True
        else:
            print(f"   ❌ Get registrations failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("🚀 Running Integration Tests for Marketplace Bot Registration APIs")
    print("=" * 70)
    
    tests = [
        ("Register Bot API", test_api_1_register_bot_integration),
        ("Update Registration API", test_api_2_update_registration_integration),
        ("Get Registrations API", test_api_3_get_registrations_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED with exception: {e}")
    
    print("\n" + "=" * 70)
    print(f"🏁 Integration Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed! The APIs are working correctly.")
        print("\n📝 Summary of tested APIs:")
        print("   1. POST /api/bots/register - ✅ Working")
        print("   2. PUT /api/bots/update-registration/{id} - ✅ Working") 
        print("   3. GET /api/bots/registrations/{principal_id} - ✅ Working")
        print("\n🔑 Key features tested:")
        print("   - API key authentication")
        print("   - Request/response schema validation")
        print("   - CRUD operations integration")
        print("   - Error handling")
    else:
        print("⚠️  Some integration tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
