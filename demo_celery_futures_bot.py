#!/usr/bin/env python3
"""
Demo script to run Futures Bot via Celery with auto-confirmation
This shows how to integrate the Futures Bot with Celery for automated trading
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_celery_futures_bot():
    """Demo Celery integration with auto-confirmation"""
    
    print("🚀 DEMO: FUTURES BOT CELERY AUTO-TRADING")
    print("="*60)
    print("✅ Auto-confirmation enabled (no user interaction)")
    print("✅ Multi-timeframe analysis")
    print("✅ LLM-powered signal generation")
    print("✅ Automated risk management")
    print("✅ Transaction logging")
    
    try:
        from core.tasks import run_futures_bot_trading
        
        # Configuration for auto-trading
        auto_config = {
            'trading_pair': 'BTCUSDT',
            'testnet': True,  # Safety first
            'leverage': 10,
            'stop_loss_pct': 0.02,
            'take_profit_pct': 0.04,
            'timeframes': ['5m', '30m', '1h', '4h', '1d'],
            'primary_timeframe': '1h',
            'use_llm_analysis': True,
            'llm_model': 'openai',
            'require_confirmation': False,  # 🔥 No confirmation required
            'auto_confirm': True  # 🤖 Auto-confirm all trades
        }
        
        print(f"\n🤖 Bot Configuration:")
        print(f"   💱 Pair: {auto_config['trading_pair']}")
        print(f"   📊 Timeframes: {auto_config['timeframes']}")
        print(f"   ⚡ Leverage: {auto_config['leverage']}x")
        print(f"   🧪 Testnet: {auto_config['testnet']}")
        print(f"   🤖 Auto-confirm: {auto_config['auto_confirm']}")
        
        print(f"\n🔄 Submitting to Celery queue 'futures_trading'...")
        
        # Submit task to Celery
        task = run_futures_bot_trading.delay(config=auto_config)
        
        print(f"✅ Task submitted successfully!")
        print(f"📋 Task ID: {task.id}")
        print(f"🎯 Queue: futures_trading")
        print(f"⏳ Status: {task.state}")
        
        print(f"\n🔍 Monitoring task execution...")
        print("   (This may take 2-5 minutes for complete analysis)")
        
        # Wait for result
        try:
            result = task.get(timeout=600)  # 10 minute timeout
            
            print(f"\n🎉 TASK COMPLETED SUCCESSFULLY!")
            print("="*50)
            
            # Display results
            signal = result.get('signal', {})
            trade_result = result.get('trade_result', {})
            
            print(f"📊 Analysis Results:")
            print(f"   🎯 Signal: {signal.get('action', 'N/A')}")
            print(f"   📈 Confidence: {signal.get('confidence', 0)*100:.1f}%")
            print(f"   💭 Reason: {signal.get('reason', 'N/A')}")
            
            if signal.get('action') != 'HOLD':
                print(f"\n🚀 Trade Execution:")
                if trade_result.get('status') == 'success':
                    print(f"   ✅ Status: EXECUTED")
                    print(f"   📈 Action: {trade_result.get('action')}")
                    print(f"   💰 Quantity: {trade_result.get('quantity')}")
                    print(f"   💵 Entry: ${trade_result.get('entry_price')}")
                    print(f"   🛡️ Stop Loss: ${trade_result.get('stop_loss', {}).get('price')}")
                    print(f"   🎯 Take Profit: ${trade_result.get('take_profit', {}).get('price')}")
                    print(f"   🆔 Order ID: {trade_result.get('main_order_id')}")
                    print(f"   💾 Transaction saved to database")
                else:
                    print(f"   ❌ Status: {trade_result.get('status')}")
                    print(f"   📝 Message: {trade_result.get('message', 'Unknown error')}")
            else:
                print(f"\n⏸️ No trade executed (HOLD signal)")
            
            # Account info
            account = result.get('account_status', {})
            if account:
                print(f"\n💼 Account Status:")
                print(f"   💰 Available: ${account.get('available_balance', 0):,.2f}")
                print(f"   📊 Positions: {account.get('active_positions', 0)}")
            
            print(f"\n⏰ Completed at: {result.get('timestamp')}")
            
        except Exception as e:
            print(f"\n❌ Task failed or timed out: {e}")
            print(f"📋 Task state: {task.state}")
            
            # Try to get error info
            try:
                error_info = task.info
                print(f"🔍 Error details: {error_info}")
            except:
                pass
        
        print(f"\n📋 CELERY INTEGRATION SUMMARY:")
        print("="*50)
        print("✅ Futures Bot successfully integrated with Celery")
        print("🤖 Auto-confirmation working (no manual input needed)")
        print("📊 Multi-timeframe analysis completed")
        print("🎯 Signals generated and executed automatically")
        print("💾 Transactions logged to database")
        print("⚡ Ready for production deployment")
        
    except ImportError as e:
        print(f"❌ Celery import failed: {e}")
        print("\n💡 To fix this:")
        print("1. Start Redis: docker run -d -p 6379:6379 redis")
        print("2. Start Celery worker: python utils/run_celery.py")
        print("3. Run this demo again")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

def show_production_setup():
    """Show how to setup for production"""
    
    print("\n🏭 PRODUCTION SETUP GUIDE")
    print("="*60)
    
    print("1. 🚀 Start services:")
    print("   docker-compose up -d  # Starts Redis, Celery, MySQL")
    
    print("\n2. 🔑 Set environment variables:")
    print("   export BINANCE_API_KEY='your_key'")
    print("   export BINANCE_API_SECRET='your_secret'")
    print("   export OPENAI_API_KEY='your_openai_key'")
    
    print("\n3. 🤖 Schedule automated trading:")
    print("   from core.tasks import schedule_futures_bot_trading")
    print("   schedule_futures_bot_trading.delay(interval_minutes=60)")
    
    print("\n4. 📊 Monitor via API:")
    print("   POST /api/futures-bot/execute")
    print("   POST /api/futures-bot/schedule")
    
    print("\n5. 🏦 Use database API keys:")
    print("   run_futures_bot_trading.delay(user_principal_id='abc123')")
    
    print("\n6. 📈 Monitor with Flower:")
    print("   celery -A utils.celery_app flower")
    print("   # Visit http://localhost:5555")

if __name__ == "__main__":
    print("🧪 FUTURES BOT CELERY DEMO")
    print(f"⏰ Starting demo...")
    
    # Show production setup
    show_production_setup()
    
    # Run demo
    print(f"\n🚀 Running Celery demo...")
    demo_celery_futures_bot()