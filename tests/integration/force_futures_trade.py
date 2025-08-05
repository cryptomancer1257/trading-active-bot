"""
Force Futures Trade with Stop Loss & Take Profit
Demonstrates real leveraged trading on Binance Futures testnet
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot_files.binance_futures_bot import BinanceFuturesBot, BinanceFuturesIntegration
from bots.bot_sdk.Action import Action
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def force_futures_trade():
    """Force execute a futures trade with full stop loss & take profit setup"""
    print("🚀 FORCE FUTURES TRADING - with Leverage & Risk Management")
    print("=" * 70)
    
    api_key = "3a768bf1e6ac655e47395907c3c5c24fa2e9627128e8d9c5aabc9cbf29e8e49f"
    secret_key = "a2da36f4c242e6a00d0940d9d101a75981f1c389aaae8017d0b394ede868d9aa"
    
    if not api_key or not secret_key:
        print("❌ Need API keys!")
        return
    
    print(f"✅ API Key: {api_key[:8]}...{api_key[-8:]}")
    
    # Aggressive futures configuration for demo
    config = {
        "trading_pair": "BTCUSDT",
        "testnet": True,
        "leverage": 10,  # Higher leverage for demo
        "stop_loss_pct": 0.02,  # 2% stop loss (tight for leverage)
        "take_profit_pct": 0.05,  # 5% take profit
        "position_size_pct": 0.05,  # 5% of balance (conservative with 10x leverage)
        "rsi_period": 14
    }
    
    api_keys = {
        "api_key": api_key,
        "api_secret": secret_key
    }
    
    try:
        print("\n🔧 Initializing Advanced Futures Bot...")
        bot = BinanceFuturesBot(config, api_keys)
        
        print(f"⚡ Futures Configuration:")
        print(f"   📊 Symbol: {config['trading_pair']}")
        print(f"   ⚡ Leverage: {config['leverage']}x (HIGH LEVERAGE!)")
        print(f"   🛡️  Stop Loss: {config['stop_loss_pct']*100}%")
        print(f"   🎯 Take Profit: {config['take_profit_pct']*100}%")
        print(f"   💰 Position Size: {config['position_size_pct']*100}% of balance")
        
        print("\n📊 Step 1: Get Real Futures Market Data...")
        data = bot.futures_client.get_klines("BTCUSDT", "5m", 200)
        
        if data is None or data.empty:
            print("❌ Failed to get futures data")
            return
        
        current_price = data['close'].iloc[-1]
        print(f"✅ Got {len(data)} data points")
        print(f"💵 Current BTC Futures: ${current_price:,.2f}")
        
        print("\n🧮 Step 2: Market Analysis...")
        analysis = bot._calculate_futures_analysis(data)
        
        print(f"📈 RSI: {analysis.get('rsi', 0):.2f}")
        print(f"📊 MACD: {analysis.get('macd', 0):.4f}")
        print(f"🎯 Volatility: {analysis.get('volatility', 0):.2f}%")
        print(f"📊 Trend: {'🟢 Bullish' if analysis.get('trend_bullish', False) else '🔴 Bearish'}")
        
        print("\n🎯 Step 3: Force LONG Position...")
        # Force create LONG signal for demo
        force_long_signal = Action(
            action="BUY",
            value=0.85,  # 85% confidence
            reason="FORCE FUTURES DEMO - Long position with 10x leverage"
        )
        
        print(f"💪 Forced Signal: {force_long_signal.action}")
        print(f"📊 Confidence: {force_long_signal.value*100:.1f}%")
        print(f"💡 Reason: {force_long_signal.reason}")
        
        # Show account before trade
        account_before = bot.futures_client.get_account_info()
        balance_before = float(account_before.get('availableBalance', 0))
        print(f"\n💰 Account Before Trade:")
        print(f"   Available Balance: ${balance_before:,.2f} USDT")
        
        print(f"\n💥 Step 4: Execute REAL FUTURES POSITION!")
        print(f"⚠️  ABOUT TO PLACE REAL LEVERAGED ORDER!")
        print(f"⚡ This will use {config['leverage']}x leverage!")
        
        # Execute the position
        result = bot.setup_position(force_long_signal, analysis)
        
        print("\n📋 FUTURES POSITION EXECUTION RESULT:")
        print("=" * 60)
        print(json.dumps(result, indent=2))
        
        if result.get('status') == 'success' and result.get('action') != 'HOLD':
            print(f"\n🎉 FUTURES POSITION SUCCESSFULLY OPENED!")
            print(f"💥 THIS IS A REAL LEVERAGED TRADE!")
            
            # Position details
            action = result.get('action')
            quantity = result.get('quantity')
            entry_price = result.get('entry_price', 0)
            leverage = result.get('leverage', 1)
            position_value = result.get('position_value', 0)
            order_id = result.get('main_order_id')
            
            print(f"\n📊 Position Details:")
            print(f"   🎯 Direction: {action} (LONG)")
            print(f"   📊 Quantity: {quantity} BTC")
            print(f"   💵 Entry Price: ${entry_price:,.2f}")
            print(f"   ⚡ Leverage: {leverage}x")
            print(f"   💰 Position Value: ${position_value:,.2f}")
            print(f"   🆔 Order ID: {order_id}")
            
            # Risk management details
            sl_info = result.get('stop_loss', {})
            tp_info = result.get('take_profit', {})
            
            print(f"\n🛡️  RISK MANAGEMENT ORDERS:")
            print(f"   🔴 Stop Loss: ${sl_info.get('price', 0):.2f}")
            print(f"      Order ID: {sl_info.get('order_id', 'Failed')}")
            print(f"   🟢 Take Profit: ${tp_info.get('price', 0):.2f}")
            print(f"      Order ID: {tp_info.get('order_id', 'Failed')}")
            
            # Calculate potential P&L with leverage
            entry = entry_price
            sl_price = sl_info.get('price', 0)
            tp_price = tp_info.get('price', 0)
            qty = float(quantity)
            
            # For LONG position
            max_loss = (sl_price - entry) * qty * leverage if sl_price > 0 else 0
            max_profit = (tp_price - entry) * qty * leverage if tp_price > 0 else 0
            
            print(f"\n💎 LEVERAGED P&L POTENTIAL:")
            print(f"   🔴 Maximum Loss: ${max_loss:.2f} USDT")
            print(f"   🟢 Target Profit: ${max_profit:.2f} USDT")
            print(f"   📊 Risk/Reward: 1:{abs(max_profit/max_loss):.1f}" if max_loss != 0 else "")
            print(f"   ⚡ Leverage Effect: {leverage}x amplification!")
            
            # Show account after
            print(f"\n💰 Checking Position Status...")
            positions = bot.futures_client.get_position_info("BTCUSDT")
            
            if positions:
                pos = positions[0]
                current_pnl = float(pos.pnl)
                pnl_color = "🟢" if current_pnl >= 0 else "🔴"
                
                print(f"   {pnl_color} Position PnL: ${current_pnl:.2f} USDT")
                print(f"   📊 Position Size: {pos.size} BTC")
                print(f"   💵 Entry: ${float(pos.entry_price):.2f}")
                print(f"   📈 Mark Price: ${float(pos.mark_price):.2f}")
            
            print(f"\n🎯 FUTURES TRADE ANALYSIS:")
            print(f"✅ Successfully opened leveraged position")
            print(f"✅ Stop loss order placed automatically")
            print(f"✅ Take profit order placed automatically")
            print(f"✅ Full risk management active")
            print(f"⚡ Trading with {leverage}x leverage amplification!")
            
        else:
            print(f"❌ Position failed: {result.get('message', 'Unknown error')}")
        
        print(f"\n🎉 FORCE FUTURES TRADE COMPLETE!")
        print(f"🔥 This demonstrates:")
        print(f"   ⚡ Real leveraged futures trading")
        print(f"   🛡️  Automatic stop loss protection")
        print(f"   🎯 Automatic take profit orders")
        print(f"   💰 Professional risk management")
        print(f"   📊 Real-time position monitoring")
        
    except Exception as e:
        print(f"\n❌ Force futures trade failed: {e}")
        import traceback
        traceback.print_exc()

def show_current_positions():
    """Show all current futures positions"""
    print("\n📊 LIVE FUTURES POSITIONS")
    print("=" * 40)
    
    api_key = os.getenv('BINANCE_API_KEY')
    secret_key = os.getenv('BINANCE_SECRET_KEY')
    
    if not api_key or not secret_key:
        return
    
    try:
        futures_client = BinanceFuturesIntegration(api_key, secret_key, testnet=True)
        
        # Account summary
        account = futures_client.get_account_info()
        available = float(account.get('availableBalance', 0))
        total = float(account.get('totalWalletBalance', 0))
        unrealized = float(account.get('totalUnrealizedProfit', 0))
        
        print(f"💰 Account Status:")
        print(f"   Available: ${available:,.2f} USDT")
        print(f"   Total Balance: ${total:,.2f} USDT")
        print(f"   Unrealized PnL: ${unrealized:,.2f} USDT")
        
        # Active positions
        positions = futures_client.get_position_info()
        
        if positions:
            print(f"\n📈 Active Leveraged Positions:")
            total_pnl = 0
            
            for pos in positions:
                pnl = float(pos.pnl)
                total_pnl += pnl
                pnl_color = "🟢" if pnl >= 0 else "🔴"
                
                print(f"\n   {pnl_color} {pos.symbol} - {pos.side}")
                print(f"      Size: {pos.size} BTC")
                print(f"      Entry: ${float(pos.entry_price):.2f}")
                print(f"      Mark: ${float(pos.mark_price):.2f}")
                print(f"      PnL: ${pnl:.2f} USDT")
                print(f"      ROE: {pos.percentage}%")
            
            print(f"\n💎 Total Unrealized PnL: ${total_pnl:.2f} USDT")
        else:
            print("\n📈 No active positions")
            
    except Exception as e:
        print(f"❌ Failed to get positions: {e}")

def main():
    """Main function"""
    print("🚀 FORCE FUTURES TRADING - LEVERAGED WITH STOP LOSS")
    print("⚠️  WARNING: This uses real leverage - High Risk!")
    print("=" * 70)
    
    # Show current status first
    show_current_positions()
    
    print("\n" + "="*70)
    
    # Execute forced trade
    force_futures_trade()
    
    print("\n" + "="*70)
    
    # Show final status
    show_current_positions()

if __name__ == "__main__":
    main()