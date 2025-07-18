#!/usr/bin/env python3
"""
Quick test for Binance API signature
"""
import requests
import hmac
import hashlib
import time

def test_binance_credentials(api_key, api_secret, testnet=True):
    """Test Binance credentials with proper signature"""
    
    base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
    
    try:
        # Step 1: Get server time
        print("1. Getting server time...")
        time_response = requests.get(f"{base_url}/api/v3/time", timeout=10)
        server_time = time_response.json()['serverTime']
        print(f"   Server time: {server_time}")
        
        # Step 2: Create signature
        print("2. Creating signature...")
        params = {'timestamp': server_time}
        query_string = '&'.join([f"{key}={value}" for key, value in sorted(params.items())])
        
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        print(f"   Query: {query_string}")
        print(f"   Signature: {signature[:16]}...")
        
        # Step 3: Test account info
        print("3. Testing account info...")
        headers = {'X-MBX-APIKEY': api_key}
        response = requests.get(
            f"{base_url}/api/v3/account",
            params=params,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            account_data = response.json()
            print(f"✅ SUCCESS!")
            print(f"   Account Type: {account_data.get('accountType', 'Unknown')}")
            print(f"   Can Trade: {account_data.get('canTrade', False)}")
            print(f"   Permissions: {account_data.get('permissions', [])}")
            return True
        else:
            error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
            print(f"❌ ERROR: {response.status_code}")
            print(f"   Message: {error_data.get('msg', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Binance API Credential Tester")
    print("=" * 40)
    
    # Test với credentials mẫu (thay bằng credentials thật)
    API_KEY = "your_testnet_api_key_here"
    API_SECRET = "your_testnet_secret_here"
    
    if API_KEY == "your_testnet_api_key_here":
        print("⚠️  Please update API_KEY and API_SECRET in script")
        print("   Then run: python quick_fix_signature.py")
    else:
        success = test_binance_credentials(API_KEY, API_SECRET, testnet=True)
        if success:
            print("\n🎉 Credentials are working!")
        else:
            print("\n🔧 Next steps to fix:")
            print("1. Recreate API keys in Binance")
            print("2. Enable trading permissions")  
            print("3. Disable IP restrictions")
            print("4. Make sure using testnet keys for testnet") 