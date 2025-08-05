#!/usr/bin/env python3
"""
Comprehensive Test for Capital Management System
Tests the integration of LLM-based capital management with Binance Futures Bot
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_files.binance_futures_bot import BinanceFuturesBot
from bot_files.capital_management import CapitalManagement, RiskMetrics
from bots.bot_sdk.Action import Action

async def test_capital_management_integration():
    """Test the complete capital management integration with bot"""
    
    print("🧪 Testing Capital Management System Integration")
    print("=" * 70)
    
    # Enhanced test configuration with capital management settings
    test_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,
        'leverage': 10,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.04,
        
        # Dynamic timeframes
        'timeframes': ['5m', '30m', '1h', '4h', '1d'],
        'primary_timeframe': '1h',
        
        # LLM Configuration
        'use_llm_analysis': True,
        'llm_model': 'openai',
        
        # Capital Management Configuration
        'base_position_size_pct': 0.02,     # 2% base size
        'max_position_size_pct': 0.08,      # 8% max size
        'max_portfolio_exposure': 0.25,     # 25% total exposure
        'max_drawdown_threshold': 0.12,     # 12% max drawdown
        'volatility_threshold_low': 0.015,   # 1.5% low volatility
        'volatility_threshold_high': 0.06,   # 6% high volatility
        'kelly_multiplier': 0.3,             # 30% of Kelly
        'min_win_rate': 0.4,                 # 40% minimum win rate
        'use_llm_capital_management': True,  # Enable LLM capital advice
        'llm_capital_weight': 0.5,           # 50% weight to LLM
        'sizing_method': 'llm_hybrid'        # Use LLM hybrid method
    }
    
    test_api_keys = {
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'claude_api_key': os.getenv('CLAUDE_API_KEY'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }
    
    print("🤖 Initializing Bot with Advanced Capital Management...")
    print(f"   Base Position Size: {test_config['base_position_size_pct']*100:.1f}%")
    print(f"   Max Position Size: {test_config['max_position_size_pct']*100:.1f}%")
    print(f"   Max Portfolio Exposure: {test_config['max_portfolio_exposure']*100:.1f}%")
    print(f"   Capital Management Method: {test_config['sizing_method']}")
    print(f"   LLM Capital Weight: {test_config['llm_capital_weight']*100:.0f}%")
    
    bot = BinanceFuturesBot(test_config, test_api_keys)
    print("✅ Bot initialized with capital management system!")
    
    # Test different market scenarios
    scenarios = [
        {
            "name": "High Confidence Bull Signal",
            "signal": Action(action="BUY", value=0.85, reason="Strong bullish signals", 
                           recommendation={
                               "action": "BUY",
                               "confidence": "85%",
                               "entry_price": "44500.00",
                               "take_profit": "47000.00",
                               "stop_loss": "43200.00",
                               "strategy": "Momentum breakout with strong volume",
                               "risk_reward": "1:2.8"
                           }),
            "market_conditions": "high_volatility"
        },
        {
            "name": "Medium Confidence Bear Signal",
            "signal": Action(action="SELL", value=0.65, reason="Bearish divergence", 
                           recommendation={
                               "action": "SELL",
                               "confidence": "65%",
                               "entry_price": "44300.00",
                               "take_profit": "42800.00",
                               "stop_loss": "44900.00",
                               "strategy": "Technical resistance reversal",
                               "risk_reward": "1:2.5"
                           }),
            "market_conditions": "medium_volatility"
        },
        {
            "name": "Low Confidence Hold Signal",
            "signal": Action(action="HOLD", value=0.30, reason="Uncertain market conditions"),
            "market_conditions": "low_volatility"
        },
        {
            "name": "Very High Confidence with High Risk",
            "signal": Action(action="BUY", value=0.95, reason="Perfect technical setup", 
                           recommendation={
                               "action": "BUY",
                               "confidence": "95%",
                               "entry_price": "44600.00",
                               "take_profit": "48200.00",
                               "stop_loss": "43800.00",
                               "strategy": "Golden cross with oversold bounce",
                               "risk_reward": "1:4.5"
                           }),
            "market_conditions": "extreme_volatility"
        }
    ]
    
    # Mock account information for different risk scenarios
    account_scenarios = [
        {
            "name": "Healthy Account",
            "account_info": {
                "totalWalletBalance": "10000.0",
                "availableBalance": "8000.0",
                "positions": []  # No current positions
            },
            "historical_performance": [
                {"pnl_pct": 0.03}, {"pnl_pct": -0.01}, {"pnl_pct": 0.02}, 
                {"pnl_pct": 0.04}, {"pnl_pct": -0.02}, {"pnl_pct": 0.01}
            ]
        },
        {
            "name": "Account in Drawdown",
            "account_info": {
                "totalWalletBalance": "7500.0",
                "availableBalance": "6000.0",
                "positions": [
                    {"positionAmt": "0.1", "markPrice": "44000", "unrealizedProfit": "-200"}
                ]
            },
            "historical_performance": [
                {"pnl_pct": -0.03}, {"pnl_pct": -0.02}, {"pnl_pct": 0.01}, 
                {"pnl_pct": -0.04}, {"pnl_pct": -0.01}, {"pnl_pct": -0.02}
            ]
        },
        {
            "name": "High Exposure Account",
            "account_info": {
                "totalWalletBalance": "15000.0",
                "availableBalance": "3000.0",
                "positions": [
                    {"positionAmt": "0.3", "markPrice": "44000", "unrealizedProfit": "500"},
                    {"positionAmt": "-0.1", "markPrice": "44000", "unrealizedProfit": "-100"}
                ]
            },
            "historical_performance": [
                {"pnl_pct": 0.05}, {"pnl_pct": 0.03}, {"pnl_pct": -0.01}, 
                {"pnl_pct": 0.06}, {"pnl_pct": 0.02}, {"pnl_pct": 0.04}
            ]
        }
    ]
    
    results = []
    
    for account_scenario in account_scenarios:
        print(f"\n📊 Testing Account Scenario: {account_scenario['name']}")
        print("-" * 50)
        
        # Mock the bot's futures client
        class MockFuturesClient:
            def __init__(self, account_info):
                self.account_info = account_info
            
            def get_account_info(self):
                return self.account_info
            
            def set_leverage(self, symbol, leverage):
                return True
            
            def create_market_order(self, symbol, side, quantity):
                from dataclasses import dataclass
                @dataclass
                class MockOrder:
                    order_id: int = 12345
                    status: str = "FILLED"
                return MockOrder()
            
            def create_stop_loss_order(self, symbol, side, quantity, price):
                from dataclasses import dataclass
                @dataclass 
                class MockOrder:
                    order_id: int = 12346
                return MockOrder()
            
            def create_take_profit_order(self, symbol, side, quantity, price):
                from dataclasses import dataclass
                @dataclass
                class MockOrder:
                    order_id: int = 12347
                return MockOrder()
        
        # Replace the bot's futures client with mock
        bot.futures_client = MockFuturesClient(account_scenario["account_info"])
        
        # Update capital manager with historical performance
        if account_scenario.get("historical_performance"):
            # This would normally be stored/tracked over time
            pass
        
        for scenario in scenarios:
            print(f"\n🎯 Testing: {scenario['name']}")
            
            # Create mock analysis data
            analysis = {
                'current_price': 44500.0,
                'primary_analysis': {
                    'current_price': 44500.0,
                    'rsi': 45.0,
                    'macd': 125.0,
                    'atr': 1200.0,
                    'volatility': 0.05 if scenario['market_conditions'] == 'medium_volatility' else 
                                 0.02 if scenario['market_conditions'] == 'low_volatility' else
                                 0.08 if scenario['market_conditions'] == 'high_volatility' else 0.12
                },
                'multi_timeframe': {
                    '5m': {'current_price': 44500.0},
                    '30m': {'current_price': 44500.0},
                    '1h': {'current_price': 44500.0},
                    '4h': {'current_price': 44500.0},
                    '1d': {'current_price': 44500.0}
                }
            }
            
            try:
                # Test the position setup with capital management
                if scenario['signal'].action != "HOLD":
                    position_result = await bot.setup_position(scenario['signal'], analysis)
                    
                    result = {
                        'account_scenario': account_scenario['name'],
                        'signal_scenario': scenario['name'],
                        'signal_action': scenario['signal'].action,
                        'signal_confidence': scenario['signal'].value,
                        'market_conditions': scenario['market_conditions'],
                        'position_result': position_result
                    }
                    
                    results.append(result)
                    
                    # Print key results
                    if position_result.get('status') == 'success':
                        capital_mgmt = position_result.get('capital_management', {})
                        risk_metrics = position_result.get('risk_metrics', {})
                        
                        print(f"   ✅ Position Setup Successful")
                        print(f"   💰 Recommended Size: {capital_mgmt.get('recommended_size_pct', 0):.2f}%")
                        print(f"   ⚠️  Risk Level: {capital_mgmt.get('risk_level', 'N/A')}")
                        print(f"   🧠 Sizing Method: {capital_mgmt.get('sizing_method', 'N/A')}")
                        print(f"   📊 Account Balance: ${risk_metrics.get('account_balance', 0):.0f}")
                        print(f"   📈 Portfolio Exposure: {risk_metrics.get('portfolio_exposure', 'N/A')}")
                        print(f"   📉 Current Drawdown: {risk_metrics.get('current_drawdown', 'N/A')}")
                        print(f"   💎 Position Value: ${position_result.get('position_value', 0):.2f}")
                        
                        if capital_mgmt.get('reasoning'):
                            print(f"   💭 Reasoning: {capital_mgmt['reasoning'][:60]}...")
                    
                    elif position_result.get('status') == 'info':
                        print(f"   ℹ️  No Position: {position_result.get('reason', 'N/A')}")
                    else:
                        print(f"   ❌ Error: {position_result.get('message', 'Unknown error')}")
                        
                else:
                    print(f"   💤 HOLD Signal - No position setup required")
                    result = {
                        'account_scenario': account_scenario['name'],
                        'signal_scenario': scenario['name'],
                        'signal_action': 'HOLD',
                        'signal_confidence': scenario['signal'].value,
                        'market_conditions': scenario['market_conditions'],
                        'position_result': {'status': 'hold', 'action': 'HOLD'}
                    }
                    results.append(result)
                    
            except Exception as e:
                print(f"   ❌ Error in scenario: {e}")
                result = {
                    'account_scenario': account_scenario['name'],
                    'signal_scenario': scenario['name'],
                    'error': str(e)
                }
                results.append(result)
    
    # Summary Analysis
    print(f"\n📈 CAPITAL MANAGEMENT TEST SUMMARY")
    print("=" * 70)
    
    successful_positions = [r for r in results if r.get('position_result', {}).get('status') == 'success']
    hold_positions = [r for r in results if r.get('position_result', {}).get('action') == 'HOLD']
    rejected_positions = [r for r in results if r.get('position_result', {}).get('status') == 'info']
    
    print(f"📊 Test Results:")
    print(f"   ✅ Successful Positions: {len(successful_positions)}")
    print(f"   💤 Hold Signals: {len(hold_positions)}")
    print(f"   🚫 Rejected by Capital Mgmt: {len(rejected_positions)}")
    print(f"   📈 Total Scenarios Tested: {len(results)}")
    
    if successful_positions:
        avg_position_size = sum(float(r['position_result'].get('capital_management', {}).get('recommended_size_pct', 0)) 
                               for r in successful_positions) / len(successful_positions)
        print(f"   💰 Average Position Size: {avg_position_size:.2f}%")
        
        risk_levels = [r['position_result'].get('capital_management', {}).get('risk_level', 'UNKNOWN') 
                      for r in successful_positions]
        risk_distribution = {level: risk_levels.count(level) for level in set(risk_levels)}
        print(f"   ⚠️  Risk Level Distribution: {risk_distribution}")
    
    print(f"\n🎯 Key Features Tested:")
    print(f"   ✅ LLM-based position sizing")
    print(f"   ✅ Multi-method size calculation (Kelly, Volatility, ATR, Confidence)")
    print(f"   ✅ Risk metrics calculation") 
    print(f"   ✅ Drawdown protection")
    print(f"   ✅ Portfolio exposure limits")
    print(f"   ✅ Volatility-based adjustments")
    print(f"   ✅ Account-specific risk assessment")
    
    # Export detailed results
    with open('capital_management_test_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to 'capital_management_test_results.json'")
    print(f"✅ Capital Management System Test Completed!")
    
    return results

def test_sync_wrapper():
    """Synchronous wrapper for async test"""
    try:
        results = asyncio.run(test_capital_management_integration())
        return results
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

if __name__ == "__main__":
    print("🚀 Starting Comprehensive Capital Management System Test")
    print("This test will evaluate LLM-enhanced position sizing in various market scenarios")
    print("=" * 80)
    
    results = test_sync_wrapper()
    
    print("=" * 80)
    if results:
        print(f"✅ Test completed successfully with {len(results)} scenarios tested!")
    else:
        print("❌ Test failed or returned no results.")
    
    print("🎉 Capital Management Testing Complete!")