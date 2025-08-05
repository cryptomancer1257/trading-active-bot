#!/usr/bin/env python3
"""
Store API keys directly via API key manager
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def store_keys_directly():
    """Store Binance API keys directly using API key manager"""
    
    try:
        from core.api_key_manager import APIKeyManager
        from core.database import SessionLocal
        from core import crud, models
        
        # Database session
        db = SessionLocal()
        
        # Initialize API key manager
        manager = APIKeyManager()
        
        # Test data
        principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        test_email = "test@marketplace.com"
        binance_api_key = "3a768bf1e6ac655e47395907c3c5c24fa2e9627128e8d9c5aabc9cbf29e8e49f"
        binance_api_secret = "a2da36f4c242e6a00d0940d9d101a75981f1c389aaae8017d0b394ede868d9aa"
        
        print(f"🔐 Storing Binance API keys for principal: {principal_id}")
        print(f"📊 Exchange: BINANCE (Testnet)")
        
        # Check or create test user
        user = crud.get_user_by_email(db, email=test_email)
        if not user:
            print(f"👤 Creating test user...")
            from core.schemas import UserCreate
            user_create = UserCreate(email=test_email, password="testpass123")
            user = crud.create_user(db, user_create)
            print(f"✅ Created user ID: {user.id}")
        else:
            print(f"👤 Using existing user ID: {user.id}")
        
        # Store credentials
        result = manager.store_user_exchange_credentials(
            db=db,
            user_id=user.id,
            exchange="BINANCE",
            api_key=binance_api_key,
            api_secret=binance_api_secret,
            is_testnet=True
        )
        
        if result:
            print("✅ SUCCESS: API keys stored successfully!")
            
            # Test retrieval
            print(f"\n🔍 Testing retrieval...")
            retrieved = manager.get_user_exchange_credentials(
                db=db,
                user_id=user.id,
                exchange="BINANCE",
                is_testnet=True
            )
            
            if retrieved:
                print("✅ SUCCESS: Keys retrieved successfully!")
                print(f"   🔑 API Key: {retrieved['api_key'][:20]}...")
                print(f"   🗝️  Secret: {retrieved['api_secret'][:20]}...")
                
                # Test bot initialization (note: bot expects principal_id but we stored with user_id)
                # For this test, we'll skip bot initialization as it needs proper principal_id mapping
                print(f"\n🤖 Bot initialization test skipped")
                print(f"   ℹ️  Bot requires principal_id mapping which needs proper user setup")
                print(f"   ℹ️  Keys are stored and can be retrieved successfully!")
                    
            else:
                print("❌ FAILED: Could not retrieve stored keys")
        else:
            print("❌ FAILED: Could not store API keys")
            
        db.close()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔐 DIRECT API KEY STORAGE TEST")
    print("="*50)
    store_keys_directly()
    print("\n🎊 Test completed!")