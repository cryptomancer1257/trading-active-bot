#!/usr/bin/env python3
"""
Test script for Marketplace Bot Registration API
Demonstrates how to use the new marketplace API endpoints
"""

import requests
import json
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8000/api/bots"
API_KEY = "your_api_key_here"  # Replace with actual API key

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def test_register_bot():
    """Test bot registration endpoint"""
    print("=== Testing Bot Registration ===")
    
    # Registration data
    registration_data = {
        "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
        "bot_id": 1,  # Assuming bot ID 1 exists and is approved
        "symbol": "BTC/USDT",
        "timeframes": ["1h", "4h", "1d"],
        "trade_evaluation_period": 60,
        "starttime": datetime.now().isoformat() + "Z",
        "endtime": (datetime.now() + timedelta(days=365)).isoformat() + "Z",
        "exchange_name": "BINANCE",
        "network_type": "testnet",
        "trade_mode": "Spot"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/register",
            headers=HEADERS,
            json=registration_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            return response.json()["subscription_id"]
        else:
            print(f"Registration failed: {response.json()}")
            return None
            
    except Exception as e:
        print(f"Error during registration: {e}")
        return None

def test_update_registration(subscription_id):
    """Test bot registration update endpoint"""
    print(f"\n=== Testing Bot Registration Update (ID: {subscription_id}) ===")
    
    # Update data
    update_data = {
        "timeframes": ["2h", "6h", "12h"],
        "trade_evaluation_period": 120,
        "network_type": "mainnet",
        "trade_mode": "Futures"
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/update-registration/{subscription_id}",
            headers=HEADERS,
            json=update_data
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error during update: {e}")

def test_get_registrations():
    """Test get registrations endpoint"""
    print("\n=== Testing Get Bot Registrations ===")
    
    user_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
    
    try:
        response = requests.get(
            f"{BASE_URL}/registrations/{user_principal_id}",
            headers=HEADERS
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error during get registrations: {e}")

def test_get_registrations_with_bot_filter():
    """Test get registrations with bot ID filter"""
    print("\n=== Testing Get Bot Registrations (with bot filter) ===")
    
    user_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
    bot_id = 1
    
    try:
        response = requests.get(
            f"{BASE_URL}/registrations/{user_principal_id}",
            headers=HEADERS,
            params={"bot_id": bot_id}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    except Exception as e:
        print(f"Error during get registrations with filter: {e}")

def main():
    """Run all tests"""
    print("Starting Marketplace Bot Registration API Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:8]}..." if API_KEY != "your_api_key_here" else "API Key: NOT SET")
    print("-" * 50)
    
    # Test registration
    subscription_id = test_register_bot()
    
    # Test update if registration was successful
    if subscription_id:
        test_update_registration(subscription_id)
    
    # Test get registrations
    test_get_registrations()
    
    # Test get registrations with filter
    test_get_registrations_with_bot_filter()
    
    print("\n" + "=" * 50)
    print("Tests completed!")

if __name__ == "__main__":
    main()