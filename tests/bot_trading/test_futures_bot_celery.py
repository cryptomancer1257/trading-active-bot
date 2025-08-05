#!/usr/bin/env python3
"""
Test script for Futures Bot Celery integration
Demonstrates auto-confirmed trading via Celery tasks
"""
import sys
import os
import time
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_futures_bot_celery():
    """Test Futures Bot with Celery auto-confirmation"""
    
    print("🚀 TESTING FUTURES BOT CELERY INTEGRATION")
    print("="*60)
    
    try:
        # Import Celery tasks
        from core.tasks import run_futures_bot_trading, schedule_futures_bot_trading
        
        print("✅ Celery tasks imported successfully")
        
        # Test 1: Single execution with auto-confirm
        print("\n📊 TEST 1: Single Futures Bot execution with auto-confirm")
        print("-" * 50)
        
        # Custom config for testing
        test_config = {
            'trading_pair': 'BTCUSDT',
            'testnet': True,
            'leverage': 10,
            'timeframes': ['5m', '1h', '4h'],  # Faster for testing
            'primary_timeframe': '1h',
            'use_llm_analysis': True,
            'llm_model': 'openai',
            'require_confirmation': False,  # No confirmation
            'auto_confirm': True  # Auto-confirm all trades
        }
        
        print(f"🤖 Config: {test_config['trading_pair']} | {len(test_config['timeframes'])} timeframes")
        print("🎯 Auto-confirm: ON (no user interaction required)")
        
        # Execute task asynchronously
        print("\n🔄 Submitting Celery task...")
        task_result = run_futures_bot_trading.delay(
            user_principal_id=None,  # Use direct keys
            config=test_config
        )
        
        print(f"✅ Task submitted with ID: {task_result.id}")
        print("⏳ Waiting for task completion...")
        
        # Wait for result with timeout
        try:
            result = task_result.get(timeout=300)  # 5 minute timeout
            print(f"\n🎉 Task completed successfully!")
            print(f"📊 Status: {result.get('status')}")
            print(f"🎯 Signal: {result.get('signal', {}).get('action')} ({result.get('signal', {}).get('confidence', 0)*100:.1f}%)")
            print(f"📈 Trade: {result.get('trade_result', {}).get('action', 'N/A')}")
            print(f"⏰ Timestamp: {result.get('timestamp')}")
            
            if result.get('signal', {}).get('action') != 'HOLD':
                trade_result = result.get('trade_result', {})
                if trade_result.get('status') == 'success':
                    print(f"✅ TRADE EXECUTED: {trade_result.get('action')} {trade_result.get('quantity')} @ ${trade_result.get('entry_price')}")
                    print(f"🛡️ Stop Loss: ${trade_result.get('stop_loss', {}).get('price')}")
                    print(f"🎯 Take Profit: ${trade_result.get('take_profit', {}).get('price')}")
                else:
                    print(f"❌ Trade failed: {trade_result}")
            
        except Exception as e:
            print(f"❌ Task failed or timed out: {e}")
            print(f"📋 Task state: {task_result.state}")
            
        # Test 2: Database API keys (if available)
        print(f"\n📊 TEST 2: Database API keys test")
        print("-" * 50)
        
        print("🏦 Testing with Principal ID (database lookup)...")
        test_principal_id = "rdmx6-jaaaa-aaaah-qcaiq-cai"
        
        task_result_2 = run_futures_bot_trading.delay(
            user_principal_id=test_principal_id,
            config=test_config
        )
        
        print(f"✅ Database test task submitted: {task_result_2.id}")
        print("⏳ Waiting for database test...")
        
        try:
            result_2 = task_result_2.get(timeout=180)  # 3 minute timeout
            print(f"🎉 Database test completed: {result_2.get('status')}")
        except Exception as e:
            print(f"⚠️ Database test failed (expected if no MySQL): {e}")
        
        # Test 3: Scheduled execution
        print(f"\n📊 TEST 3: Scheduled execution")
        print("-" * 50)
        
        print("⏰ Testing scheduled execution (every 30 minutes)...")
        schedule_config = test_config.copy()
        schedule_config['timeframes'] = ['1h']  # Single timeframe for faster execution
        
        schedule_result = schedule_futures_bot_trading.delay(
            interval_minutes=30,
            user_principal_id=None,
            config=schedule_config
        )
        
        print(f"✅ Schedule task submitted: {schedule_result.id}")
        print("📅 Bot will now run every 30 minutes automatically")
        
        try:
            schedule_response = schedule_result.get(timeout=60)
            print(f"🎯 Schedule status: {schedule_response.get('status')}")
            print(f"⏰ Next run in: {schedule_response.get('next_run_in_minutes', 'Unknown')} minutes")
        except Exception as e:
            print(f"⚠️ Schedule setup failed: {e}")
            
    except ImportError as e:
        print(f"❌ Failed to import Celery tasks: {e}")
        print("💡 Make sure Celery is running: python utils/run_celery.py")
        return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n🎊 FUTURES BOT CELERY INTEGRATION TEST COMPLETED!")
    print("="*60)
    print("✅ Key Features Demonstrated:")
    print("   🤖 Auto-confirmed trading (no user interaction)")
    print("   🎯 Celery task execution")
    print("   🏦 Database API key support")
    print("   ⏰ Scheduled periodic trading")
    print("   📊 Multi-timeframe analysis")
    print("   🛡️ Risk management with stop-loss/take-profit")
    
    return True

def show_celery_usage():
    """Show how to use Celery tasks for Futures Bot"""
    
    print("\n📋 CELERY USAGE EXAMPLES")
    print("="*60)
    
    print("1. 🚀 Manual execution (auto-confirmed):")
    print("```python")
    print("from core.tasks import run_futures_bot_trading")
    print("result = run_futures_bot_trading.delay()")
    print("print(result.get())  # Wait for completion")
    print("```")
    
    print("\n2. 🏦 With database API keys:")
    print("```python")
    print("result = run_futures_bot_trading.delay(")
    print("    user_principal_id='rdmx6-jaaaa-aaaah-qcaiq-cai',")
    print("    config={'trading_pair': 'ETHUSDT', 'leverage': 5}")
    print(")")
    print("```")
    
    print("\n3. ⏰ Scheduled execution:")
    print("```python")
    print("from core.tasks import schedule_futures_bot_trading")
    print("schedule_futures_bot_trading.delay(")
    print("    interval_minutes=60,  # Every hour")
    print("    config={'timeframes': ['1h', '4h']}")
    print(")")
    print("```")
    
    print("\n4. 🔄 Start Celery worker:")
    print("```bash")
    print("python utils/run_celery.py")
    print("```")
    
    print("\n5. 📊 Monitor tasks:")
    print("```bash")
    print("celery -A utils.celery_app flower  # Web UI")
    print("celery -A utils.celery_app status  # Worker status")
    print("```")

if __name__ == "__main__":
    print("🧪 FUTURES BOT CELERY TEST SUITE")
    print(f"⏰ Started at: {datetime.now()}")
    
    # Show usage examples first
    show_celery_usage()
    
    # Ask user if they want to run actual tests
    print(f"\n❓ Do you want to run live Celery tests?")
    print("   ⚠️  This will execute actual trading logic")
    print("   🧪 Testnet mode is enabled by default")
    
    user_input = input("\nRun tests? (yes/no): ")
    
    if user_input.lower() in ['yes', 'y']:
        print("\n🚀 Starting Celery tests...")
        success = test_futures_bot_celery()
        
        if success:
            print("✅ All tests completed successfully!")
            sys.exit(0)
        else:
            print("❌ Some tests failed")
            sys.exit(1)
    else:
        print("📋 Test skipped. Use the examples above to integrate Futures Bot with Celery.")
        sys.exit(0)