"""
Test Script for Secure API Key Management System
Demonstrates how to use the new encrypted API key system
"""

import os
import sys
import logging
from sqlalchemy.orm import Session

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal, engine
from core import models
from core.api_key_manager import api_key_manager, get_bot_api_keys
from bot_files.binance_futures_bot import BinanceFuturesBot, create_futures_bot_for_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_api_key_encryption():
    """Test basic encryption/decryption functionality"""
    print("\n🔐 TESTING API KEY ENCRYPTION")
    print("=" * 50)
    
    # Test data
    test_api_key = "test_api_key_12345"
    test_secret = "test_secret_67890"
    
    try:
        # Test encryption
        encrypted_key = api_key_manager.encrypt_api_key(test_api_key)
        encrypted_secret = api_key_manager.encrypt_api_key(test_secret)
        
        print(f"✅ Original API Key: {test_api_key}")
        print(f"🔒 Encrypted API Key: {encrypted_key[:50]}...")
        
        # Test decryption
        decrypted_key = api_key_manager.decrypt_api_key(encrypted_key)
        decrypted_secret = api_key_manager.decrypt_api_key(encrypted_secret)
        
        print(f"🔓 Decrypted API Key: {decrypted_key}")
        
        # Verify
        assert decrypted_key == test_api_key, "Key decryption failed"
        assert decrypted_secret == test_secret, "Secret decryption failed"
        
        print("✅ Encryption/Decryption test PASSED")
        
    except Exception as e:
        print(f"❌ Encryption test FAILED: {e}")
        return False
    
    return True

def test_database_storage():
    """Test storing and retrieving encrypted credentials from database"""
    print("\n💾 TESTING DATABASE STORAGE")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Create test user if doesn't exist
        test_email = "test_crypto_trader@example.com"
        test_user = db.query(models.User).filter(models.User.email == test_email).first()
        
        if not test_user:
            test_user = models.User(
                email=test_email,
                hashed_password="test_hash",
                role=models.UserRole.USER
            )
            db.add(test_user)
            db.commit()
            print(f"✅ Created test user: {test_email}")
        else:
            print(f"✅ Using existing test user: {test_email}")
        
        # Test storing Binance credentials
        binance_api_key = "binance_test_api_key_12345"
        binance_secret = "binance_test_secret_67890"
        
        success = api_key_manager.store_user_exchange_credentials(
            db=db,
            user_id=test_user.id,
            exchange="BINANCE",
            api_key=binance_api_key,
            api_secret=binance_secret,
            is_testnet=True
        )
        
        if success:
            print("✅ Stored Binance testnet credentials")
        else:
            print("❌ Failed to store credentials")
            return False
        
        # Test retrieving credentials
        retrieved_creds = api_key_manager.get_user_exchange_credentials(
            db=db,
            user_id=test_user.id,
            exchange="BINANCE",
            is_testnet=True
        )
        
        if retrieved_creds:
            print("✅ Retrieved encrypted credentials from database")
            print(f"   Exchange: {retrieved_creds['exchange']}")
            print(f"   Is Testnet: {retrieved_creds['is_testnet']}")
            print(f"   API Key: {retrieved_creds['api_key'][:20]}...")
            print(f"   Validation Status: {retrieved_creds['validation_status']}")
            
            # Verify decryption worked
            assert retrieved_creds['api_key'] == binance_api_key, "API key mismatch"
            assert retrieved_creds['api_secret'] == binance_secret, "API secret mismatch"
            print("✅ Credential decryption verified")
        else:
            print("❌ Failed to retrieve credentials")
            return False
            
    except Exception as e:
        print(f"❌ Database storage test FAILED: {e}")
        return False
    finally:
        db.close()
    
    return True

def test_principal_id_lookup():
    """Test getting credentials by ICP Principal ID"""
    print("\n🆔 TESTING PRINCIPAL ID LOOKUP")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Create test subscription with principal ID
        test_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        test_email = "test_crypto_trader@example.com"
        
        # Get test user
        test_user = db.query(models.User).filter(models.User.email == test_email).first()
        if not test_user:
            print("❌ Test user not found. Run database storage test first.")
            return False
        
        # Create test subscription with principal ID
        test_subscription = db.query(models.Subscription).filter(
            models.Subscription.user_principal_id == test_principal_id
        ).first()
        
        if not test_subscription:
            test_subscription = models.Subscription(
                user_id=test_user.id,
                user_principal_id=test_principal_id,
                instance_name="Test Bot Instance",
                bot_id=1,  # Assuming bot ID 1 exists
                exchange_type=models.ExchangeType.BINANCE,
                trading_pair="BTCUSDT",
                is_testnet=True
            )
            db.add(test_subscription)
            db.commit()
            print(f"✅ Created test subscription with principal ID: {test_principal_id}")
        else:
            print(f"✅ Using existing subscription with principal ID: {test_principal_id}")
        
        # Test getting credentials by principal ID
        principal_creds = api_key_manager.get_user_credentials_by_principal_id(
            db=db,
            user_principal_id=test_principal_id,
            exchange="BINANCE",
            is_testnet=True
        )
        
        if principal_creds:
            print("✅ Retrieved credentials by Principal ID")
            print(f"   Principal ID: {test_principal_id}")
            print(f"   Exchange: {principal_creds['exchange']}")
            print(f"   API Key: {principal_creds['api_key'][:20]}...")
        else:
            print("❌ Failed to retrieve credentials by Principal ID")
            return False
            
    except Exception as e:
        print(f"❌ Principal ID lookup test FAILED: {e}")
        return False
    finally:
        db.close()
    
    return True

def test_bot_initialization():
    """Test initializing bot with encrypted API keys from database"""
    print("\n🤖 TESTING BOT INITIALIZATION WITH DATABASE KEYS")
    print("=" * 50)
    
    try:
        # Test the convenience function
        test_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        
        bot_keys = get_bot_api_keys(
            user_principal_id=test_principal_id,
            exchange="BINANCE",
            is_testnet=True
        )
        
        if bot_keys:
            print("✅ Retrieved bot API keys using convenience function")
            print(f"   API Key: {bot_keys['api_key'][:20]}...")
            print(f"   Has Secret: {bool(bot_keys['api_secret'])}")
            print(f"   Testnet: {bot_keys['testnet']}")
        else:
            print("❌ Failed to get bot API keys")
            return False
        
        # Test creating bot with database credentials
        test_config = {
            'trading_pair': 'BTCUSDT',
            'testnet': True,
            'leverage': 5,
            'use_llm_analysis': False  # Disable LLM for testing
        }
        
        print("\n🏗️ Creating bot with database credentials...")
        
        # This should fail gracefully if no API keys are found
        try:
            bot = create_futures_bot_for_user(test_principal_id, test_config)
            print("✅ Bot created successfully with database credentials")
            
            # Test connectivity (this might fail if keys are fake)
            connectivity = bot.futures_client.test_connectivity()
            print(f"🌐 API Connectivity Test: {'✅ Connected' if connectivity else '❌ Failed'}")
            
        except ValueError as e:
            print(f"⚠️ Expected error: {e}")
            print("✅ Bot initialization properly handles missing credentials")
        
    except Exception as e:
        print(f"❌ Bot initialization test FAILED: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 SECURE API KEY MANAGEMENT SYSTEM TESTS")
    print("=" * 60)
    
    tests = [
        ("Encryption/Decryption", test_api_key_encryption),
        ("Database Storage", test_database_storage),
        ("Principal ID Lookup", test_principal_id_lookup),
        ("Bot Initialization", test_bot_initialization)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    print(f"\n📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Secure API Key Management System is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
    
    print(f"\n🔑 USAGE SUMMARY:")
    print("1. Store encrypted API keys using API endpoints or admin interface")
    print("2. Create bots using Principal ID instead of hardcoded keys:")
    print("   bot = create_futures_bot_for_user(principal_id, config)")
    print("3. Keys are automatically decrypted and loaded from secure database")
    print("4. System supports multiple exchanges and testnet/mainnet separation")

if __name__ == "__main__":
    main()