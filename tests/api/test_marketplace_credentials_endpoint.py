#!/usr/bin/env python3
"""
Test script for marketplace credentials endpoint
"""

import requests
import json
import time

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "marketplace_dev_api_key_12345"
TEST_PRINCIPAL_ID = "rdmx6-jaaaa-aaaah-qcaiq-cai"

def test_health():
    """Test if API server is running"""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"🏥 Health Check: {response.status_code}")
        if response.status_code == 200:
            print(f"   Response: {response.json()}")
            return True
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_store_credentials():
    """Test the new store-by-principal endpoint"""
    print(f"\n🔑 Testing Store Credentials by Principal ID...")
    
    # Test data
    test_data = {
        "principal_id": TEST_PRINCIPAL_ID,
        "exchange": "BINANCE",
        "api_key": "test_api_key_12345",
        "api_secret": "test_secret_key_67890",
        "api_passphrase": None,
        "is_testnet": True
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.post(
            f"{API_URL}/exchange-credentials/marketplace/store-by-principal",
            headers=headers,
            json=test_data,
            timeout=10
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📋 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Store credentials: SUCCESS!")
            return True
        else:
            print("❌ Store credentials: FAILED!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode failed: {e}")
        print(f"   Raw response: {response.text}")
        return False

def test_get_credentials():
    """Test getting credentials back"""
    print(f"\n🔍 Testing Get Credentials by Principal ID...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        response = requests.get(
            f"{API_URL}/exchange-credentials/marketplace/credentials/{TEST_PRINCIPAL_ID}",
            headers=headers,
            params={"exchange": "BINANCE", "is_testnet": True},
            timeout=10
        )
        
        print(f"📡 Status Code: {response.status_code}")
        print(f"📋 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Get credentials: SUCCESS!")
            return True
        else:
            print("❌ Get credentials: FAILED!")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode failed: {e}")
        print(f"   Raw response: {response.text}")
        return False

def main():
    print("🚀 TESTING MARKETPLACE CREDENTIALS ENDPOINT")
    print("=" * 50)
    
    # Step 1: Health check
    if not test_health():
        print("❌ API server not running. Please start it first:")
        print("   docker-compose up -d")
        print("   OR")
        print("   python core/main.py")
        return
    
    # Wait a bit for server to be fully ready
    print("\n⏳ Waiting 5 seconds for server to be ready...")
    time.sleep(5)
    
    # Step 2: Test store credentials
    store_success = test_store_credentials()
    
    # Step 3: Test get credentials (only if store was successful)
    if store_success:
        time.sleep(2)  # Brief delay
        get_success = test_get_credentials()
    else:
        get_success = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY:")
    print(f"   Health Check: {'✅ PASS' if test_health() else '❌ FAIL'}")
    print(f"   Store Credentials: {'✅ PASS' if store_success else '❌ FAIL'}")
    print(f"   Get Credentials: {'✅ PASS' if get_success else '❌ FAIL'}")
    
    if store_success and get_success:
        print("\n🎉 ALL TESTS PASSED! Endpoint is working correctly!")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()