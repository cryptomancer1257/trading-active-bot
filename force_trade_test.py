"""
Force Trade Test - Execute Real Binance Testnet Trading
Forces bot to execute actual BUY/SELL orders for demonstration
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_files.binance_trading_bot import BinanceTradingBot
from bots.bot_sdk.Action import Action
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def force_trade_test():
    """
    Force execute real trades on Binance testnet
    Uses real API keys to place actual orders
    """
    print("🚀 FORCE TRADE TEST - Real Binance Testnet Orders")
    print("=" * 60)
    
    # Get API keys
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Need API keys! Set:")
        print("export BINANCE_API_KEY='your_key'")
        print("export BINANCE_SECRET_KEY='your_secret'")
        return
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-8:]}")
    
    # Configuration for aggressive trading
    config = {
        "exchange_type": "BINANCE",
        "trading_pair": "BTC/USDT", 
        "testnet": True,
        "timeframe": "5m",
        "rsi_period": 14,
        "rsi_oversold": 50,  # Higher threshold to trigger easier
        "rsi_overbought": 60,  # Lower threshold to trigger easier  
        "max_position_size": 0.001,  # Very small for safety
        "min_trade_amount": 10.0
    }
    
    api_keys = {
        "api_key": api_key,
        "api_secret": secret_key
    }
    
    try:
        print("\n🔄 Initializing Bot...")
        bot = BinanceTradingBot(config, api_keys)
        
        print("📊 Step 1: Getting Real Market Data...")
        historical_data = bot.crawl_data()
        if not historical_data:
            print("❌ Failed to get market data")
            return
        
        print(f"✅ Got {len(historical_data)} data points")
        current_price = historical_data[-1]['close']
        print(f"💵 Current BTC Price: ${current_price:,.2f}")
        
        print("\n📊 Step 2: Market Analysis...")
        analysis = bot.analyze_data(historical_data)
        if 'error' in analysis:
            print(f"❌ Analysis error: {analysis['error']}")
            return
        
        print(f"📈 RSI: {analysis.get('rsi', 0):.2f}")
        print(f"📊 MACD: {analysis.get('macd', 0):.4f}")
        print(f"🎯 Volume Ratio: {analysis.get('volume_ratio', 0):.2f}x")
        
        print("\n🎯 Step 3: Force BUY Signal...")
        # Force create BUY action for demo
        force_buy_action = Action(
            action="BUY",
            value=0.8,  # 80% confidence
            reason="FORCE TRADE TEST - Demonstrating real order execution"
        )
        
        print(f"✅ Forced Signal: {force_buy_action.action}")
        print(f"🎯 Confidence: {force_buy_action.value*100:.1f}%")
        print(f"💡 Reason: {force_buy_action.reason}")
        
        print("\n💰 Step 4: Execute REAL Trade...")
        print("⚠️  About to place REAL ORDER on Binance testnet!")
        
        # Execute the forced trade
        trade_result = bot.execute_trade(force_buy_action, analysis)
        
        print("\n📋 TRADE EXECUTION RESULT:")
        print("=" * 40)
        print(json.dumps(trade_result, indent=2))
        
        if trade_result.get('status') == 'success':
            if trade_result.get('action') != 'HOLD':
                print(f"\n🎉 REAL TRADE EXECUTED!")
                print(f"💰 Action: {trade_result.get('action')}")
                print(f"📊 Quantity: {trade_result.get('quantity')}")
                print(f"💵 Price: ${trade_result.get('price', 0):,.2f}")
                print(f"🆔 Order ID: {trade_result.get('order_id', 'N/A')}")
                print(f"⏰ Time: {trade_result.get('timestamp')}")
            else:
                print(f"⏸️  Action: HOLD - {trade_result.get('reason', '')}")
        else:
            print(f"❌ Trade failed: {trade_result.get('message', 'Unknown error')}")
        
        print("\n🔍 Step 5: Test SELL Order Too...")
        force_sell_action = Action(
            action="SELL", 
            value=0.7,
            reason="FORCE SELL TEST - Demonstrating sell order"
        )
        
        sell_result = bot.execute_trade(force_sell_action, analysis)
        print("\n📋 SELL ORDER RESULT:")
        print(json.dumps(sell_result, indent=2))
        
        print(f"\n✅ FORCE TRADE TEST COMPLETE!")
        print(f"🎯 Demonstrated real trading capabilities on Binance testnet")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_account_balance():
    """Test account balance and trading info"""
    print("\n💰 ACCOUNT BALANCE TEST")
    print("=" * 30)
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Need API keys!")
        return
    
    try:
        from services.exchange_factory import ExchangeFactory
        
        exchange = ExchangeFactory.create_exchange(
            exchange_name="BINANCE",
            api_key=api_key,
            api_secret=secret_key,
            testnet=True
        )
        
        # Test connection
        if exchange.test_connectivity():
            print("✅ Connected to Binance testnet")
        
        # Get account info
        account = exchange.get_account_info()
        print(f"📊 Account Type: {account.get('accountType', 'Unknown')}")
        print(f"🔐 Can Trade: {account.get('canTrade', False)}")
        
        # Check balances
        print(f"\n💰 Account Balances:")
        balances = account.get('balances', [])
        for balance in balances:
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            if free > 0 or locked > 0:
                asset = balance.get('asset', 'Unknown')
                print(f"   {asset}: Free={free:.8f}, Locked={locked:.8f}")
        
        # Get current BTC price
        current_price = exchange.get_current_price("BTCUSDT")
        print(f"\n📈 Current BTC/USDT: ${current_price:,.2f}")
        
    except Exception as e:
        print(f"❌ Balance test failed: {e}")

def main():
    """Main function"""
    print("Choose test:")
    print("1. Force Trade Test (Execute real orders)")
    print("2. Account Balance Test")
    print("3. Both")
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("\n❌ Missing API keys!")
        print("Set environment variables:")
        print("export BINANCE_API_KEY='your_key'")
        print("export BINANCE_SECRET_KEY='your_secret'")
        return
    
    # Run balance test first
    test_account_balance()
    
    print("\n" + "="*60)
    
    # Run force trade test
    force_trade_test()

if __name__ == "__main__":
    main()