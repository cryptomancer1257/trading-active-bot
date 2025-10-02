#!/usr/bin/env python3
"""
Script to debug production decryption issues
Run this in production environment to test decryption
"""

import sys
import os
sys.path.append('.')

from core.database import get_db
from core import models
from core.api_key_manager import get_bot_api_keys, APIKeyManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== PRODUCTION DECRYPTION DEBUG ===")
    
    # Check environment variables
    print("\n1. Environment Variables:")
    print(f"   API_KEY_ENCRYPTION_KEY: {os.getenv('API_KEY_ENCRYPTION_KEY', 'NOT_SET')}")
    print(f"   API_KEY_MASTER_PASSWORD: {os.getenv('API_KEY_MASTER_PASSWORD', 'NOT_SET')}")
    print(f"   API_KEY_SALT: {os.getenv('API_KEY_SALT', 'NOT_SET')}")
    
    # Get database session
    db = next(get_db())
    
    # Check subscription 491
    print("\n2. Checking Subscription 491:")
    subscription = db.query(models.Subscription).filter(models.Subscription.id == 491).first()
    if subscription:
        print(f"   ✅ Found subscription 491:")
        print(f"   - Principal ID: {subscription.user_principal_id}")
        print(f"   - Payment Method: {subscription.payment_method}")
        print(f"   - Bot ID: {subscription.bot_id}")
        
        if subscription.bot:
            print(f"   - Bot: {subscription.bot.name}")
            print(f"   - Developer ID: {subscription.bot.developer_id}")
    else:
        print("   ❌ Subscription 491 not found")
        return
    
    # Check developer 7 credentials
    print("\n3. Checking Developer 7 Credentials:")
    dev_creds = db.query(models.DeveloperExchangeCredentials).filter(
        models.DeveloperExchangeCredentials.user_id == 7,
        models.DeveloperExchangeCredentials.exchange_type == models.ExchangeType.BINANCE,
        models.DeveloperExchangeCredentials.network_type == models.NetworkType.TESTNET,
        models.DeveloperExchangeCredentials.is_active == True
    ).all()
    
    print(f"   Found {len(dev_creds)} credentials:")
    for cred in dev_creds:
        print(f"   - ID: {cred.id}, Name: {cred.name}")
        print(f"     API Key: {cred.api_key[:50]}...")
        print(f"     API Secret: {cred.api_secret[:50]}...")
    
    # Test decryption
    print("\n4. Testing Decryption:")
    api_manager = APIKeyManager()
    print(f"   Encryption key: {api_manager._encryption_key}")
    
    for cred in dev_creds:
        print(f"\n   Testing credential ID {cred.id}:")
        try:
            decrypted_key = api_manager.decrypt_api_key(cred.api_key)
            decrypted_secret = api_manager.decrypt_api_key(cred.api_secret)
            print(f"   ✅ Decrypted API Key: {decrypted_key[:20]}...")
            print(f"   ✅ Decrypted API Secret: {decrypted_secret[:20]}...")
        except Exception as e:
            print(f"   ❌ Decryption FAILED: {e}")
            print(f"   This is the problem! Encryption key mismatch.")
    
    # Test get_bot_api_keys
    print("\n5. Testing get_bot_api_keys:")
    try:
        result = get_bot_api_keys(
            user_principal_id='trial_user_1759279793106',
            exchange='BINANCE',
            is_testnet=True,
            subscription_id=491
        )
        if result:
            print("   ✅ SUCCESS: Credentials found!")
            print(f"   API Key: {result['api_key']}")
            print(f"   API Secret: {result['api_secret']}")
        else:
            print("   ❌ FAILED: No credentials returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    main()
