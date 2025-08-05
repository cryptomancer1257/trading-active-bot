import os
import sys
sys.path.append('.')

# Set database URL
os.environ['DATABASE_URL'] = 'mysql+pymysql://botuser:botpassword123@localhost:3307/bot_marketplace'

from core.database import get_db
from core.api_key_manager import APIKeyManager
from core.models import Subscription, ExchangeCredentials, User
from sqlalchemy.orm import Session

def check_keys():
    print("🔍 KIỂM TRA DATABASE KEYS (CORRECT METHOD)...")
    
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
                print(f"   - API Key (encrypted): {credentials.api_key[:50]}...")
                print(f"   - API Secret (encrypted): {credentials.api_secret[:50]}...")
                
                # Method 2: Use API Manager để decrypt với method đúng
                print(f"\n🔓 Decrypt credentials using API Manager:")
                try:
                    decrypted = api_manager.get_user_credentials_by_principal_id(
                        db, principal_id, "BINANCE", True
                    )
                    
                    if decrypted:
                        print(f"✅ Decrypted successfully:")
                        print(f"   - API Key: {decrypted['api_key']}")
                        print(f"   - API Secret: {decrypted['api_secret']}")
                        
                        # Kiểm tra có phải là Binance keys đã biết không
                        expected_api_key = "3a768bf1e6ac655e47395907c3c5c24fa2e9627128e8d9c5aabc9cbf29e8e49f"
                        expected_api_secret = "a2da36f4c242e6a00d0940d9d101a75981f1c389aaae8017d0b394ede868d9aa"
                        
                        print(f"\n🔍 Kiểm tra API keys:")
                        print(f"   - Expected API Key: {expected_api_key}")
                        print(f"   - Actual API Key: {decrypted['api_key']}")
                        print(f"   - Keys match: {decrypted['api_key'] == expected_api_key}")
                        
                        if decrypted['api_key'] == expected_api_key:
                            print("✅ BINANCE API KEYS CHÍNH XÁC!")
                        else:
                            print("⚠️  BINANCE API KEYS KHÁC VỚI EXPECTED")
                        
                    else:
                        print("❌ Failed to decrypt credentials")
                except Exception as e:
                    print(f"❌ Decryption error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("❌ Không tìm thấy Exchange Credentials")
                
        else:
            print("❌ Không tìm thấy subscription cho Principal ID này")
            
        # Check environment variables cho LLM keys
        print(f"\n🌍 ENVIRONMENT VARIABLES:")
        openai_key = os.getenv('OPENAI_API_KEY', 'Not set')
        claude_key = os.getenv('CLAUDE_API_KEY', 'Not set')
        gemini_key = os.getenv('GEMINI_API_KEY', 'Not set')
        
        print(f"   - OPENAI_API_KEY: {openai_key[:30]}..." if openai_key != 'Not set' else "   - OPENAI_API_KEY: Not set")
        print(f"   - CLAUDE_API_KEY: {claude_key[:30]}..." if claude_key != 'Not set' else "   - CLAUDE_API_KEY: Not set")
        print(f"   - GEMINI_API_KEY: {gemini_key[:30]}..." if gemini_key != 'Not set' else "   - GEMINI_API_KEY: Not set")
        
        # Test OpenAI key validity
        if openai_key != 'Not set':
            print(f"\n🤖 TESTING OPENAI API KEY:")
            try:
                import openai
                client = openai.OpenAI(api_key=openai_key)
                
                # Simple test call
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                print("✅ OpenAI API key is VALID!")
            except Exception as e:
                print(f"❌ OpenAI API key is INVALID: {e}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_keys()
