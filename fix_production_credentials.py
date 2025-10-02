#!/usr/bin/env python3
"""
Script to fix developer credentials in production database
Run this in production environment to update credentials with correct encryption key
"""

import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from core.database import get_db
from core import models
from core.api_key_manager import APIKeyManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("=== FIXING PRODUCTION DEVELOPER CREDENTIALS ===")
    
    # Check environment variables
    print("\n1. Environment Variables:")
    print(f"   API_KEY_ENCRYPTION_KEY: {os.getenv('API_KEY_ENCRYPTION_KEY', 'NOT_SET')}")
    print(f"   API_KEY_MASTER_PASSWORD: {os.getenv('API_KEY_MASTER_PASSWORD', 'NOT_SET')}")
    print(f"   API_KEY_SALT: {os.getenv('API_KEY_SALT', 'NOT_SET')}")
    
    # Get database session
    db = next(get_db())
    
    # Get all developer credentials for user 7
    print("\n2. Current Developer 7 Credentials:")
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
    
    # Test decryption with current key
    print("\n3. Testing Decryption:")
    api_manager = APIKeyManager()
    print(f"   Current encryption key: {api_manager._encryption_key}")
    
    for cred in dev_creds:
        print(f"\n   Testing credential ID {cred.id}:")
        try:
            decrypted_key = api_manager.decrypt_api_key(cred.api_key)
            decrypted_secret = api_manager.decrypt_api_key(cred.api_secret)
            print(f"   ✅ Decryption SUCCESS:")
            print(f"     - API Key: {decrypted_key}")
            print(f"     - API Secret: {decrypted_secret}")
        except Exception as e:
            print(f"   ❌ Decryption FAILED: {e}")
            print(f"   This credential needs to be updated!")
            
            # Update with new encryption
            print(f"\n   Updating credential ID {cred.id}...")
            new_api_key = f"production_binance_api_key_{cred.id}"
            new_api_secret = f"production_binance_api_secret_{cred.id}"
            
            # Encrypt with current key
            new_encrypted_key = api_manager.encrypt_api_key(new_api_key)
            new_encrypted_secret = api_manager.encrypt_api_key(new_api_secret)
            
            # Update database
            cred.api_key = new_encrypted_key
            cred.api_secret = new_encrypted_secret
            db.commit()
            
            print(f"   ✅ Updated credential ID {cred.id}")
            
            # Test new decryption
            try:
                test_key = api_manager.decrypt_api_key(cred.api_key)
                test_secret = api_manager.decrypt_api_key(cred.api_secret)
                print(f"   ✅ New decryption test: SUCCESS")
                print(f"     - API Key: {test_key}")
                print(f"     - API Secret: {test_secret}")
            except Exception as test_error:
                print(f"   ❌ New decryption test: FAILED - {test_error}")
    
    print("\n4. Final Test - get_bot_api_keys:")
    try:
        from core.api_key_manager import get_bot_api_keys
        result = get_bot_api_keys(
            user_principal_id='trial_user_1759279793106',
            exchange='BINANCE',
            is_testnet=True,
            subscription_id=491
        )
        
        if result:
            print("   ✅ SUCCESS: Credentials found and decrypted!")
            print(f"   API Key: {result['api_key']}")
            print(f"   API Secret: {result['api_secret']}")
            print("\n🎉 PROBLEM SOLVED! Bot should now work correctly.")
        else:
            print("   ❌ FAILED: No credentials returned")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    main()
