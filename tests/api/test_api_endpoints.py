#!/usr/bin/env python3
"""
Test script for the 3 marketplace bot registration APIs
"""

import sys
import os
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append('.')

from core.database import get_db
from core import models, schemas, crud, security
from api.endpoints import bots
from fastapi import FastAPI

# Create test app
app = FastAPI()
app.include_router(bots.router, prefix="/api/bots", tags=["bots"])

client = TestClient(app)

def setup_test_data():
    """Setup test data for API testing"""
    print("🔧 Setting up test data...")
    
    db = next(get_db())
    
    try:
        # Create test user with API key
        test_user = db.query(models.User).filter(
            models.User.email == "test_marketplace@example.com"
        ).first()
        
        if not test_user:
            test_user = models.User(
                email="test_marketplace@example.com",
                hashed_password=security.get_password_hash("testpassword"),
                role=models.UserRole.USER,
                api_key="test_api_key_12345",
                is_active=True,
                developer_name="Test Marketplace User"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Create test bot category
        test_category = db.query(models.BotCategory).filter(
            models.BotCategory.name == "Test Category"
        ).first()
        
        if not test_category:
            test_category = models.BotCategory(
                name="Test Category",
                description="Category for testing"
            )
            db.add(test_category)
            db.commit()
            db.refresh(test_category)
        
        # Create test bot
        test_bot = db.query(models.Bot).filter(
            models.Bot.name == "Test Trading Bot"
        ).first()
        
        if not test_bot:
            test_bot = models.Bot(
                name="Test Trading Bot",
                description="A test bot for API testing",
                developer_id=test_user.id,
                category_id=test_category.id,
                status=models.BotStatus.APPROVED,  # Must be approved for registration
                bot_type="TECHNICAL",
                price_per_month=10.0,
                is_free=False
            )
            db.add(test_bot)
            db.commit()
            db.refresh(test_bot)
        
        print(f"✅ Test data setup complete:")
        print(f"   User ID: {test_user.id}")
        print(f"   Bot ID: {test_bot.id}")
        print(f"   API Key: {test_user.api_key}")
        
        return test_user, test_bot
        
    except Exception as e:
        print(f"❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_api_1_register_bot():
    """Test API 1: POST /api/bots/register"""
    print("\n🧪 Testing API 1: POST /api/bots/register")
    
    test_user, test_bot = setup_test_data()
    if not test_user or not test_bot:
        print("❌ Failed to setup test data")
        return False
    
    # Test data
    registration_data = {
        "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
        "bot_id": test_bot.id,
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
        "X-API-Key": test_user.api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = client.post("/api/bots/register", json=registration_data, headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"   ✅ Registration successful!")
            print(f"   Subscription ID: {data.get('subscription_id')}")
            print(f"   User Principal ID: {data.get('user_principal_id')}")
            print(f"   Status: {data.get('status')}")
            return data.get('subscription_id')
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_api_2_update_registration(subscription_id):
    """Test API 2: PUT /api/bots/update-registration/{subscription_id}"""
    print(f"\n🧪 Testing API 2: PUT /api/bots/update-registration/{subscription_id}")
    
    if not subscription_id:
        print("   ❌ No subscription ID provided")
        return False
    
    test_user, _ = setup_test_data()
    if not test_user:
        print("   ❌ Failed to get test user")
        return False
    
    # Update data
    update_data = {
        "timeframes": ["2h", "6h", "12h"],
        "trade_evaluation_period": 120,
        "network_type": "mainnet",
        "trade_mode": "Futures"
    }
    
    headers = {
        "X-API-Key": test_user.api_key,
        "Content-Type": "application/json"
    }
    
    try:
        response = client.put(f"/api/bots/update-registration/{subscription_id}", 
                            json=update_data, headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Update successful!")
            print(f"   Updated fields: {data.get('updated_fields')}")
            print(f"   Status: {data.get('status')}")
            return True
        else:
            print(f"   ❌ Update failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_api_3_get_registrations():
    """Test API 3: GET /api/bots/registrations/{user_principal_id}"""
    print("\n🧪 Testing API 3: GET /api/bots/registrations/{user_principal_id}")
    
    test_user, _ = setup_test_data()
    if not test_user:
        print("   ❌ Failed to get test user")
        return False
    
    user_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
    
    headers = {
        "X-API-Key": test_user.api_key
    }
    
    try:
        response = client.get(f"/api/bots/registrations/{user_principal_id}", headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Get registrations successful!")
            print(f"   Found {len(data)} registrations")
            
            if data:
                first_reg = data[0]
                print(f"   First registration:")
                print(f"     - ID: {first_reg.get('id')}")
                print(f"     - Bot ID: {first_reg.get('bot_id')}")
                print(f"     - Status: {first_reg.get('status')}")
                print(f"     - Trading Pair: {first_reg.get('trading_pair')}")
                print(f"     - Timeframes: {first_reg.get('timeframes')}")
            
            return True
        else:
            print(f"   ❌ Get registrations failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Starting API Tests for Marketplace Bot Registration")
    print("=" * 60)
    
    # Test API 1: Register bot
    subscription_id = test_api_1_register_bot()
    
    # Test API 2: Update registration (if registration was successful)
    if subscription_id:
        test_api_2_update_registration(subscription_id)
    
    # Test API 3: Get registrations
    test_api_3_get_registrations()
    
    print("\n" + "=" * 60)
    print("🏁 API Tests completed!")

if __name__ == "__main__":
    main()
