#!/usr/bin/env python3
"""
Test Full LLM Recommendation Usage
Verify that ALL LLM recommendation fields are used correctly
"""

import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_files.binance_futures_bot import BinanceFuturesBot
from bots.bot_sdk.Action import Action

async def test_full_llm_recommendation_usage():
    """Test if bot uses ALL LLM recommendation fields correctly"""
    
    print("🔍 Testing Full LLM Recommendation Usage...")
    
    # Test configuration with LLM enabled
    test_config = {
        'trading_pair': 'BTCUSDT',
        'testnet': True,
        'leverage': 10,
        'stop_loss_pct': 0.02,  # These should be IGNORED when LLM provides values
        'take_profit_pct': 0.04,  # These should be IGNORED when LLM provides values
        'position_size_pct': 0.1,
        'timeframes': ['1h', '4h', '1d'],
        'primary_timeframe': '1h',
        'use_llm_analysis': True,  # Enable LLM
        'llm_model': 'openai'
    }
    
    test_api_keys = {
        'api_key': 'test_key',
        'api_secret': 'test_secret',
        'openai_api_key': os.getenv('OPENAI_API_KEY'),
        'claude_api_key': os.getenv('CLAUDE_API_KEY'),
        'gemini_api_key': os.getenv('GEMINI_API_KEY')
    }
    
    bot = BinanceFuturesBot(test_config, test_api_keys)
    
    # Mock LLM Service Response
    class MockLLMService:
        async def analyze_market(self, symbol, timeframes_data, model):
            # Return a complete LLM recommendation
            return {
                "parsed": True,
                "recommendation": {
                    "action": "BUY",  # This should be used as Action.action
                    "confidence": "85%",  # This should be used as Action.value
                    "entry_price": "44500.00",  # This should be used for entry
                    "take_profit": "46700.00",  # This should be used for TP
                    "stop_loss": "43200.00",  # This should be used for SL
                    "strategy": "LLM Fibonacci retracement with oversold RSI reversal",  # This should be used
                    "risk_reward": "1:2.5",  # This should be used
                    "reasoning": "Multi-timeframe analysis shows strong support at current levels with bullish divergence on RSI"  # This should be used
                }
            }
    
    # Replace LLM service with mock
    bot.llm_service = MockLLMService()
    
    print("✅ Bot initialized with mocked LLM service")
    
    # Create sample timeframes data
    sample_timeframes_data = {
        "1h": [{"timestamp": 1640995200000, "open": 44000, "high": 45000, "low": 43500, "close": 44800, "volume": 1000}],
        "4h": [{"timestamp": 1640995200000, "open": 44000, "high": 45500, "low": 43000, "close": 44800, "volume": 5000}],
        "1d": [{"timestamp": 1640995200000, "open": 44000, "high": 46000, "low": 42000, "close": 44800, "volume": 25000}]
    }
    
    # Test LLM signal generation
    print("\n📊 Testing LLM Signal Generation...")
    action = await bot._generate_llm_signal_from_multi_timeframes(sample_timeframes_data)
    
    print(f"🔄 LLM Response Processing:")
    print(f"Action: {action.action} (should be 'BUY' from LLM)")
    print(f"Confidence: {action.value:.2f} (should be 0.85 from LLM)")
    print(f"Reason: {action.reason}")
    
    if action.recommendation:
        rec = action.recommendation
        print(f"\n📋 Recommendation Details:")
        print(f"Action: {rec['action']} (should match Action.action)")
        print(f"Confidence: {rec['confidence']} (should be '85.0%')")
        print(f"Entry Price: {rec['entry_price']} (should be '44500.00')")
        print(f"Take Profit: {rec['take_profit']} (should be '46700.00')")
        print(f"Stop Loss: {rec['stop_loss']} (should be '43200.00')")
        print(f"Strategy: {rec['strategy']}")
        print(f"Risk/Reward: {rec['risk_reward']} (should be '1:2.5')")
        print(f"Reasoning: {rec['reasoning'][:50]}...")
    
    # Test execute_trade with LLM recommendation
    print(f"\n📊 Testing Trade Execution with LLM Recommendation...")
    
    analysis = {
        'current_price': 44600.0,  # Different from LLM entry price
        'primary_analysis': {'current_price': 44600.0},
        'primary_timeframe': '1h',
        'multi_timeframe': {'1h': {}, '4h': {}, '1d': {}}
    }
    
    trade_result = bot.execute_trade(action, analysis)
    
    print(f"🔄 Trade Execution Results:")
    print(f"Entry Price Used: ${trade_result.get('entry_price', 'N/A')} (should be 44500.0 from LLM, NOT 44600.0 current price)")
    print(f"Take Profit: ${trade_result.get('take_profit_price', 'N/A')} (should be 46700.0 from LLM)")
    print(f"Stop Loss: ${trade_result.get('stop_loss_price', 'N/A')} (should be 43200.0 from LLM)")
    print(f"Strategy: {trade_result.get('strategy', 'N/A')} (should be LLM strategy)")
    print(f"Risk/Reward: {trade_result.get('risk_reward', 'N/A')} (should be '1:2.5' from LLM)")
    
    # Verification
    print(f"\n✅ VERIFICATION:")
    
    # Check Action fields
    llm_action_correct = action.action == "BUY"
    llm_confidence_correct = abs(action.value - 0.85) < 0.01
    
    print(f"Action from LLM: {'✅' if llm_action_correct else '❌'} (Expected: BUY, Got: {action.action})")
    print(f"Confidence from LLM: {'✅' if llm_confidence_correct else '❌'} (Expected: 0.85, Got: {action.value:.2f})")
    
    # Check trade execution uses LLM prices
    entry_from_llm = trade_result.get('entry_price') == 44500.0
    tp_from_llm = trade_result.get('take_profit_price') == 46700.0
    sl_from_llm = trade_result.get('stop_loss_price') == 43200.0
    
    print(f"Entry Price from LLM: {'✅' if entry_from_llm else '❌'} (Expected: 44500.0, Got: {trade_result.get('entry_price')})")
    print(f"Take Profit from LLM: {'✅' if tp_from_llm else '❌'} (Expected: 46700.0, Got: {trade_result.get('take_profit_price')})")
    print(f"Stop Loss from LLM: {'✅' if sl_from_llm else '❌'} (Expected: 43200.0, Got: {trade_result.get('stop_loss_price')})")
    
    # Check strategy and risk/reward
    strategy_from_llm = "LLM" in trade_result.get('strategy', '')
    rr_from_llm = trade_result.get('risk_reward') == '1:2.5'
    
    print(f"Strategy from LLM: {'✅' if strategy_from_llm else '❌'}")
    print(f"Risk/Reward from LLM: {'✅' if rr_from_llm else '❌'} (Expected: 1:2.5, Got: {trade_result.get('risk_reward')})")
    
    # Summary
    all_correct = all([
        llm_action_correct, llm_confidence_correct, 
        entry_from_llm, tp_from_llm, sl_from_llm,
        strategy_from_llm, rr_from_llm
    ])
    
    print(f"\n🎯 FINAL RESULT:")
    if all_correct:
        print("✅ ALL LLM recommendation fields are used correctly!")
        print("✅ No hardcoded values override LLM recommendations!")
        print("✅ Bot fully respects LLM analysis!")
    else:
        print("❌ Some LLM recommendations are not being used correctly!")
        print("❌ Need to fix LLM recommendation usage!")
    
    return all_correct

def test_sync_wrapper():
    """Synchronous wrapper"""
    try:
        result = asyncio.run(test_full_llm_recommendation_usage())
        return result
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Full LLM Recommendation Usage")
    print("=" * 60)
    success = test_sync_wrapper()
    print("=" * 60)
    print(f"Test {'PASSED ✅' if success else 'FAILED ❌'}")