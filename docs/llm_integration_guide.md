# LLM Integration Service Guide

## Overview

The LLM Integration Service enables advanced AI-powered crypto trading analysis using OpenAI, Claude, and Gemini models. The service provides comprehensive technical analysis including Fibonacci retracement levels, multiple timeframe analysis, and strategic trading recommendations.

## Features

### 🤖 Multi-Model Support
- **OpenAI GPT-4**: Advanced reasoning and analysis
- **Claude Sonnet**: Strong analytical capabilities  
- **Gemini Pro**: Google's latest AI model

### 📊 Technical Analysis
- **Moving Averages**: MA20, MA50
- **Bollinger Bands**: Position and signals
- **RSI(14)**: Momentum indicator
- **MACD (12,26,9)**: Trend analysis
- **Stochastic RSI**: Overbought/oversold levels
- **Volume Analysis**: Rising/falling trends

### 📈 Fibonacci Analysis
- **Automatic Calculation**: LLM calculates retracement levels from OHLCV data
- **Swing Detection**: Identifies swing highs and lows
- **Golden Ratio**: 61.8% level analysis
- **Support/Resistance**: Key Fibonacci levels
- **Extension Levels**: 127.2%, 161.8%, 200%, 261.8%

### 🎯 Trading Recommendations
- **Action**: BUY/SELL/HOLD/CLOSE
- **Entry Price**: Fibonacci-based entry points
- **Take Profit**: Using Fibonacci levels
- **Stop Loss**: Risk management with Fibonacci
- **Strategy**: Detailed trading strategy
- **Risk/Reward**: Calculated ratios
- **Confidence Score**: 0-100% confidence

## Installation

### 1. Install Dependencies

```bash
pip install openai>=1.0.0 anthropic>=0.7.0 google-generativeai>=0.3.0
```

### 2. Set API Keys

```bash
export OPENAI_API_KEY="your_openai_key"
export CLAUDE_API_KEY="your_claude_key"
export GEMINI_API_KEY="your_gemini_key"
```

### 3. Import Service

```python
from services.llm_integration import create_llm_service
```

## Usage Examples

### Basic Usage

```python
import asyncio
from services.llm_integration import create_llm_service

# Initialize service
config = {
    "openai_api_key": "your_openai_key",
    "claude_api_key": "your_claude_key",
    "gemini_api_key": "your_gemini_key"
}

llm_service = create_llm_service(config)

# Prepare market data
timeframes_data = {
    "1h": [
        {"timestamp": 1640995200000, "open": 47000, "high": 48000, "low": 46500, "close": 47500, "volume": 1000},
        # ... more OHLCV data
    ],
    "4h": [
        {"timestamp": 1640995200000, "open": 47000, "high": 50000, "low": 46000, "close": 49000, "volume": 5000},
        # ... more OHLCV data
    ],
    "1d": [
        {"timestamp": 1640995200000, "open": 47000, "high": 52000, "low": 45000, "close": 51500, "volume": 25000}
    ]
}

# Analyze with LLM
analysis = await llm_service.analyze_market(
    symbol="BTC/USDT",
    timeframes_data=timeframes_data,
    model="openai"  # or "claude", "gemini"
)

# Process results
if analysis.get("parsed"):
    recommendation = analysis["recommendation"]
    print(f"Action: {recommendation['action']}")
    print(f"Entry: ${recommendation['entry_price']}")
    print(f"Take Profit: ${recommendation['take_profit']}")
    print(f"Stop Loss: ${recommendation['stop_loss']}")
    print(f"Confidence: {recommendation['confidence']}%")
```

### Using in Trading Bot

```python
from bots.bot_sdk.CustomBot import CustomBot
from bots.bot_sdk.Action import Action
from services.llm_integration import create_llm_service

class MyLLMBot(CustomBot):
    def __init__(self, config, api_keys):
        super().__init__(config, api_keys)
        
        # Initialize LLM service
        self.llm_service = create_llm_service({
            'openai_api_key': api_keys.get('openai_api_key'),
            'claude_api_key': api_keys.get('claude_api_key'),
            'gemini_api_key': api_keys.get('gemini_api_key')
        })
    
    def execute_algorithm(self, data, timeframe, subscription_config=None):
        # Prepare timeframes data
        timeframes_data = self.prepare_timeframes_data(data)
        
        # Get LLM analysis
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            analysis = loop.run_until_complete(
                self.llm_service.analyze_market(
                    symbol=self.trading_pair,
                    timeframes_data=timeframes_data,
                    model="openai"
                )
            )
        finally:
            loop.close()
        
        # Convert to action
        if analysis.get("parsed"):
            rec = analysis["recommendation"]
            action = rec["action"]
            confidence = float(rec["confidence"])
            
            if confidence >= 70:  # Minimum confidence threshold
                if action == "BUY":
                    return Action.buy("PERCENTAGE", 10.0, f"LLM {action} signal")
                elif action == "SELL":
                    return Action.sell("PERCENTAGE", 50.0, f"LLM {action} signal")
        
        return Action.hold("Low confidence or no signal")
```

## Response Format

### Analysis Structure

```json
{
  "analysis": {
    "1h": {
      "ma20": "49500 - above current price",
      "ma50": "48000 - below current price",
      "bollinger_bands": "Price near upper band - overbought signal",
      "rsi": "72.5 - overbought territory",
      "macd": "Bullish crossover - upward momentum",
      "stoch_rsi": "85.2 - overbought",
      "volume_trend": "Rising - confirming upward move",
      "fibonacci": {
        "trend": "uptrend",
        "swing_high": 52000,
        "swing_low": 45000,
        "current_position": "above_618",
        "key_levels": {
          "support": 48650,
          "resistance": 52000
        }
      }
    },
    "4h": { "similar structure" },
    "1d": { "similar structure" }
  },
  "recommendation": {
    "action": "BUY",
    "entry_price": 50500,
    "take_profit": 53500,
    "stop_loss": 48500,
    "strategy": "Fibonacci retracement breakout with multi-timeframe confirmation",
    "risk_reward": "1:2.5",
    "confidence": "85",
    "reasoning": "Strong bullish signals across timeframes with Fibonacci support"
  },
  "metadata": {
    "symbol": "BTC/USDT",
    "model": "openai",
    "timestamp": "2024-01-31T10:30:00Z",
    "timeframes_analyzed": ["1h", "4h", "1d"]
  }
}
```

## Model Comparison

| Feature | OpenAI GPT-4 | Claude Sonnet | Gemini Pro |
|---------|--------------|---------------|------------|
| **Analysis Depth** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Fibonacci Accuracy** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Speed** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Cost** | $$$ | $$$ | $$ |
| **JSON Consistency** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

## Configuration Options

```python
config = {
    # API Keys
    "openai_api_key": "your_key",
    "claude_api_key": "your_key", 
    "gemini_api_key": "your_key",
    
    # Model Settings
    "openai_model": "gpt-4",  # or "gpt-3.5-turbo"
    "claude_model": "claude-3-sonnet-20240229",
    "gemini_model": "gemini-1.5-pro",
    
    # Analysis Settings
    "temperature": 0.2,  # Lower = more consistent
    "max_tokens": 4000,  # Response length
    "timeout": 30        # Request timeout seconds
}
```

## Error Handling

```python
analysis = await llm_service.analyze_market(symbol, data, model)

if "error" in analysis:
    print(f"Analysis failed: {analysis['error']}")
elif not analysis.get("parsed"):
    print("Failed to parse LLM response")
    print(f"Raw response: {analysis.get('raw_response', '')[:200]}...")
else:
    # Process successful analysis
    recommendation = analysis["recommendation"]
```

## Best Practices

### 1. Data Quality
- Provide at least 50+ data points per timeframe
- Ensure OHLCV data is clean and consistent
- Use recent data for better analysis

### 2. Model Selection
- **OpenAI**: Best for complex analysis and consistency
- **Claude**: Strong analytical capabilities, good for risk assessment
- **Gemini**: Fast and cost-effective for frequent analysis

### 3. Risk Management
- Set minimum confidence thresholds (70%+)
- Use position sizing based on confidence
- Always validate Fibonacci levels manually

### 4. Performance Optimization
- Cache analysis results for similar market conditions
- Use async/await for non-blocking analysis
- Implement retry logic for API failures

## Troubleshooting

### Common Issues

1. **No LLM models available**
   ```bash
   # Install dependencies
   pip install openai anthropic google-generativeai
   
   # Set API keys
   export OPENAI_API_KEY="your_key"
   ```

2. **JSON parsing errors**
   ```python
   # Check raw response
   if not analysis.get("parsed"):
       print(analysis.get("raw_response"))
   ```

3. **Low confidence scores**
   - Provide more historical data
   - Check market conditions (high volatility = lower confidence)
   - Try different LLM models

4. **API rate limits**
   ```python
   # Implement retry with exponential backoff
   import time
   
   for attempt in range(3):
       try:
           analysis = await llm_service.analyze_market(...)
           break
       except Exception as e:
           if "rate limit" in str(e).lower():
               time.sleep(2 ** attempt)
           else:
               raise
   ```

## Integration with Existing Bots

The LLM service can be easily integrated with existing bot frameworks:

```python
# In your existing bot's execute_algorithm method
from services.llm_integration import create_llm_service

class ExistingBot(CustomBot):
    def __init__(self, config, api_keys):
        super().__init__(config, api_keys)
        self.llm_service = create_llm_service(config)
    
    def execute_algorithm(self, data, timeframe, subscription_config=None):
        # Your existing logic
        traditional_signal = self.calculate_traditional_indicators(data)
        
        # Add LLM analysis
        llm_analysis = await self.get_llm_analysis(data)
        
        # Combine signals
        final_action = self.combine_signals(traditional_signal, llm_analysis)
        
        return final_action
```

## Future Enhancements

- [ ] Real-time sentiment analysis
- [ ] News integration
- [ ] Multi-asset correlation analysis
- [ ] Custom prompt templates
- [ ] Performance backtesting
- [ ] Risk-adjusted position sizing
- [ ] Portfolio-level analysis

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation for your chosen LLM provider
3. Ensure all dependencies are installed correctly
4. Verify API keys and permissions

## License

This LLM Integration Service is part of the Bot Marketplace platform.