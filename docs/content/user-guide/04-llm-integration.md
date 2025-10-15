# 🤖 LLM Integration Guide

Add AI intelligence to your trading bots with LLM (Large Language Model) integration.

## 📋 Table of Contents

1. [What is LLM Integration?](#what-is-llm-integration)
2. [Supported Providers](#supported-providers)
3. [Setting Up LLM Providers](#setting-up-llm-providers)
4. [Using LLMs in Bots](#using-llms-in-bots)
5. [Cost Management](#cost-management)
6. [Best Practices](#best-practices)

---

## 1. What is LLM Integration?

### Overview

LLM integration allows your trading bots to:

- 📰 **Analyze news** and market sentiment
- 🧠 **Make intelligent decisions** based on context
- 📊 **Interpret complex data** patterns
- 💬 **Generate trading insights** in natural language
- 🔍 **Process unstructured data** (social media, forums, etc.)

### How It Works

```
┌──────────────┐      ┌─────────────┐      ┌──────────────┐
│ Market Data  │──────►│ Your Bot    │──────►│ LLM Provider │
│ News, Prices │      │ + Prompt    │      │ (OpenAI)     │
└──────────────┘      └─────────────┘      └──────────────┘
                             │                      │
                             │   ◄──────────────────┘
                             │   AI Analysis
                             ▼
                      ┌─────────────┐
                      │ Trading     │
                      │ Signal      │
                      └─────────────┘
```

---

## 2. Supported Providers

### Provider Comparison

| Provider | Models | Speed | Cost | Best For |
|----------|--------|-------|------|----------|
| **OpenAI** | GPT-4, GPT-3.5 | Fast | $$$ | General purpose |
| **Anthropic** | Claude 3 (Opus, Sonnet, Haiku) | Fast | $$ | Long context, safety |
| **Google** | Gemini Pro, Ultra | Fast | $ | Multimodal analysis |
| **Groq** | Llama 3, Mixtral | Ultra-fast | $ | Low-latency trading |
| **Cohere** | Command, Embed | Fast | $$ | Embeddings, search |

### Recommended Models

#### For Trading Analysis
- **GPT-4 Turbo** - Best overall performance
- **Claude 3 Opus** - Best for complex reasoning
- **Gemini 1.5 Pro** - Best value for money

#### For Real-Time Trading
- **GPT-3.5 Turbo** - Fast and cheap
- **Groq Llama 3** - Ultra-low latency
- **Claude 3 Haiku** - Fast and accurate

---

## 3. Setting Up LLM Providers

### OpenAI Setup

#### Step 1: Get API Key

1. Go to [platform.openai.com](https://platform.openai.com)
2. Sign up / Log in
3. Navigate to **API Keys**
4. Click **"Create new secret key"**
5. Copy your key: `sk-proj-...`

#### Step 2: Add to QuantumForge

**Via Web Interface:**

1. Go to **LLM Providers** → **"Add Provider"**
2. Fill in the form:
   ```
   Provider: OpenAI
   Display Name: My OpenAI Provider
   API Key: sk-proj-...
   Organization ID: (optional)
   ```
3. **Model Settings**:
   ```
   Default Model: gpt-4-turbo
   Max Tokens: 4000
   Temperature: 0.3
   Top P: 1.0
   ```
4. Click **"Save & Test Connection"**
5. ✅ Connection successful!

**Via API:**

```python
import requests

response = requests.post(
    "https://api.quantumforge.ai/llm-providers",
    headers={"Authorization": f"Bearer {YOUR_API_TOKEN}"},
    json={
        "provider_type": "OPENAI",
        "api_key": "sk-proj-...",
        "config": {
            "model": "gpt-4-turbo",
            "max_tokens": 4000,
            "temperature": 0.3
        }
    }
)
```

### Anthropic (Claude) Setup

1. Go to **LLM Providers** → **"Add Provider"**
2. Configure:
   ```
   Provider: Anthropic
   Display Name: Claude 3 Provider
   API Key: sk-ant-...
   Default Model: claude-3-opus-20240229
   Max Tokens: 4000
   Temperature: 0.5
   ```
3. Save & Test

### Google Gemini Setup

1. Get API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to QuantumForge:
   ```
   Provider: Google (Gemini)
   Display Name: Gemini Provider
   API Key: AI...
   Default Model: gemini-1.5-pro
   ```

### Groq Setup (Fast & Free)

1. Get API key from [console.groq.com](https://console.groq.com)
2. Add provider:
   ```
   Provider: Groq
   Display Name: Groq Llama 3
   API Key: gsk_...
   Default Model: llama-3.1-70b-versatile
   ```

---

## 4. Using LLMs in Bots

### Method 1: Direct LLM Bot

Create a bot that runs entirely on LLM decisions:

```python
# Bot Configuration
{
  "bot_type": "LLM",
  "bot_mode": "ACTIVE",
  "llm_provider_id": 123,
  "prompt_template_id": 456,
  "analysis_frequency": "1h",  # Run AI analysis every hour
  "min_confidence": 70,        # Only trade if AI is 70%+ confident
}
```

### Method 2: Hybrid Bot (Technical + LLM)

Combine technical indicators with AI analysis:

```python
# Strategy: Buy when RSI < 30 AND AI confirms bullish
{
  "bot_type": "TECHNICAL",
  "llm_provider_id": 123,
  "entry_conditions": [
    "rsi < 30",                    # Technical signal
    "llm_sentiment == 'BULLISH'"   # AI confirmation
  ]
}
```

### Method 3: LLM as Filter

Use LLM to filter technical signals:

```python
# Only execute technical signals if AI approves
{
  "bot_type": "TECHNICAL",
  "llm_filter_enabled": true,
  "llm_filter_confidence": 60,
  "entry_conditions": [
    "macd_crossover == true",
    "rsi < 30"
  ]
}
```

---

## 5. Cost Management

### Token Usage

Understanding costs:

| Provider | Model | Input Cost | Output Cost | Example Cost |
|----------|-------|------------|-------------|--------------|
| OpenAI | GPT-4 Turbo | $10 / 1M | $30 / 1M | ~$0.05/call |
| OpenAI | GPT-3.5 Turbo | $0.50 / 1M | $1.50 / 1M | ~$0.002/call |
| Anthropic | Claude 3 Opus | $15 / 1M | $75 / 1M | ~$0.10/call |
| Anthropic | Claude 3 Haiku | $0.25 / 1M | $1.25 / 1M | ~$0.002/call |
| Google | Gemini 1.5 Pro | $3.50 / 1M | $10.50 / 1M | ~$0.02/call |
| Groq | Llama 3 70B | **FREE** | **FREE** | **$0/call** |

### Cost Optimization Tips

#### 1. Use Cheaper Models for Simple Tasks

```python
# Use GPT-3.5 for sentiment analysis
llm_provider_sentiment = "openai-gpt35"

# Use GPT-4 only for complex decisions
llm_provider_trading = "openai-gpt4"
```

#### 2. Reduce Call Frequency

```python
# Instead of every 5 minutes:
"analysis_frequency": "5m"  # Expensive!

# Use hourly or on-demand:
"analysis_frequency": "1h"   # Much cheaper
"trigger_on_signal": true    # Only when technical signal appears
```

#### 3. Cache Results

```python
{
  "cache_llm_results": true,
  "cache_duration": "15m",  # Reuse same analysis for 15 minutes
}
```

#### 4. Set Token Limits

```python
{
  "max_tokens": 500,  # Limit response length
  "max_calls_per_day": 100,  # Budget protection
}
```

### Monitoring Costs

Track your LLM usage:

```python
# Get usage stats
GET /llm-providers/{id}/usage

Response:
{
  "total_calls": 1234,
  "total_tokens": 500000,
  "total_cost_usd": 25.50,
  "last_30_days": {
    "calls": 456,
    "tokens": 180000,
    "cost_usd": 9.20
  }
}
```

### Cost Alerts

Set up budget alerts:

1. Go to **LLM Providers** → **[Your Provider]** → **"Alerts"**
2. Configure:
   ```
   Daily Budget: $10
   Alert at: 80% ($8)
   Action: Pause bot automatically
   ```

---

## 6. Best Practices

### Prompt Engineering

#### ✅ Good Prompt

```
You are a professional crypto trader.

Analyze BTC/USDT based on:
- Current price: $65,420
- RSI(14): 45
- MACD: Bullish crossover
- Volume: Above average

Should we BUY, SELL, or HOLD?

Respond in JSON:
{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reason": "brief explanation",
  "entry": price,
  "stop_loss": price,
  "take_profit": price
}
```

**Why it's good**:
- Clear role definition
- Specific data points
- Structured output (JSON)
- Actionable format

#### ❌ Bad Prompt

```
What do you think about Bitcoin?
```

**Why it's bad**:
- Too vague
- No structure
- Not actionable
- No context

### Model Selection

```python
# For complex analysis (once per hour)
use_model = "gpt-4-turbo"

# For quick sentiment checks (every 5 min)
use_model = "gpt-3.5-turbo"

# For ultra-fast signals (every minute)
use_model = "groq-llama-3-70b"
```

### Error Handling

```python
{
  "llm_retry_on_error": true,
  "max_retries": 3,
  "fallback_to_technical": true,  # Use technical if LLM fails
  "timeout_seconds": 30,
}
```

### Testing

Always test LLM responses:

1. **Prompt Testing** (in Prompt Template editor)
   - Test with sample data
   - Verify JSON format
   - Check response consistency

2. **Bot Backtesting**
   - Run backtest with LLM enabled
   - Compare with pure technical strategy
   - Measure ROI improvement

---

## 🎯 Next Steps

- **[Prompt Engineering →](./05-prompt-engineering.md)** - Master prompt creation
- **[Multi-Pair Trading →](./06-multi-pair-trading.md)** - Scale your bot
- **[Risk Management →](./08-risk-management.md)** - Protect your capital

---

## 🆘 Troubleshooting

### "LLM provider authentication failed"
```
Solution:
1. Verify API key is correct
2. Check key permissions
3. Verify billing is active
```

### "LLM responses are inconsistent"
```
Solution:
1. Lower temperature (0.1-0.3)
2. Use more specific prompts
3. Add examples in system prompt
4. Switch to GPT-4 for better reasoning
```

### "Too expensive - high token usage"
```
Solution:
1. Reduce call frequency
2. Switch to cheaper model (GPT-3.5, Groq)
3. Limit max_tokens
4. Use caching
```

---

**Next**: [Prompt Engineering Guide →](./05-prompt-engineering.md)

