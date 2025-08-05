#!/usr/bin/env python3
"""
Test Bot System với Bot Files thực tế
Hướng dẫn cách test hệ thống bot đã được hỗ trợ
"""

import requests
import json
import pandas as pd
from datetime import datetime

# API Configuration
BASE_URL = "http://localhost:8000"
API_KEY = "test_marketplace_api_key_12345"

def test_bot_api(bot_id: int):
    """Test bot API để lấy thông tin bot"""
    print(f"\n📋 Testing Bot API for Bot ID {bot_id}")
    
    try:
        response = requests.get(f"{BASE_URL}/bots/{bot_id}")
        if response.status_code == 200:
            bot_data = response.json()
            print(f"✅ Bot Name: {bot_data['name']}")
            print(f"   Description: {bot_data['description']}")
            print(f"   Code Path: {bot_data.get('code_path', 'Not set')}")
            print(f"   Bot Type: {bot_data.get('bot_type', 'Not set')}")
            print(f"   Subscribers: {bot_data['total_subscribers']}")
            return bot_data
        else:
            print(f"❌ Failed to get bot info: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_bot_file_loading():
    """Test loading bot files trực tiếp"""
    print(f"\n🔧 Testing Bot File Loading")
    
    try:
        # Test import Advanced ML Bot
        import sys
        import os
        sys.path.insert(0, os.path.join(os.getcwd(), 'bot_files'))
        
        from advanced_ml_bot import AdvancedMLBot
        from simple_sma_bot import SimpleSMABot
        
        # Test ML Bot
        ml_config = {
            'exchange_type': 'BINANCE',
            'trading_pair': 'BTC/USDT',
            'lookback_period': 50,
            'prediction_threshold': 0.6
        }
        api_keys = {'api_key': 'test', 'api_secret': 'test'}
        
        ml_bot = AdvancedMLBot(ml_config, api_keys)
        print(f"✅ ML Bot loaded: {ml_bot.bot_name} v{ml_bot.version}")
        
        # Test SMA Bot
        sma_config = {
            'exchange_type': 'BINANCE', 
            'trading_pair': 'ETH/USDT',
            'ma_short_period': 10,
            'ma_long_period': 20
        }
        
        sma_bot = SimpleSMABot(sma_config, api_keys)
        print(f"✅ SMA Bot loaded: {sma_bot.bot_name} v{sma_bot.version}")
        
        # Test execute_algorithm với sample data
        sample_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106], 
            'low': [99, 100, 101, 102, 103],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000, 1100, 1200, 1300, 1400]
        })
        
        # Test ML Bot execution
        try:
            ml_action = ml_bot.execute_algorithm(sample_data, '1h')
            print(f"✅ ML Bot Action: {ml_action}")
        except Exception as e:
            print(f"⚠️ ML Bot execution (expected with minimal data): {e}")
        
        # Test SMA Bot execution  
        try:
            sma_action = sma_bot.execute_algorithm(sample_data, '1h')
            print(f"✅ SMA Bot Action: {sma_action}")
        except Exception as e:
            print(f"⚠️ SMA Bot execution (expected with minimal data): {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Bot file loading error: {e}")
        return False

def test_bot_test_api():
    """Test bot test API nếu có"""
    print(f"\n🧪 Testing Bot Test API")
    
    # Test với Bot ID 1 (SMA Bot)
    test_data = {
        "timeframe": "1h",
        "test_config": {
            "ma_short_period": 10,
            "ma_long_period": 20
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bots/1/test",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Bot test successful: {result}")
        else:
            print(f"⚠️ Bot test API response: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Bot test API error: {e}")

def test_subscription_with_bot():
    """Test subscription với bot có file thực tế"""
    print(f"\n🔗 Testing Subscription with Real Bot Files")
    
    # Lấy danh sách registrations hiện tại
    try:
        response = requests.get(
            f"{BASE_URL}/bots/registrations/rdmx6-jaaaa-aaaah-qcaiq-cai",
            headers={"X-API-Key": API_KEY}
        )
        
        if response.status_code == 200:
            registrations = response.json()
            print(f"✅ Found {len(registrations)} active registrations")
            
            for reg in registrations:
                print(f"   - Registration {reg['id']}: {reg['instance_name']}")
                print(f"     Bot ID: {reg['bot_id']}, Status: {reg['status']}")
        else:
            print(f"⚠️ Could not get registrations: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Subscription test error: {e}")

def show_system_architecture():
    """Hiển thị kiến trúc hệ thống bot"""
    print(f"\n🏗️ BOT SYSTEM ARCHITECTURE")
    print("=" * 60)
    print("""
�� Project Structure:
├── bots/bot_sdk/
│   ├── CustomBot.py      # Base class cho tất cả bots
│   └── Action.py         # Trading action model
├── bot_files/            # Bot implementations
│   ├── advanced_ml_bot.py    # ML Trading Bot
│   └── simple_sma_bot.py     # SMA Trading Bot
├── services/
│   └── exchange_factory.py  # Exchange integrations
└── api/endpoints/
    └── bots.py          # Bot management APIs

🔄 Bot Execution Flow:
1. User registers bot via API → Database subscription
2. System loads bot file from code_path
3. Bot extends CustomBot class
4. Bot implements execute_algorithm() method:
   ├── crawl_data()      # Get market data
   ├── preprocess_data() # Calculate indicators  
   ├── run_algorithm()   # Generate signals
   └── make_prediction() # Return Action
5. System executes trading action

🛠️ How to Create New Bot:
1. Extend CustomBot class
2. Implement execute_algorithm() method
3. Save file in bot_files/ directory
4. Update database code_path
5. Test via bot APIs

📊 Supported Bot Types:
- TECHNICAL: Technical analysis bots
- ML: Machine learning bots  
- DL: Deep learning bots
- LLM: Large language model bots
""")

def main():
    """Main test function"""
    print("🚀 TESTING BOT SYSTEM WITH REAL FILES")
    print("=" * 60)
    
    # Show system architecture
    show_system_architecture()
    
    # Test bot APIs
    test_bot_api(1)  # SMA Bot
    test_bot_api(3)  # ML Bot
    
    # Test bot file loading
    test_bot_file_loading()
    
    # Test bot test API
    test_bot_test_api()
    
    # Test subscriptions
    test_subscription_with_bot()
    
    print(f"\n✅ BOT SYSTEM TEST COMPLETED!")
    print("=" * 60)
    print("""
🎯 Next Steps:
1. Implement real exchange connections
2. Add more sophisticated ML models  
3. Create bot performance monitoring
4. Add backtesting capabilities
5. Implement risk management systems
""")

if __name__ == "__main__":
    main()
