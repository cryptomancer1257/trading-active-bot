#!/usr/bin/env python3
"""
Test frontend API call simulation
"""

import requests
import json

def test_frontend_api_call():
    """Test what frontend would receive"""
    
    print("🧪 Testing Frontend API Call")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Without authentication (what frontend gets if no token)
    print("\n1. Testing /quota-topups/usage without auth:")
    try:
        response = requests.get(f"{base_url}/quota-topups/usage")
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Requires authentication")
            print("   📝 Frontend would get 401 error")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: With fake token (what frontend gets with invalid token)
    print("\n2. Testing /quota-topups/usage with fake token:")
    try:
        response = requests.get(
            f"{base_url}/quota-topups/usage",
            headers={"Authorization": "Bearer fake-token"}
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Expected: Invalid token")
            print("   📝 Frontend would get 401 error")
        else:
            print(f"   Response: {response.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Check if there's a demo endpoint
    print("\n3. Testing if there's a demo usage endpoint:")
    try:
        response = requests.get(f"{base_url}/quota-topups/usage-demo")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Demo endpoint exists")
            print(f"   Response: {response.text[:200]}...")
        else:
            print("   ❌ No demo endpoint")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Check packages endpoint (should work without auth)
    print("\n4. Testing /quota-topups/packages (should work):")
    try:
        response = requests.get(f"{base_url}/quota-topups/packages")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {len(data.get('packages', {}))} packages")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print(f"\n💡 Conclusion:")
    print(f"   - Frontend needs authentication to get quota usage")
    print(f"   - If no auth token, frontend gets 401 error")
    print(f"   - Frontend might be showing cached/fallback data")
    print(f"   - Need to check if user is logged in")

if __name__ == "__main__":
    test_frontend_api_call()
