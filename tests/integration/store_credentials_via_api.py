#!/usr/bin/env python3
"""
Store credentials via API endpoint with marketplace key
"""
import requests
import json

def store_via_api():
    """Store credentials via REST API"""
    
    url = "http://localhost:8000/api/exchange-credentials/store"
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'marketplace_dev_api_key_12345'
    }
    
    data = {
        "principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
        "exchange": "BINANCE",
        "api_key": "3a768bf1e6ac655e47395907c3c5c24fa2e9627128e8d9c5aabc9cbf29e8e49f",
        "api_secret": "a2da36f4c242e6a00d0940d9d101a75981f1c389aaae8017d0b394ede868d9aa",
        "is_testnet": True
    }
    
    print("🔐 Storing credentials via API...")
    print(f"📊 URL: {url}")
    print(f"🔑 API Key: marketplace_dev_api_key_12345")
    print(f"🆔 Principal ID: {data['principal_id']}")
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📈 Response Status: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Credentials stored via API!")
            return True
        else:
            print("❌ FAILED: API request failed")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_alternative_endpoints():
    """Test other possible endpoints"""
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/exchange-credentials/credentials",
        "/api/exchange-credentials/credentials", 
        "/auth/me/credentials",
        "/admin/exchange-credentials"
    ]
    
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': 'marketplace_dev_api_key_12345'
    }
    
    data = {
        "principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
        "exchange": "BINANCE",
        "api_key": "3a768bf1e6ac655e47395907c3c5c24fa2e9627128e8d9c5aabc9cbf29e8e49f",
        "api_secret": "a2da36f4c242e6a00d0940d9d101a75981f1c389aaae8017d0b394ede868d9aa",
        "is_testnet": True
    }
    
    print("\n🔍 Testing alternative endpoints...")
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"\n📊 Testing: {endpoint}")
        
        try:
            response = requests.post(url, headers=headers, json=data)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 404:
                print("   ❌ Not Found")
            elif response.status_code == 401:
                print("   🔒 Unauthorized")
            elif response.status_code == 422:
                print("   📝 Validation Error")
                print(f"   Details: {response.text[:200]}")
            elif response.status_code == 200:
                print("   ✅ SUCCESS!")
                print(f"   Response: {response.text}")
                return True
            else:
                print(f"   Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return False

if __name__ == "__main__":
    print("🔐 TESTING API CREDENTIAL STORAGE")
    print("="*50)
    
    # Test main endpoint
    success = store_via_api()
    
    if not success:
        print("\n🔄 Trying alternative endpoints...")
        success = test_alternative_endpoints()
    
    if success:
        print(f"\n🎊 SUCCESS: Credentials stored!")
        print(f"   ✅ Ready to test bot with database keys")
    else:
        print(f"\n❌ FAILED: Could not store credentials via API")
        print(f"   💡 May need to create custom endpoint or use direct database access")
    
    print("\n" + "="*50)