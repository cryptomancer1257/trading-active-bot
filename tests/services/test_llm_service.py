#!/usr/bin/env python3
"""
Test LLM Integration Service
Demo how to use OpenAI, Claude, Gemini for crypto trading analysis with Fibonacci
"""

import asyncio
import os
import json
from services.llm_integration import create_llm_service

async def test_llm_analysis():
    """Test LLM analysis with sample market data"""
    
    print("🚀 TESTING LLM INTEGRATION SERVICE")
    print("=" * 60)
    
    # Sample market data with Fibonacci patterns
    sample_data = {
        "symbol": "BTC/USDT",
        "timeframes": {
            "1h": [
                {"timestamp": 1640995200000, "open": 47000, "high": 48000, "low": 46500, "close": 47500, "volume": 1000},
                {"timestamp": 1640998800000, "open": 47500, "high": 49000, "low": 47000, "close": 48500, "volume": 1200},
                {"timestamp": 1641002400000, "open": 48500, "high": 50000, "low": 48000, "close": 49500, "volume": 1500},
                {"timestamp": 1641006000000, "open": 49500, "high": 51000, "low": 49000, "close": 50500, "volume": 1800},
                {"timestamp": 1641009600000, "open": 50500, "high": 52000, "low": 50000, "close": 51500, "volume": 2000},
                {"timestamp": 1641013200000, "open": 51500, "high": 53000, "low": 51000, "close": 52500, "volume": 2200},
                {"timestamp": 1641016800000, "open": 52500, "high": 54000, "low": 52000, "close": 53000, "volume": 2400}
            ],
            "4h": [
                {"timestamp": 1640995200000, "open": 47000, "high": 50000, "low": 46000, "close": 49000, "volume": 5000},
                {"timestamp": 1641009600000, "open": 49000, "high": 54000, "low": 48500, "close": 53000, "volume": 6000},
                {"timestamp": 1641024000000, "open": 53000, "high": 55000, "low": 52000, "close": 54500, "volume": 7000}
            ],
            "1d": [
                {"timestamp": 1640995200000, "open": 47000, "high": 55000, "low": 45000, "close": 54500, "volume": 25000}
            ]
        }
    }
    
    # Initialize LLM service
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "claude_api_key": os.getenv("CLAUDE_API_KEY"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY")
    }
    
    llm_service = create_llm_service(config)
    
    print(f"📋 Service Status:")
    print(f"   OpenAI: {'✅' if llm_service.openai_client else '❌'}")
    print(f"   Claude: {'✅' if llm_service.claude_client else '❌'}")
    print(f"   Gemini: {'✅' if llm_service.gemini_client else '❌'}")
    
    # Test with available models
    models_to_test = []
    if llm_service.openai_client:
        models_to_test.append("openai")
    if llm_service.claude_client:
        models_to_test.append("claude")
    if llm_service.gemini_client:
        models_to_test.append("gemini")
    
    if not models_to_test:
        print("❌ No LLM models available. Set API keys:")
        print("   export OPENAI_API_KEY='your_key'")
        print("   export CLAUDE_API_KEY='your_key'")
        print("   export GEMINI_API_KEY='your_key'")
        return
    
    print(f"\n🧪 Testing models: {models_to_test}")
    
    for model in models_to_test:
        print(f"\n{'='*60}")
        print(f"🤖 TESTING {model.upper()} MODEL")
        print(f"{'='*60}")
        
        try:
            # Analyze market data
            analysis = await llm_service.analyze_market(
                symbol=sample_data["symbol"],
                timeframes_data=sample_data["timeframes"],
                model=model
            )
            
            if "error" in analysis:
                print(f"❌ {model} Error: {analysis['error']}")
                continue
            
            # Display results
            print(f"✅ {model} Analysis completed!")
            
            if analysis.get("parsed", False):
                print("\n📊 ANALYSIS SUMMARY:")
                
                # Show recommendation
                if "recommendation" in analysis:
                    rec = analysis["recommendation"]
                    print(f"   🎯 Action: {rec.get('action', 'N/A')}")
                    print(f"   💰 Entry: ${rec.get('entry_price', 'N/A')}")
                    print(f"   🎯 Take Profit: ${rec.get('take_profit', 'N/A')}")
                    print(f"   🛡️ Stop Loss: ${rec.get('stop_loss', 'N/A')}")
                    print(f"   📊 Strategy: {rec.get('strategy', 'N/A')}")
                    print(f"   ⚖️ Risk/Reward: {rec.get('risk_reward', 'N/A')}")
                    print(f"   🎯 Confidence: {rec.get('confidence', 'N/A')}%")
                
                # Show Fibonacci analysis for 1D
                if "analysis" in analysis and "1d" in analysis["analysis"]:
                    fib = analysis["analysis"]["1d"].get("fibonacci", {})
                    if fib:
                        print(f"\n📈 FIBONACCI ANALYSIS (1D):")
                        print(f"   📊 Trend: {fib.get('trend', 'N/A')}")
                        print(f"   ⬆️ Swing High: ${fib.get('swing_high', 'N/A')}")
                        print(f"   ⬇️ Swing Low: ${fib.get('swing_low', 'N/A')}")
                        print(f"   🎯 Position: {fib.get('current_position', 'N/A')}")
                        
                        if "key_levels" in fib:
                            levels = fib["key_levels"]
                            print(f"   🛡️ Support: ${levels.get('support', 'N/A')}")
                            print(f"   ⚡ Resistance: ${levels.get('resistance', 'N/A')}")
            else:
                print(f"⚠️ {model} returned unparsed response")
                print(f"Raw response length: {len(analysis.get('raw_response', ''))}")
            
        except Exception as e:
            print(f"❌ {model} Test failed: {e}")
    
    print(f"\n{'='*60}")
    print("✅ LLM INTEGRATION TEST COMPLETED!")
    print(f"{'='*60}")

def demo_usage():
    """Demo how to use LLM service in trading bots"""
    
    print("\n🎯 USAGE EXAMPLE:")
    print("=" * 40)
    
    usage_code = '''
# Import service
from services.llm_integration import create_llm_service

# Initialize with config
config = {
    "openai_api_key": "your_openai_key",
    "claude_api_key": "your_claude_key", 
    "gemini_api_key": "your_gemini_key"
}

llm_service = create_llm_service(config)

# Prepare market data (from exchange)
timeframes_data = {
    "1h": [...],  # OHLCV data
    "4h": [...],
    "1d": [...]
}

# Analyze with LLM (async)
analysis = await llm_service.analyze_market(
    symbol="BTC/USDT",
    timeframes_data=timeframes_data,
    model="openai"  # or "claude", "gemini"
)

# Use results
if analysis.get("parsed"):
    action = analysis["recommendation"]["action"]
    entry_price = analysis["recommendation"]["entry_price"]
    take_profit = analysis["recommendation"]["take_profit"]
    stop_loss = analysis["recommendation"]["stop_loss"]
    
    # Execute trading logic
    if action == "BUY":
        # Place buy order
        pass
    elif action == "SELL":
        # Place sell order
        pass
'''
    
    print(usage_code)

if __name__ == "__main__":
    # Run test
    asyncio.run(test_llm_analysis())
    
    # Show usage demo
    demo_usage()