#!/usr/bin/env python3
"""
Test real API calls to the running FastAPI server
"""

import requests
import json
import time
from datetime import datetime, timedelta

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test_marketplace_api_key_12345"

def test_server_health():
    """Test if server is running"""
    print("🔍 Testing server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False

def test_register_bot_api():
    """Test the real bot registration API"""
    print("\n🎯 Testing POST /bots/register API")
    
    # Prepare test data
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
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        print(f"📤 Sending request to: {BASE_URL}/bots/register")
        print(f"📋 Headers: {headers}")
        print(f"📋 Data: {json.dumps(registration_data, indent=2, default=str)}")
        
        response = requests.post(
            f"{BASE_URL}/bots/register",
            json=registration_data,
            headers=headers,
            timeout=10
        )
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"   Body: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 201:
                print("✅ Bot registration successful!")
                return response_data.get('subscription_id')
            else:
                print(f"❌ Bot registration failed")
                return None
                
        except json.JSONDecodeError:
            print(f"   Body (raw): {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def test_update_registration_api(subscription_id):
    """Test the real update registration API"""
    if not subscription_id:
        print("\n⚠️ Skipping update test - no subscription ID")
        return False
        
    print(f"\n🎯 Testing PUT /bots/update-registration/{subscription_id} API")
    
    update_data = {
        "timeframes": ["2h", "6h", "12h"],
        "trade_evaluation_period": 120,
        "network_type": "mainnet",
        "trade_mode": "Futures"
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        print(f"📤 Sending request to: {BASE_URL}/bots/update-registration/{subscription_id}")
        print(f"📋 Data: {json.dumps(update_data, indent=2)}")
        
        response = requests.put(
            f"{BASE_URL}/bots/update-registration/{subscription_id}",
            json=update_data,
            headers=headers,
            timeout=10
        )
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"   Body: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200:
                print("✅ Registration update successful!")
                return True
            else:
                print(f"❌ Registration update failed")
                return False
                
        except json.JSONDecodeError:
            print(f"   Body (raw): {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_get_registrations_api():
    """Test the real get registrations API"""
    print(f"\n🎯 Testing GET /bots/registrations/rdmx6-jaaaa-aaaah-qcaiq-cai API")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        user_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        print(f"📤 Sending request to: {BASE_URL}/bots/registrations/{user_principal_id}")
        
        response = requests.get(
            f"{BASE_URL}/bots/registrations/{user_principal_id}",
            headers=headers,
            timeout=10
        )
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"   Body: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200:
                print(f"✅ Get registrations successful! Found {len(response_data)} registrations")
                return True
            else:
                print(f"❌ Get registrations failed")
                return False
                
        except json.JSONDecodeError:
            print(f"   Body (raw): {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_error_scenarios():
    """Test error scenarios"""
    print(f"\n⚠️ Testing Error Scenarios")
    
    # Test 1: Missing API Key
    print("\n🔍 Test: Missing API Key")
    try:
        response = requests.post(f"{BASE_URL}/bots/register", json={})
        print(f"   Status: {response.status_code} (Expected: 422)")
        if response.status_code == 422:
            print("   ✅ Correctly rejected missing API key")
        else:
            print("   ⚠️ Unexpected response")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Invalid API Key
    print("\n🔍 Test: Invalid API Key")
    try:
        headers = {"X-API-Key": "invalid_key", "Content-Type": "application/json"}
        response = requests.post(f"{BASE_URL}/bots/register", json={}, headers=headers)
        print(f"   Status: {response.status_code} (Expected: 401)")
        if response.status_code == 401:
            print("   ✅ Correctly rejected invalid API key")
        else:
            print("   ⚠️ Unexpected response")
    except Exception as e:
        print(f"   Error: {e}")

def main():
    """Run all real API tests"""
    print("🚀 REAL API TEST - Marketplace Bot Registration")
    print("=" * 60)
    
    # Check if server is running
    if not test_server_health():
        print("\n❌ Server is not running. Please start the server first:")
        print("   python main.py")
        return
    
    print("\n" + "=" * 60)
    print("🧪 TESTING REAL APIs")
    print("=" * 60)
    
    # Test API 1: Register bot
    subscription_id = test_register_bot_api()
    
    # Test API 2: Update registration
    test_update_registration_api(subscription_id)
    
    # Test API 3: Get registrations
    test_get_registrations_api()
    
    # Test error scenarios
    test_error_scenarios()
    
    print("\n" + "=" * 60)
    print("🏁 REAL API TESTS COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    main()
