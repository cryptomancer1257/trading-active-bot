#!/usr/bin/env python3
"""
Direct LLM Testing Script
Test LLM integration service directly with sample market data
"""

import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm_integration import create_llm_service

async def test_direct_llm_call():
    """Test direct LLM call with sample market data"""
    
    print("🚀 Testing Direct LLM Call...")
    
    # Sample market data for BTC/USDT
    sample_data = {
        "1h": [
            {"timestamp": 1704067200000, "open": 43500, "high": 44200, "low": 43200, "close": 44000, "volume": 1200},
            {"timestamp": 1704070800000, "open": 44000, "high": 44800, "low": 43800, "close": 44500, "volume": 1350},
            {"timestamp": 1704074400000, "open": 44500, "high": 45200, "low": 44300, "close": 45000, "volume": 1500},
            {"timestamp": 1704078000000, "open": 45000, "high": 45800, "low": 44800, "close": 45500, "volume": 1800},
            {"timestamp": 1704081600000, "open": 45500, "high": 46200, "low": 45200, "close": 46000, "volume": 2000}
        ],
        "4h": [
            {"timestamp": 1704067200000, "open": 43500, "high": 45000, "low": 43000, "close": 44800, "volume": 5200},
            {"timestamp": 1704081600000, "open": 44800, "high": 46500, "low": 44500, "close": 46000, "volume": 6800}
        ],
        "1d": [
            {"timestamp": 1704067200000, "open": 43500, "high": 46500, "low": 42800, "close": 46000, "volume": 28500}
        ]
    }
    
    # Initialize LLM service
    print("📡 Initializing LLM Service...")
    service = create_llm_service()
    
    print("🔍 Available Models:")
    print(f"   OpenAI: {'✅' if service.openai_client else '❌'}")
    print(f"   Claude: {'✅' if service.claude_client else '❌'}")
    print(f"   Gemini: {'✅' if service.gemini_client else '❌'}")
    
    # Test with available models
    models_to_test = []
    if service.openai_client:
        models_to_test.append("openai")
    if service.claude_client:
        models_to_test.append("claude")
    if service.gemini_client:
        models_to_test.append("gemini")
    
    if not models_to_test:
        print("❌ No LLM models available! Please check your API keys.")
        return
    
    # Test each available model
    for model in models_to_test:
        print(f"\n🧠 Testing {model.upper()} Model...")
        print("=" * 50)
        
        try:
            # Call LLM analysis
            result = await service.analyze_market(
                symbol="BTC/USDT",
                timeframes_data=sample_data,
                model=model
            )
            
            if "error" in result:
                print(f"❌ Error with {model}: {result['error']}")
                continue
            
            print(f"✅ {model.upper()} Analysis Successful!")
            
            # Display results
            if result.get("parsed", False):
                print("\n📊 Parsed Analysis:")
                if "analysis" in result:
                    print("   Technical Analysis: ✅")
                if "recommendation" in result:
                    recommendation = result["recommendation"]
                    print(f"   Action: {recommendation.get('action', 'N/A')}")
                    print(f"   Entry Price: {recommendation.get('entry_price', 'N/A')}")
                    print(f"   Take Profit: {recommendation.get('take_profit', 'N/A')}")
                    print(f"   Stop Loss: {recommendation.get('stop_loss', 'N/A')}")
                    print(f"   Confidence: {recommendation.get('confidence', 'N/A')}%")
            else:
                print("\n📝 Raw Response:")
                raw_response = result.get("raw_response", "No response")
                # Truncate if too long
                if len(raw_response) > 500:
                    print(raw_response[:500] + "... [truncated]")
                else:
                    print(raw_response)
            
            print(f"\n🔧 Metadata:")
            metadata = result.get("metadata", {})
            print(f"   Model: {metadata.get('model', 'N/A')}")
            print(f"   Timestamp: {metadata.get('timestamp', 'N/A')}")
            print(f"   Timeframes: {metadata.get('timeframes_analyzed', [])}")
            
        except Exception as e:
            print(f"❌ Exception with {model}: {str(e)}")
    
    print("\n🎯 Direct LLM Test Completed!")

def test_sync_version():
    """Synchronous wrapper for testing"""
    try:
        # Run the async test
        asyncio.run(test_direct_llm_call())
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    print("🤖 Direct LLM Testing Script")
    print("=" * 40)
    test_sync_version()