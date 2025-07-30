"""
Test Script for Binance Trading Bot
Demonstrates real trading with actual Binance testnet API keys
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from binance_trading_bot import BinanceTradingBot, execute_trading_logic
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_with_real_api_keys():
    """
    Test bot with real Binance testnet API keys
    Set environment variables: BINANCE_API_KEY and BINANCE_SECRET_KEY
    """
    print("🚀 Binance Trading Bot - Real API Test")
    print("=" * 60)
    
    # Get API keys from environment
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ API keys not found!")
        print("\n📋 To test with real API keys:")
        print("1. Get keys from: https://testnet.binance.vision/")
        print("2. Set environment variables:")
        print("   export BINANCE_API_KEY='your_key_here'")
        print("   export BINANCE_SECRET_KEY='your_secret_here'")
        print("3. Run: python3 test_binance_bot.py")
        return
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-8:]}")
    print(f"✅ Secret Key: {'*' * len(secret_key)}")
    
    # Configuration for real trading
    config = {
        "exchange_type": "BINANCE",
        "trading_pair": "BTC/USDT",
        "testnet": True,
        "timeframe": "5m",
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "macd_fast": 12,
        "macd_slow": 26,
        "macd_signal": 9,
        "ma_fast_period": 20,
        "ma_slow_period": 50,
        "max_position_size": 0.01,  # Small size for testing
        "min_trade_amount": 10.0,
        "stop_loss_pct": 0.02
    }
    
    # API credentials
    api_keys = {
        "api_key": api_key,
        "api_secret": secret_key
    }
    
    try:
        print("\n🔄 Starting Real Trading Test...")
        
        # Execute complete trading logic
        result = execute_trading_logic(config, api_keys)
        
        # Display results
        print("\n📊 TRADING RESULTS:")
        print("=" * 40)
        print(json.dumps(result, indent=2))
        
        if result.get('status') == 'success':
            print("\n✅ Bot executed successfully!")
            
            signal = result.get('signal', {})
            print(f"📈 Signal: {signal.get('action', 'UNKNOWN')}")
            print(f"🎯 Confidence: {signal.get('confidence', 0):.1f}%")
            print(f"💡 Reason: {signal.get('reason', 'N/A')}")
            
            trade_result = result.get('trade_result', {})
            if trade_result.get('status') == 'success':
                if trade_result.get('action') == 'HOLD':
                    print(f"⏸️  Action: HOLD - {trade_result.get('reason', '')}")
                else:
                    print(f"💰 Trade: {trade_result.get('action')} {trade_result.get('quantity')} at ${trade_result.get('price', 0):.2f}")
            
            analysis = result.get('analysis', {})
            if analysis:
                print(f"\n📊 Market Analysis:")
                print(f"   💵 Current Price: ${analysis.get('current_price', 0):.2f}")
                print(f"   📈 RSI: {analysis.get('rsi', 0):.2f}")
                print(f"   📊 MACD: {analysis.get('macd', 0):.4f}")
                print(f"   📈 Volume Ratio: {analysis.get('volume_ratio', 0):.2f}x")
        else:
            print(f"\n❌ Bot failed: {result.get('message', 'Unknown error')}")
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

def test_bot_demo():
    """
    Demo test showing bot structure without real API calls
    """
    print("🎮 Binance Trading Bot - Demo Mode")
    print("=" * 50)
    
    # Demo configuration
    config = {
        "exchange_type": "BINANCE",
        "trading_pair": "BTC/USDT",
        "testnet": True,
        "rsi_period": 14,
        "max_position_size": 0.1
    }
    
    # Fake API keys for demo
    api_keys = {
        "api_key": "eTVRuGceal7eZq0AlNKQLLEw5AILFbMOY9Shp2BvXRvkiu5SCQNK4Pq4vaS9f6bd",
        "api_secret": "BgW2TKVLiFVy550iaBiHUNwIVnIiQ1Al1ldPoU9P2x6s3qWfV6BzHAeVZOQqDnJW"
    }
    
    try:
        # Initialize bot (won't make real API calls)
        bot = BinanceTradingBot(config, api_keys)
        
        print(f"✅ Bot initialized:")
        print(f"   📊 Trading Pair: {bot.trading_pair}")
        print(f"   ⏰ Timeframe: {bot.timeframe}")
        print(f"   🎯 RSI Period: {bot.rsi_period}")
        print(f"   💰 Max Position: {bot.max_position_size}")
        print(f"   🌐 Testnet: {bot.testnet}")
        
        print(f"\n🧮 Strategy Components:")
        print(f"   📈 RSI: Oversold < {bot.rsi_oversold}, Overbought > {bot.rsi_overbought}")
        print(f"   📊 MACD: Fast={bot.macd_fast}, Slow={bot.macd_slow}, Signal={bot.macd_signal}")
        print(f"   📊 MA: Fast={bot.ma_fast_period}, Slow={bot.ma_slow_period}")
        print(f"   ⚠️  Stop Loss: {bot.stop_loss_pct * 100}%")
        
        print(f"\n🔧 Methods Available:")
        print(f"   📥 crawl_data() - Get real market data from Binance")
        print(f"   🧮 analyze_data() - Calculate RSI, MACD, MA, Volume")
        print(f"   🎯 generate_signal() - BUY/SELL/HOLD with confidence")
        print(f"   💰 execute_trade() - Place actual orders on testnet")
        
        print(f"\n✅ Bot ready for real trading with API keys!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

def main():
    """Main function"""
    print("Choose test mode:")
    print("1. Real API Test (requires Binance testnet keys)")
    print("2. Demo Mode (shows bot structure)")
    
    # Check for API keys
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if api_key and secret_key:
        print("\n🔑 API keys detected - Running real test!")
        test_with_real_api_keys()
    else:
        print("\n🎮 No API keys - Running demo mode!")
        test_bot_demo()
        print("\n" + "="*50)
        print("🔑 To test with real API keys:")
        print("1. Visit: https://testnet.binance.vision/")
        print("2. Create API key with trading permissions")
        print("3. Set environment variables:")
        print("   export BINANCE_API_KEY='your_key'")
        print("   export BINANCE_SECRET_KEY='your_secret'")
        print("4. Run again: python3 test_binance_bot.py")

if __name__ == "__main__":
    main()