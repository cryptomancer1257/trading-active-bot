#!/usr/bin/env python3
"""Quick PayPal Backend Test"""

import requests
import json
import time
import subprocess
import signal
import os

def test_paypal_backend():
    BASE_URL = "http://localhost:8000"
    
    print("🧪 Quick PayPal Backend Test")
    print("="*30)
    
    # Test endpoints
    tests = [
        ("Health Check", "GET", "/health"),
        ("API Root", "GET", "/"),
        ("Currency Rate", "GET", "/payments/paypal/currency-rate"),
        ("PayPal Config", "GET", "/payments/paypal/config"),
        ("Payment Summary", "GET", "/payments/paypal/payments/summary"),
    ]
    
    results = []
    
    for name, method, endpoint in tests:
        try:
            url = BASE_URL + endpoint
            response = requests.get(url, timeout=5)
            status = "✅ PASS" if response.status_code == 200 else f"❌ FAIL ({response.status_code})"
            results.append((name, status, response.status_code))
            print(f"{status} {name} - {response.status_code}")
            
            # Show response preview for key endpoints
            if endpoint == "/payments/paypal/currency-rate" and response.status_code == 200:
                data = response.json()
                print(f"    💱 ICP/USD Rate: ${data.get('icp_usd_rate', 'N/A')}")
            elif endpoint == "/payments/paypal/config" and response.status_code == 200:
                data = response.json()
                print(f"    ⚙️  Environment: {data.get('environment', 'N/A')}")
                
        except requests.exceptions.ConnectionError:
            results.append((name, "❌ CONNECTION FAILED", 0))
            print(f"❌ CONNECTION FAILED {name} - Server not running?")
        except Exception as e:
            results.append((name, f"❌ ERROR: {str(e)}", 0))
            print(f"❌ ERROR {name} - {str(e)}")
    
    print("\n" + "="*30)
    print("📊 SUMMARY")
    print("="*30)
    
    passed = sum(1 for _, status, _ in results if "PASS" in status)
    total = len(results)
    
    for name, status, code in results:
        print(f"{status} {name}")
    
    print(f"\nResult: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is ready for marketplace integration!")
        return True
    else:
        print("⚠️  Some tests failed. Check server status and configuration.")
        return False

def test_paypal_order_creation():
    """Test creating a PayPal order"""
    BASE_URL = "http://localhost:8000"
    
    print("\n💳 Testing PayPal Order Creation")
    print("-" * 30)
    
    order_data = {
        "user_principal_id": "test-principal-12345",
        "bot_id": 1,
        "duration_days": 30,
        "pricing_tier": "monthly"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/payments/paypal/create-order",
            json=order_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PayPal order creation successful!")
            print(f"   Payment ID: {data.get('payment_id', 'N/A')}")
            print(f"   Amount USD: ${data.get('amount_usd', 'N/A')}")
            print(f"   ICP Equivalent: {data.get('amount_icp_equivalent', 'N/A')}")
            return True
        else:
            print(f"❌ PayPal order creation failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing PayPal order: {e}")
        return False

if __name__ == "__main__":
    # Check if server is running first
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        print("✅ Server is already running")
        server_running = True
    except:
        print("❌ Server not running. Please start server first:")
        print("   source .venv/bin/activate")
        print("   python main.py")
        server_running = False
    
    if server_running:
        # Run basic tests
        basic_passed = test_paypal_backend()
        
        if basic_passed:
            # Test order creation
            order_passed = test_paypal_order_creation()
            
            if order_passed:
                print("\n🚀 FINAL RESULT: Backend fully ready for integration!")
            else:
                print("\n⚠️  Backend partially ready - order creation needs attention")
        
        print("\n🔗 Useful URLs:")
        print("   📚 API Docs: http://localhost:8000/docs")
        print("   💱 Currency: http://localhost:8000/payments/paypal/currency-rate")
        print("   ⚙️  Config: http://localhost:8000/payments/paypal/config")
    else:
        print("\n💡 To start server:")
        print("   source .venv/bin/activate")
        print("   python main.py")
