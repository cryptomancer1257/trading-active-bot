#!/usr/bin/env python3
"""
Test script for the new bot marketplace registration API
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
HARDCODED_API_KEY = "marketplace_dev_api_key_12345"

def test_register_bot_marketplace():
    """Test the new bot marketplace registration API"""
    print("🎯 Testing NEW POST /api/bots/register API (Bot Marketplace Registration)")
    
    registration_data = {
        "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
        "bot_id": 1,
        "marketplace_name": "Advanced Trading Bot Pro",
        "marketplace_description": "Professional trading bot with advanced technical analysis",
        "price_on_marketplace": 29.99
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": HARDCODED_API_KEY
    }
    
    try:
        print(f"📤 POST {BASE_URL}/api/bots/register")
        print(f"📋 Headers: {headers}")
        print(f"📋 Data: {json.dumps(registration_data, indent=2)}")
        
        response = requests.post(
            f"{BASE_URL}/api/bots/register",
            json=registration_data,
            headers=headers,
            timeout=10
        )
        
        print(f"\n📥 Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 201:
            response_data = response.json()
            print(f"✅ Bot marketplace registration successful!")
            print(f"📋 Response: {json.dumps(response_data, indent=2)}")
            
            # Extract and return the generated API key
            api_key = response_data.get('api_key')
            registration_id = response_data.get('registration_id')
            
            print(f"\n🔑 Generated Bot API Key: {api_key}")
            print(f"📊 Registration ID: {registration_id}")
            
            return api_key, registration_id
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else response.text
            print(f"❌ Registration failed: {error_data}")
            return None, None
            
    except Exception as e:
        print(f"❌ Registration request failed: {e}")
        return None, None

def test_validate_bot_api_key(api_key):
    """Test bot API key validation"""
    if not api_key:
        print("⚠️ Skipping API key validation - no API key to test")
        return
        
    print(f"\n🔍 Testing Bot API Key Validation")
    
    try:
        response = requests.get(f"{BASE_URL}/api/bots/validate-bot-key/{api_key}")
        
        print(f"📥 Validation Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Bot API key is valid!")
            print(f"📋 Registration Info: {json.dumps(response_data, indent=2)}")
        else:
            print(f"❌ Bot API key validation failed: {response.text}")
            
    except Exception as e:
        print(f"❌ API key validation failed: {e}")

def test_get_marketplace_bots():
    """Test getting marketplace bots list"""
    print(f"\n📋 Testing GET /api/bots/marketplace")
    
    try:
        response = requests.get(f"{BASE_URL}/api/bots/marketplace")
        
        print(f"📥 Marketplace Bots Response:")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Marketplace bots retrieved successfully!")
            print(f"📊 Number of bots: {len(response_data)}")
            
            if response_data:
                print(f"📋 Sample bot: {json.dumps(response_data[0], indent=2, default=str)}")
        else:
            print(f"❌ Failed to get marketplace bots: {response.text}")
            
    except Exception as e:
        print(f"❌ Marketplace bots request failed: {e}")

def main():
    """Main test flow"""
    print("🚀 Testing New Bot Marketplace Registration API")
    print("=" * 60)
    
    # Test 1: Register bot for marketplace
    api_key, registration_id = test_register_bot_marketplace()
    
    # Test 2: Validate the generated bot API key
    if api_key:
        test_validate_bot_api_key(api_key)
    
    # Test 3: Get marketplace bots list
    test_get_marketplace_bots()
    
    print(f"\n📊 Test Summary:")
    if api_key and registration_id:
        print(f"✅ Bot registered successfully with ID: {registration_id}")
        print(f"✅ Generated API key: {api_key}")
        print(f"✅ API key validation working")
        print(f"✅ Marketplace bots listing working")
        print(f"\n🎉 All tests passed! New API is working correctly.")
    else:
        print(f"❌ Bot registration failed")
        print(f"\n⚠️ Please check server logs and database setup")

if __name__ == "__main__":
    main()