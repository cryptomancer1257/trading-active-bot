#!/usr/bin/env python3
"""
Store API keys directly via docker database on port 3307
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def store_keys_docker_db():
    """Store Binance API keys in docker database"""
    
    try:
        # Temporarily override database URL to connect to docker
        os.environ['DATABASE_URL'] = 'mysql+pymysql://botuser:botpassword123@localhost:3307/bot_marketplace'
        
        from core.api_key_manager import APIKeyManager
        from core.database import SessionLocal
        from core import crud, models
        
        # Database session with docker connection
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
        print(f"🐳 Database: Docker MySQL (bot_marketplace) on port 3307")
        
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
                
                # Now we need to create a principal ID mapping
                print(f"\n🔗 Creating principal ID mapping...")
                
                # Create exchange credentials record with principal ID
                from core.models import ExchangeCredentials
                from sqlalchemy.orm import Session
                
                # Check if credentials with principal_id already exist
                principal_creds = db.query(ExchangeCredentials).filter(
                    ExchangeCredentials.principal_id == principal_id,
                    ExchangeCredentials.exchange == models.ExchangeType.BINANCE,
                    ExchangeCredentials.is_testnet == True
                ).first()
                
                if not principal_creds:
                    # Create new record with principal_id
                    encrypted_key = manager.encrypt_api_key(binance_api_key)
                    encrypted_secret = manager.encrypt_api_key(binance_api_secret)
                    
                    principal_creds = ExchangeCredentials(
                        principal_id=principal_id,
                        exchange=models.ExchangeType.BINANCE,
                        api_key_encrypted=encrypted_key,
                        api_secret_encrypted=encrypted_secret,
                        is_testnet=True,
                        is_active=True,
                        validation_status="valid"
                    )
                    
                    db.add(principal_creds)
                    db.commit()
                    db.refresh(principal_creds)
                    
                    print(f"✅ Created principal ID mapping: {principal_creds.id}")
                else:
                    print(f"✅ Principal ID mapping already exists: {principal_creds.id}")
                
                # Test principal ID retrieval
                print(f"\n🧪 Testing principal ID retrieval...")
                principal_retrieved = manager.get_credentials_by_principal_id(
                    db=db,
                    principal_id=principal_id,
                    exchange="BINANCE",
                    is_testnet=True
                )
                
                if principal_retrieved:
                    print("✅ SUCCESS: Principal ID retrieval working!")
                    print(f"   🔑 API Key: {principal_retrieved['api_key'][:20]}...")
                    print(f"   🗝️  Secret: {principal_retrieved['api_secret'][:20]}...")
                    
                    print(f"\n🎊 ALL TESTS PASSED!")
                    print(f"   ✅ API keys stored in database")
                    print(f"   ✅ Principal ID mapping created")
                    print(f"   ✅ Bot should now work with database keys")
                    
                else:
                    print("❌ FAILED: Principal ID retrieval failed")
                    
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
    print("🔐 DOCKER DATABASE API KEY STORAGE")
    print("="*50)
    store_keys_docker_db()
    print("\n🎊 Test completed!")