import os
import sys
sys.path.append('../..')

# Set database URL
os.environ['DATABASE_URL'] = 'mysql+pymysql://botuser:botpassword123@localhost:3307/bot_marketplace'

from core.database import get_db
from core.api_key_manager import APIKeyManager
from core.models import Subscription, ExchangeCredentials, User
from sqlalchemy.orm import Session

def check_keys():
    print("🔍 KIỂM TRA DATABASE KEYS...")
    
    # Get database session
    db_gen = get_db()
    db: Session = next(db_gen)
    
    try:
        # Initialize API Key Manager
        api_manager = APIKeyManager()
        print("✅ APIKeyManager initialized")
        
        # Check subscriptions với principal ID
        principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        print(f"\n📋 Tìm subscription cho Principal ID: {principal_id}")
        
        subscription = db.query(Subscription).filter(
            Subscription.user_principal_id == principal_id
        ).first()
        
        if subscription:
            print(f"✅ Tìm thấy subscription:")
            print(f"   - ID: {subscription.id}")
            print(f"   - User ID: {subscription.user_id}")
            print(f"   - Bot ID: {subscription.bot_id}")
            print(f"   - Principal ID: {subscription.user_principal_id}")
            
            # Lấy exchange credentials
            print(f"\n🔑 Lấy Exchange Credentials cho User ID: {subscription.user_id}")
            
            # Method 1: Direct database query
            credentials = db.query(ExchangeCredentials).filter(
                ExchangeCredentials.user_id == subscription.user_id,
                ExchangeCredentials.exchange == 'BINANCE',
                ExchangeCredentials.is_testnet == True
            ).first()
            
            if credentials:
                print(f"✅ Tìm thấy Exchange Credentials:")
                print(f"   - ID: {credentials.id}")
                print(f"   - Exchange: {credentials.exchange}")
                print(f"   - Is Testnet: {credentials.is_testnet}")
                print(f"   - Is Active: {credentials.is_active}")
                print(f"   - API Key (encrypted): {credentials.api_key_encrypted[:50]}...")
                print(f"   - API Secret (encrypted): {credentials.api_secret_encrypted[:50]}...")
                
                # Method 2: Use API Manager
                print(f"\n🔓 Decrypt credentials using API Manager:")
                decrypted = api_manager.get_credentials_by_principal_id(
                    db, principal_id, "BINANCE", True
                )
                
                if decrypted:
                    print(f"✅ Decrypted successfully:")
                    print(f"   - API Key: {decrypted['api_key'][:20]}...")
                    print(f"   - API Secret: {decrypted['api_secret'][:20]}...")
                else:
                    print("❌ Failed to decrypt credentials")
            else:
                print("❌ Không tìm thấy Exchange Credentials")
                
        else:
            print("❌ Không tìm thấy subscription cho Principal ID này")
            
            # List all subscriptions
            print("\n📋 Tất cả subscriptions trong database:")
            subscriptions = db.query(Subscription).all()
            for sub in subscriptions:
                print(f"   - ID: {sub.id}, User: {sub.user_id}, Principal: {sub.user_principal_id}")
                
        # Check all users
        print(f"\n👥 Tất cả users trong database:")
        users = db.query(User).all()
        for user in users:
            print(f"   - ID: {user.id}, Email: {user.email}")
            
        # Check all exchange credentials
        print(f"\n🔑 Tất cả Exchange Credentials:")
        all_creds = db.query(ExchangeCredentials).all()
        for cred in all_creds:
            print(f"   - User: {cred.user_id}, Exchange: {cred.exchange}, Testnet: {cred.is_testnet}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_keys()
