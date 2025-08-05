#!/usr/bin/env python3
"""
Demo LLM Integration with Real Market Data
Test OpenAI, Claude, Gemini for crypto trading analysis
"""

import asyncio
import os
import json
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.llm_integration import create_llm_service
from services.binance_integration import BinanceIntegration

def get_real_market_data():
    """Get real market data from Binance"""
    print("📊 Fetching real market data from Binance...")
    
    try:
        # Initialize Binance (no API keys needed for public data)
        binance = BinanceIntegration("", "", testnet=False)
        
        # Get smaller data sets to avoid context length issues
        h1_data = binance.get_klines("BTCUSDT", "1h", 24)  # Last 24 hours
        h4_data = binance.get_klines("BTCUSDT", "4h", 12)  # Last 48 hours
        d1_data = binance.get_klines("BTCUSDT", "1d", 7)   # Last 7 days
        
        # Convert to LLM format
        def df_to_ohlcv_list(df):
            ohlcv_list = []
            for idx, row in df.iterrows():
                ohlcv_list.append({
                    'timestamp': int(idx.timestamp() * 1000),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            return ohlcv_list
        
        timeframes_data = {
            "1h": df_to_ohlcv_list(h1_data),
            "4h": df_to_ohlcv_list(h4_data), 
            "1d": df_to_ohlcv_list(d1_data)
        }
        
        # Show current price
        current_price = timeframes_data["1h"][-1]["close"]
        print(f"✅ Current BTC Price: ${current_price:,.2f}")
        print(f"📊 Data points: 1H({len(timeframes_data['1h'])}), 4H({len(timeframes_data['4h'])}), 1D({len(timeframes_data['1d'])})")
        print("💡 Using smaller data sets to avoid LLM context limits")
        
        return timeframes_data
        
    except Exception as e:
        print(f"❌ Error fetching market data: {e}")
        
        # Fallback to sample data
        print("📊 Using sample data instead...")
        return get_sample_data()

def get_sample_data():
    """Get sample market data for testing"""
    base_time = int(datetime.now().timestamp() * 1000)
    
    # Generate realistic BTC price data
    timeframes_data = {
        "1h": [],
        "4h": [],
        "1d": []
    }
    
    # 1H data (last 24 hours)
    price = 50000
    for i in range(24):
        timestamp = base_time - (23 - i) * 3600000  # 1 hour intervals
        price += (hash(f"{timestamp}_{i}") % 1000 - 500) * 0.1  # Random walk
        price = max(45000, min(55000, price))  # Keep in range
        
        timeframes_data["1h"].append({
            'timestamp': timestamp,
            'open': price - 50,
            'high': price + 100,
            'low': price - 100,
            'close': price,
            'volume': 1000 + (i * 10)
        })
    
    # 4H data (last 48 hours = 12 periods)
    for i in range(12):
        timestamp = base_time - (11 - i) * 14400000  # 4 hour intervals
        # Simplified 4H data
        daily_price = 49000 + (i * 100) + (hash(f"4h_{i}") % 1000 - 500)
        timeframes_data["4h"].append({
            'timestamp': timestamp,
            'open': daily_price - 100,
            'high': daily_price + 200,
            'low': daily_price - 200,
            'close': daily_price,
            'volume': 4000 + (i * 100)
        })
    
    # 1D data (last 7 days)
    for i in range(7):
        timestamp = base_time - (6 - i) * 86400000  # 1 day intervals
        # Simplified daily data
        daily_price = 47000 + (i * 200) + (hash(f"daily_{i}") % 2000 - 1000)
        timeframes_data["1d"].append({
            'timestamp': timestamp,
            'open': daily_price - 200,
            'high': daily_price + 500,
            'low': daily_price - 500,
            'close': daily_price,
            'volume': 25000 + (i * 500)
        })
    
    return timeframes_data

async def test_llm_models(timeframes_data):
    """Test all available LLM models"""
    print(f"\n{'='*60}")
    print("🤖 TESTING LLM MODELS FOR CRYPTO ANALYSIS")
    print(f"{'='*60}")
    
    # Validate market data
    if not timeframes_data:
        print("❌ No market data provided")
        return {}
    
    required_timeframes = ["1h", "4h", "1d"]
    missing_timeframes = [tf for tf in required_timeframes if tf not in timeframes_data or not timeframes_data[tf]]
    
    if missing_timeframes:
        print(f"⚠️ Missing timeframes: {missing_timeframes}")
        print("Continuing with available data...")
    
    # Show data summary
    for tf, data in timeframes_data.items():
        if data:
            print(f"📊 {tf.upper()}: {len(data)} candles (${data[-1]['close']:.2f} current)")
    
    # Initialize LLM service
    config = {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "claude_api_key": os.getenv("CLAUDE_API_KEY"),
        "gemini_api_key": os.getenv("GEMINI_API_KEY")
    }
    
    llm_service = create_llm_service(config)
    
    # Debug: Show model configurations
    print(f"🔧 Model configurations:")
    print(f"   OpenAI: {llm_service.openai_model}")
    print(f"   Claude: {llm_service.claude_model}")
    print(f"   Gemini: {llm_service.gemini_model}")
    
    # Check available models
    available_models = []
    if llm_service.openai_client:
        available_models.append("openai")
        print(f"✅ OpenAI client available")
    else:
        print(f"❌ OpenAI client not available")
        
    if llm_service.claude_client:
        available_models.append("claude")
        print(f"✅ Claude client available")
    else:
        print(f"❌ Claude client not available")
        
    if llm_service.gemini_client:
        available_models.append("gemini")
        print(f"✅ Gemini client available")
    else:
        print(f"❌ Gemini client not available")
    
    if not available_models:
        print("❌ No LLM models available!")
        print("💡 Set API keys:")
        print("   export OPENAI_API_KEY='your_key'")
        print("   export CLAUDE_API_KEY='your_key'")
        print("   export GEMINI_API_KEY='your_key'")
        return
    
    print(f"🎯 Available models: {available_models}")
    
    results = {}
    
    for model in available_models:
        print(f"\n{'-'*50}")
        print(f"🔮 ANALYZING WITH {model.upper()}")
        print(f"{'-'*50}")
        
        try:
            start_time = datetime.now()
            
            # Analyze market
            analysis = await llm_service.analyze_market(
                symbol="BTC/USDT",
                timeframes_data=timeframes_data,
                model=model
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if "error" in analysis:
                error_msg = analysis['error']
                print(f"❌ {model} Error: {error_msg}")
                
                # Provide specific guidance for common errors
                if "context length" in error_msg.lower():
                    print(f"💡 Tip: Try reducing market data size further")
                elif "not_found_error" in error_msg.lower() or "404" in error_msg:
                    print(f"💡 Tip: Check if the model name is correct and available")
                elif "api_key" in error_msg.lower():
                    print(f"💡 Tip: Verify your API key is correct and has proper permissions")
                
                results[model] = {"error": error_msg}
                continue
            
            print(f"✅ {model} Analysis completed in {duration:.1f}s")
            
            if analysis.get("parsed", False):
                # Extract recommendation
                rec = analysis.get("recommendation", {})
                
                print(f"\n📊 {model.upper()} RECOMMENDATION:")
                print(f"   🎯 Action: {rec.get('action', 'N/A')}")
                print(f"   💰 Entry: ${rec.get('entry_price', 'N/A')}")
                print(f"   🎯 Take Profit: ${rec.get('take_profit', 'N/A')}")
                print(f"   🛡️ Stop Loss: ${rec.get('stop_loss', 'N/A')}")
                print(f"   📈 Strategy: {rec.get('strategy', 'N/A')}")
                print(f"   ⚖️ Risk/Reward: {rec.get('risk_reward', 'N/A')}")
                print(f"   🎯 Confidence: {rec.get('confidence', 'N/A')}%")
                
                # Extract Fibonacci analysis
                analysis_data = analysis.get("analysis", {})
                if "1d" in analysis_data and "fibonacci" in analysis_data["1d"]:
                    fib = analysis_data["1d"]["fibonacci"]
                    print(f"\n📈 FIBONACCI ANALYSIS:")
                    print(f"   📊 Trend: {fib.get('trend', 'N/A')}")
                    print(f"   ⬆️ Swing High: ${fib.get('swing_high', 'N/A')}")
                    print(f"   ⬇️ Swing Low: ${fib.get('swing_low', 'N/A')}")
                    print(f"   🎯 Position: {fib.get('current_position', 'N/A')}")
                
                results[model] = {
                    "success": True,
                    "duration": duration,
                    "recommendation": rec,
                    "confidence": rec.get('confidence', 0)
                }
            else:
                print(f"⚠️ {model} returned unparsed response")
                print(f"Raw response preview: {analysis.get('raw_response', '')[:200]}...")
                results[model] = {"error": "Unparsed response"}
        
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {model} Test failed: {error_msg}")
            
            # Provide specific guidance for common exceptions
            if "connection" in error_msg.lower():
                print(f"💡 Tip: Check your internet connection")
            elif "timeout" in error_msg.lower():
                print(f"💡 Tip: The API request timed out, try again later")
            elif "rate" in error_msg.lower() and "limit" in error_msg.lower():
                print(f"💡 Tip: You've hit API rate limits, wait a moment and try again")
            
            results[model] = {"error": error_msg}
    
    return results

def compare_results(results):
    """Compare results from different models"""
    print(f"\n{'='*60}")
    print("📊 MODEL COMPARISON")
    print(f"{'='*60}")
    
    if not results:
        print("❌ No results to compare")
        return
    
    successful_models = [model for model, result in results.items() if result.get("success")]
    
    if not successful_models:
        print("❌ No successful analyses to compare")
        return
    
    print(f"✅ Successful models: {successful_models}")
    
    # Compare recommendations
    print(f"\n📊 TRADING RECOMMENDATIONS:")
    print(f"{'Model':<10} {'Action':<8} {'Confidence':<12} {'Duration':<10}")
    print(f"{'-'*45}")
    
    for model in successful_models:
        result = results[model]
        rec = result.get("recommendation", {})
        action = rec.get("action", "N/A")
        confidence = rec.get("confidence", "N/A")
        duration = result.get("duration", "N/A")
        
        # Handle duration formatting safely
        duration_str = f"{duration:.1f}s" if isinstance(duration, (int, float)) else str(duration)
        confidence_str = f"{confidence}%" if confidence != "N/A" else "N/A"
        
        print(f"{model.capitalize():<10} {action:<8} {confidence_str:<12} {duration_str}")
    
    # Consensus analysis - only if we have recommendations
    valid_actions = []
    valid_confidences = []
    
    for model in successful_models:
        result = results[model]
        if "recommendation" in result and result["recommendation"]:
            rec = result["recommendation"]
            action = rec.get("action")
            confidence = rec.get("confidence")
            
            if action and action != "N/A":
                valid_actions.append(action)
            
            if confidence is not None and confidence != "N/A":
                try:
                    valid_confidences.append(float(confidence))
                except (ValueError, TypeError):
                    pass
    
    if valid_actions:
        action_counts = {action: valid_actions.count(action) for action in set(valid_actions)}
        consensus_action = max(action_counts, key=action_counts.get)
        
        print(f"\n🎯 CONSENSUS:")
        print(f"   Most common action: {consensus_action}")
        print(f"   Agreement: {action_counts[consensus_action]}/{len(successful_models)} models")
        
        # Average confidence
        if valid_confidences:
            avg_confidence = sum(valid_confidences) / len(valid_confidences)
            print(f"   Average confidence: {avg_confidence:.1f}%")
        else:
            print(f"   Average confidence: N/A")
    else:
        print(f"\n🎯 CONSENSUS:")
        print(f"   No valid recommendations to analyze")

async def main():
    """Main demo function"""
    print("🚀 LLM INTEGRATION DEMO - REAL CRYPTO ANALYSIS")
    print("=" * 60)
    
    # Get market data
    timeframes_data = get_real_market_data()
    
    if not timeframes_data:
        print("❌ Failed to get market data")
        return
    
    # Test LLM models
    results = await test_llm_models(timeframes_data)
    
    # Compare results
    compare_results(results)
    
    print(f"\n{'='*60}")
    print("✅ DEMO COMPLETED!")
    print("💡 Next steps:")
    print("   1. Set up API keys for more models")
    print("   2. Integrate into trading bot")
    print("   3. Implement real-time analysis")
    print("   4. Add risk management rules")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())