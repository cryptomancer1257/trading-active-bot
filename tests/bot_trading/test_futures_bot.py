"""
Test Binance Futures Trading Bot with Stop Loss
Demonstrates real futures trading on Binance testnet
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from binance_futures_bot import BinanceFuturesBot, BinanceFuturesIntegration
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_futures_connectivity():
    """Test Binance Futures API connectivity"""
    print("\n🔗 Testing Futures API Connectivity...")
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Missing API keys!")
        return False
    
    try:
        futures_client = BinanceFuturesIntegration(api_key, secret_key, testnet=True)
        
        # Test ping
        if futures_client.test_connectivity():
            print("✅ Futures API connectivity OK")
        else:
            print("❌ Futures API connectivity failed")
            return False
        
        # Test account info
        account = futures_client.get_account_info()
        print(f"📊 Futures Account Type: {account.get('accountType', 'Unknown')}")
        print(f"💰 Available Balance: ${float(account.get('availableBalance', 0)):.2f} USDT")
        print(f"🔐 Can Trade: {account.get('canTrade', False)}")
        
        # Show active positions
        positions = futures_client.get_position_info()
        if positions:
            print(f"\n📈 Active Positions:")
            for pos in positions:
                print(f"   {pos.symbol}: {pos.side} {pos.size} @ ${float(pos.entry_price):.2f} (PnL: ${float(pos.pnl):.2f})")
        else:
            print("\n📈 No active positions")
        
        return True
        
    except Exception as e:
        print(f"❌ Futures connectivity test failed: {e}")
        return False

def test_futures_trading():
    """Test futures trading with stop loss"""
    print("\n🚀 FUTURES TRADING TEST - with Stop Loss & Take Profit")
    print("=" * 70)
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Need API keys! Set:")
        print("export BINANCE_API_KEY='your_key'")
        print("export BINANCE_SECRET_KEY='your_secret'")
        return
    
    # Futures configuration
    config = {
        "trading_pair": "BTCUSDT",
        "testnet": True,
        "leverage": 5,  # Conservative leverage for testing
        "stop_loss_pct": 0.03,  # 3% stop loss
        "take_profit_pct": 0.06,  # 6% take profit (2:1 R/R ratio)
        "position_size_pct": 0.1,  # 10% of balance
        "rsi_period": 14,
        "rsi_oversold": 35,  # More conservative for futures
        "rsi_overbought": 65
    }
    
    api_keys = {
        "api_key": api_key,
        "api_secret": secret_key
    }
    
    try:
        print("🔧 Initializing Futures Bot...")
        bot = BinanceFuturesBot(config, api_keys)
        
        print(f"✅ Bot Config:")
        print(f"   📊 Symbol: {config['trading_pair']}")
        print(f"   ⚡ Leverage: {config['leverage']}x")
        print(f"   🛡️  Stop Loss: {config['stop_loss_pct']*100}%")
        print(f"   🎯 Take Profit: {config['take_profit_pct']*100}%")
        print(f"   💰 Position Size: {config['position_size_pct']*100}% of balance")
        
        print("\n📊 Step 1: Getting Futures Market Data...")
        # Get market data from futures client
        data = bot.futures_client.get_klines("BTCUSDT", "5m", 200)
        
        if data is None or data.empty:
            print("❌ Failed to get futures market data")
            return
        
        print(f"✅ Got {len(data)} futures data points")
        current_price = data['close'].iloc[-1]
        print(f"💵 Current BTC Futures Price: ${current_price:,.2f}")
        
        print("\n🧮 Step 2: Technical Analysis...")
        analysis = bot._calculate_futures_analysis(data)
        
        if 'error' in analysis:
            print(f"❌ Analysis error: {analysis['error']}")
            return
        
        print(f"📈 RSI: {analysis.get('rsi', 0):.2f}")
        print(f"📊 MACD: {analysis.get('macd', 0):.4f}")
        print(f"📊 SMA20: ${analysis.get('sma_20', 0):.2f}")
        print(f"📊 SMA50: ${analysis.get('sma_50', 0):.2f}")
        print(f"🎯 Volatility: {analysis.get('volatility', 0):.2f}%")
        print(f"📊 Volume Ratio: {analysis.get('volume_ratio', 0):.2f}x")
        
        print("\n🎯 Step 3: Generate Trading Signal...")
        signal = bot._generate_futures_signal(analysis, data)
        
        print(f"✅ Signal Generated:")
        print(f"   🎯 Action: {signal.action}")
        print(f"   📊 Confidence: {signal.value*100:.1f}%")
        print(f"   💡 Reason: {signal.reason}")
        
        print("\n💰 Step 4: Setup Futures Position with Stop Loss...")
        if signal.action != "HOLD":
            print("⚠️  About to place REAL FUTURES ORDER with LEVERAGE!")
            
            result = bot.setup_position(signal, analysis)
            
            print("\n📋 FUTURES POSITION RESULT:")
            print("=" * 50)
            print(json.dumps(result, indent=2))
            
            if result.get('status') == 'success':
                if result.get('action') != 'HOLD':
                    print(f"\n🎉 FUTURES POSITION OPENED!")
                    print(f"💰 Action: {result.get('action')} (Leveraged)")
                    print(f"📊 Quantity: {result.get('quantity')}")
                    print(f"💵 Entry Price: ${result.get('entry_price', 0):,.2f}")
                    print(f"⚡ Leverage: {result.get('leverage')}x")
                    print(f"💰 Position Value: ${result.get('position_value', 0):,.2f}")
                    print(f"🆔 Order ID: {result.get('main_order_id')}")
                    
                    # Stop Loss & Take Profit info
                    sl_info = result.get('stop_loss', {})
                    tp_info = result.get('take_profit', {})
                    
                    print(f"\n🛡️  Risk Management:")
                    print(f"   🔴 Stop Loss: ${sl_info.get('price', 0):.2f} (Order: {sl_info.get('order_id')})")
                    print(f"   🟢 Take Profit: ${tp_info.get('price', 0):.2f} (Order: {tp_info.get('order_id')})")
                    
                    # Calculate potential P&L
                    entry_price = result.get('entry_price', 0)
                    quantity = float(result.get('quantity', 0))
                    leverage = result.get('leverage', 1)
                    
                    if signal.action == "BUY":
                        sl_pnl = (sl_info.get('price', 0) - entry_price) * quantity * leverage
                        tp_pnl = (tp_info.get('price', 0) - entry_price) * quantity * leverage
                    else:
                        sl_pnl = (entry_price - sl_info.get('price', 0)) * quantity * leverage
                        tp_pnl = (entry_price - tp_info.get('price', 0)) * quantity * leverage
                    
                    print(f"\n💎 Potential P&L:")
                    print(f"   🔴 Max Loss (SL): ${sl_pnl:.2f}")
                    print(f"   🟢 Target Profit (TP): ${tp_pnl:.2f}")
                    print(f"   📊 Risk/Reward Ratio: 1:{abs(tp_pnl/sl_pnl):.1f}")
                    
                else:
                    print(f"⏸️  Action: HOLD - {result.get('reason', '')}")
            else:
                print(f"❌ Position setup failed: {result.get('message', 'Unknown error')}")
        else:
            print("⏸️  Signal is HOLD - No position opened")
        
        print(f"\n✅ FUTURES TRADING TEST COMPLETE!")
        print(f"🔥 Advanced features demonstrated:")
        print(f"   ⚡ Leverage trading")
        print(f"   🛡️  Automatic stop loss")
        print(f"   🎯 Take profit orders")
        print(f"   📊 Futures-specific analysis")
        print(f"   💰 Risk management")
        
    except Exception as e:
        print(f"\n❌ Futures test failed: {e}")
        import traceback
        traceback.print_exc()

def show_position_status():
    """Show current futures positions"""
    print("\n📊 CURRENT POSITIONS STATUS")
    print("=" * 40)
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("❌ Need API keys!")
        return
    
    try:
        futures_client = BinanceFuturesIntegration(api_key, secret_key, testnet=True)
        
        # Get account info
        account = futures_client.get_account_info()
        balance = float(account.get('availableBalance', 0))
        total_balance = float(account.get('totalWalletBalance', 0))
        unrealized_pnl = float(account.get('totalUnrealizedProfit', 0))
        
        print(f"💰 Account Summary:")
        print(f"   Available Balance: ${balance:.2f} USDT")
        print(f"   Total Balance: ${total_balance:.2f} USDT")
        print(f"   Unrealized PnL: ${unrealized_pnl:.2f} USDT")
        
        # Get positions
        positions = futures_client.get_position_info()
        
        if positions:
            print(f"\n📈 Active Futures Positions:")
            for pos in positions:
                pnl_color = "🟢" if float(pos.pnl) >= 0 else "🔴"
                print(f"   {pnl_color} {pos.symbol}: {pos.side}")
                print(f"      Size: {pos.size}")
                print(f"      Entry: ${float(pos.entry_price):.2f}")
                print(f"      Mark: ${float(pos.mark_price):.2f}")
                print(f"      PnL: ${float(pos.pnl):.2f}")
                print()
        else:
            print("\n📈 No active positions")
            
    except Exception as e:
        print(f"❌ Failed to get position status: {e}")

def main():
    """Main function"""
    print("🚀 BINANCE FUTURES TRADING BOT TEST")
    print("Advanced leveraged trading with stop loss")
    print("=" * 60)
    
    # Check API keys
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        print("\n❌ Missing API keys!")
        print("🔑 Setup Instructions:")
        print("1. Get API keys from: https://testnet.binancefuture.com/")
        print("2. Enable Futures trading permissions")
        print("3. Set environment variables:")
        print("   export BINANCE_API_KEY='your_key'")
        print("   export BINANCE_SECRET_KEY='your_secret'")
        return
    
    # Run tests
    if test_futures_connectivity():
        show_position_status()
        print("\n" + "="*70)
        test_futures_trading()
    else:
        print("❌ Cannot proceed - futures connectivity failed")

if __name__ == "__main__":
    main()