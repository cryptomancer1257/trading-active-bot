#!/usr/bin/env python3
"""
Create principal ID mapping via subscription
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_mapping():
    """Create principal ID to user mapping via subscription"""
    
    try:
        # Connect to docker database
        os.environ['DATABASE_URL'] = 'mysql+pymysql://botuser:botpassword123@localhost:3307/bot_marketplace'
        
        from core.database import SessionLocal
        from core import models, crud
        from datetime import datetime
        
        db = SessionLocal()
        
        principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        user_id = 4  # From previous creation
        
        print(f"🔗 Creating principal ID mapping...")
        print(f"   👤 User ID: {user_id}")
        print(f"   🆔 Principal ID: {principal_id}")
        
        # Check if mapping already exists
        existing = db.query(models.Subscription).filter(
            models.Subscription.user_principal_id == principal_id
        ).first()
        
        if existing:
            print(f"✅ Mapping already exists: Subscription ID {existing.id}")
        else:
            # Create a test subscription for mapping
            subscription = models.Subscription(
                user_id=user_id,
                user_principal_id=principal_id,
                instance_name="Test Mapping Subscription",
                bot_id=1,  # Dummy bot ID
                exchange_type=models.ExchangeType.BINANCE,
                trading_pair="BTCUSDT",
                timeframe="1h",
                strategy_config={},
                execution_config={
                    "buy_order_type": "USDT_AMOUNT",
                    "buy_order_value": 100,
                    "sell_order_type": "PERCENTAGE", 
                    "sell_order_value": 100
                },
                risk_config={
                    "stop_loss_percent": 2.0,
                    "take_profit_percent": 4.0
                },
                is_testnet=True,
                status=models.SubscriptionStatus.ACTIVE,
                started_at=datetime.utcnow()
            )
            
            db.add(subscription)
            db.commit()
            db.refresh(subscription)
            
            print(f"✅ Created mapping subscription: ID {subscription.id}")
        
        # Test the mapping
        print(f"\n🧪 Testing principal ID lookup...")
        from core.api_key_manager import APIKeyManager
        
        manager = APIKeyManager()
        credentials = manager.get_credentials_by_principal_id(
            db=db,
            user_principal_id=principal_id,
            exchange="BINANCE",
            is_testnet=True
        )
        
        if credentials:
            print("✅ SUCCESS: Principal ID mapping works!")
            print(f"   🔑 API Key: {credentials['api_key'][:20]}...")
            print(f"   🗝️  Secret: {credentials['api_secret'][:20]}...")
            print(f"\n🎊 READY TO TEST BOT!")
        else:
            print("❌ FAILED: Principal ID mapping not working")
            
        db.close()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔗 CREATING PRINCIPAL ID MAPPING")
    print("="*50)
    create_mapping()
    print("\n🎊 Mapping completed!")