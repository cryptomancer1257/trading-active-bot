#!/usr/bin/env python3
"""
Debug script for trade execution issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core import crud, models
from services.exchange_factory import ExchangeFactory
from core.tasks import execute_trade_action
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_trade_execution(subscription_id: int):
    """Debug trade execution for a specific subscription"""
    
    db = SessionLocal()
    try:
        # Get subscription
        subscription = crud.get_subscription_by_id(db, subscription_id)
        if not subscription:
            print(f"❌ Subscription {subscription_id} not found")
            return
        
        print(f"🔍 Debugging subscription {subscription_id}")
        print(f"   User: {subscription.user.email}")
        print(f"   Bot: {subscription.bot.name}")
        print(f"   Status: {subscription.status}")
        print(f"   Testnet: {subscription.is_testnet}")
        print(f"   Trading Pair: {subscription.trading_pair}")
        print(f"   Timeframe: {subscription.timeframe}")
        
        # Get exchange credentials
        exchange_type = subscription.exchange_type or models.ExchangeType.BINANCE
        use_testnet = getattr(subscription, 'is_testnet', True)
        
        print(f"\n🔑 Exchange Credentials:")
        credentials = crud.get_user_exchange_credentials(
            db, 
            user_id=subscription.user.id, 
            exchange=exchange_type.value,
            is_testnet=use_testnet
        )
        
        if credentials:
            cred = credentials[0]
            print(f"   Exchange: {exchange_type.value}")
            print(f"   Testnet: {use_testnet}")
            print(f"   API Key: {cred.api_key[:10]}...")
            print(f"   Status: {cred.validation_status}")
        else:
            print(f"   ❌ No exchange credentials found")
            return
        
        # Create exchange client
        print(f"\n🌐 Creating exchange client...")
        exchange = ExchangeFactory.create_exchange(
            exchange_name=exchange_type.value,
            api_key=cred.api_key,
            api_secret=cred.api_secret,
            testnet=use_testnet
        )
        
        # Get current price
        trading_pair = subscription.trading_pair or 'BTC/USDT'
        exchange_symbol = trading_pair.replace('/', '')
        
        try:
            ticker = exchange.get_ticker(exchange_symbol)
            current_price = float(ticker['price'])
            print(f"   Current price: ${current_price:.2f}")
        except Exception as e:
            print(f"   ❌ Failed to get price: {e}")
            return
        
        # Get balance
        try:
            base_asset = trading_pair.split('/')[0]
            quote_asset = trading_pair.split('/')[1]
            
            base_balance = exchange.get_balance(base_asset)
            quote_balance = exchange.get_balance(quote_asset)
            
            print(f"\n💰 Balance:")
            print(f"   {base_asset}: {base_balance.free} (free) + {base_balance.locked} (locked)")
            print(f"   {quote_asset}: {quote_balance.free} (free) + {quote_balance.locked} (locked)")
            
        except Exception as e:
            print(f"   ❌ Failed to get balance: {e}")
            return
        
        # Test SELL action
        print(f"\n🧪 Testing SELL action...")
        from bots.bot_sdk.Action import Action
        
        # Create a test SELL action
        test_action = Action.sell("PERCENTAGE", 5.0, "Test sell order")
        print(f"   Action: {test_action}")
        
        # Execute trade
        result = execute_trade_action(db, subscription, exchange, test_action, current_price)
        print(f"   Result: {'✅ Success' if result else '❌ Failed'}")
        
        # Check recent logs
        print(f"\n📝 Recent logs:")
        logs = crud.get_subscription_logs(db, subscription_id, limit=5)
        for log in logs:
            print(f"   {log.timestamp}: {log.action} - {log.details}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_trade_execution.py <subscription_id>")
        sys.exit(1)
    
    subscription_id = int(sys.argv[1])
    debug_trade_execution(subscription_id) 