# ✍️ Prompt Engineering for Trading Bots

Master the art of creating effective prompts for AI-powered trading decisions.

## 📋 Table of Contents

1. [Introduction to Prompt Engineering](#introduction)
2. [Prompt Template Basics](#prompt-template-basics)
3. [Creating Your First Prompt](#creating-your-first-prompt)
4. [Advanced Techniques](#advanced-techniques)
5. [Prompt Categories](#prompt-categories)
6. [Attaching Prompts to Bots](#attaching-prompts-to-bots)
7. [Best Practices](#best-practices)

---

## 1. Introduction to Prompt Engineering {#introduction}

### What is Prompt Engineering?

**Prompt engineering** is the process of designing inputs (prompts) to guide AI models toward producing desired outputs.

In trading, good prompts help AI:
- ✅ Make accurate trading decisions
- ✅ Provide clear, actionable signals
- ✅ Explain reasoning transparently
- ✅ Respond consistently

### Anatomy of a Trading Prompt

```
┌─────────────────────────────────────────┐
│ System Prompt (Who is the AI?)         │
│ - Role definition                       │
│ - Capabilities                          │
│ - Output format                         │
└─────────────────────────────────────────┘
             ▼
┌─────────────────────────────────────────┐
│ User Prompt (What data to analyze?)    │
│ - Market data                           │
│ - Technical indicators                  │
│ - News/sentiment                        │
│ - Variables: {{price}}, {{rsi}}        │
└─────────────────────────────────────────┘
             ▼
┌─────────────────────────────────────────┐
│ AI Response                             │
│ {                                       │
│   "signal": "BUY",                     │
│   "confidence": 85,                    │
│   "entry": 65000,                      │
│   ...                                  │
│ }                                       │
└─────────────────────────────────────────┘
```

---

## 2. Prompt Template Basics

### Template Structure

Every prompt template has:

```python
{
  "title": "BTC Trend Analysis",
  "category": "Technical Analysis",
  "llm_provider": "openai-gpt4",
  "system_prompt": "...",    # WHO the AI is
  "user_prompt": "...",       # WHAT to analyze
  "parameters": {...},        # Model settings
  "output_schema": {...}      # Expected response format
}
```

### Variables

Use variables to inject dynamic data:

```
Available variables:
- {{current_price}}         Current market price
- {{price_change_24h}}      24h price change %
- {{volume_24h}}            24h trading volume
- {{rsi}}                   RSI indicator value
- {{macd}}                  MACD value
- {{ema_200}}               200 EMA
- {{bollinger_upper}}       Bollinger upper band
- {{bollinger_lower}}       Bollinger lower band
- {{news_headlines}}        Latest news headlines
- {{social_sentiment}}      Social media sentiment
- {{timestamp}}             Current timestamp
```

---

## 3. Creating Your First Prompt

### Example: Simple Trend Analysis

Let's create a prompt to analyze BTC trend.

#### Step 1: Navigate to Prompt Templates

1. Go to **Prompt Templates** in Studio
2. Click **"Create New Prompt"**

#### Step 2: Basic Information

```
Title: BTC Trend Analyzer
Description: Analyzes BTC/USDT trend using price action and RSI
Category: Technical Analysis
Is Public: No (keep private for now)
```

#### Step 3: System Prompt

```markdown
You are an expert cryptocurrency trader specializing in Bitcoin.

Your task is to analyze BTC/USDT and determine the current trend.

Use the following criteria:
- Price above 200 EMA = Bullish trend
- Price below 200 EMA = Bearish trend
- RSI > 70 = Overbought
- RSI < 30 = Oversold

Provide your analysis in JSON format:
{
  "trend": "BULLISH" | "BEARISH" | "NEUTRAL",
  "strength": 1-10,
  "recommendation": "BUY" | "SELL" | "HOLD",
  "confidence": 0-100,
  "reasoning": "brief explanation (max 100 words)"
}

Be concise and objective.
```

#### Step 4: User Prompt

```markdown
Analyze current BTC/USDT market conditions:

**Price Data:**
- Current Price: ${{current_price}}
- 24h Change: {{price_change_24h}}%
- 200 EMA: ${{ema_200}}

**Technical Indicators:**
- RSI(14): {{rsi}}
- MACD: {{macd}}
- Volume (24h): ${{volume_24h}}

**Recent Price Action:**
- High (24h): ${{high_24h}}
- Low (24h): ${{low_24h}}

What is your analysis?
```

#### Step 5: Model Configuration

```json
{
  "model": "gpt-4-turbo",
  "temperature": 0.3,
  "max_tokens": 500,
  "top_p": 1.0
}
```

#### Step 6: Test the Prompt

Click **"Test Prompt"** and enter sample data:

```json
{
  "current_price": "65420",
  "price_change_24h": "+2.5",
  "ema_200": "63000",
  "rsi": "58",
  "macd": "150",
  "volume_24h": "28000000000",
  "high_24h": "66000",
  "low_24h": "64200"
}
```

**Expected Response:**
```json
{
  "trend": "BULLISH",
  "strength": 7,
  "recommendation": "HOLD",
  "confidence": 75,
  "reasoning": "Price is above 200 EMA indicating bullish trend. RSI at 58 shows neutral momentum, not overbought. MACD is positive. Strong uptrend but wait for better entry."
}
```

#### Step 7: Save Template

Click **"Save Template"** ✅

---

## 4. Advanced Techniques

### Technique 1: Few-Shot Learning

Provide examples in your system prompt:

```markdown
You are a crypto trading expert.

Here are examples of good analysis:

Example 1:
Input: BTC at $50,000, RSI 75, above 200 EMA
Output: {"signal": "SELL", "confidence": 80, "reason": "Overbought in uptrend, take profits"}

Example 2:
Input: BTC at $40,000, RSI 28, below 200 EMA
Output: {"signal": "HOLD", "confidence": 60, "reason": "Oversold but in downtrend, wait for reversal confirmation"}

Now analyze the current market:
[User prompt with variables]
```

### Technique 2: Chain of Thought

Ask AI to explain its reasoning step-by-step:

```markdown
Analyze the market using these steps:

1. **Trend Analysis**: Is the price above or below key EMAs?
2. **Momentum Check**: What do RSI and MACD indicate?
3. **Volume Analysis**: Is volume confirming the move?
4. **Risk Assessment**: What's the risk/reward ratio?
5. **Final Decision**: BUY, SELL, or HOLD?

Provide your analysis in JSON format with each step explained.
```

### Technique 3: Multi-Criteria Decision

Combine multiple factors:

```markdown
Analyze BTC/USDT based on:

**Technical Score (40%)**:
- Trend direction
- RSI levels
- MACD signal

**Fundamental Score (30%)**:
- News sentiment
- On-chain metrics
- Market dominance

**Risk Score (30%)**:
- Volatility
- Support/resistance levels
- Market conditions

Calculate weighted score (0-100) and make recommendation.
```

### Technique 4: Sentiment Analysis

Incorporate news and social media:

```markdown
System Prompt:
---
You are a crypto market analyst specializing in sentiment analysis.

Analyze the following news headlines and social sentiment:

News: {{news_headlines}}
Social Sentiment: {{social_sentiment}}
Reddit Trending: {{reddit_trending}}

Classify overall sentiment as:
- VERY BULLISH (80-100)
- BULLISH (60-80)
- NEUTRAL (40-60)
- BEARISH (20-40)
- VERY BEARISH (0-20)

Respond in JSON.
```

---

## 5. Prompt Categories

### Technical Analysis Prompts

**Use for**: Price action, indicators, chart patterns

```markdown
Examples:
- Trend Identification
- Support/Resistance Detection
- Breakout Analysis
- Divergence Detection
```

### Fundamental Analysis Prompts

**Use for**: News, on-chain data, market events

```markdown
Examples:
- News Impact Analysis
- On-Chain Metrics Evaluation
- Market Cycle Detection
- Macro Trend Analysis
```

### Risk Management Prompts

**Use for**: Position sizing, stop loss, portfolio management

```markdown
Examples:
- Optimal Position Size Calculator
- Stop Loss/Take Profit Recommender
- Risk/Reward Analyzer
- Portfolio Rebalancing Advisor
```

### Multi-Timeframe Prompts

**Use for**: Cross-timeframe confirmation

```markdown
Example:
Analyze BTC/USDT across multiple timeframes:
- 15m: {{data_15m}}
- 1h: {{data_1h}}
- 4h: {{data_4h}}
- 1d: {{data_1d}}

Determine if all timeframes align for a trade.
```

---

## 6. Attaching Prompts to Bots

### Method 1: During Bot Creation

1. Create bot → **Bot Configuration**
2. Enable **"Use LLM"**
3. Select **LLM Provider**
4. Select **Prompt Template**
5. Configure **Analysis Frequency**

```python
{
  "llm_enabled": true,
  "llm_provider_id": 123,
  "prompt_template_id": 456,
  "analysis_frequency": "1h"
}
```

### Method 2: Update Existing Bot

1. Go to **My Bots** → Select bot
2. Click **"Edit"**
3. Scroll to **"LLM Configuration"**
4. Attach prompt template
5. **Save Changes**

### Method 3: Via API

```python
import requests

# Attach prompt to bot
response = requests.patch(
    f"https://api.quantumforge.ai/bots/{bot_id}",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "llm_provider_id": 123,
        "prompt_template_id": 456,
        "llm_config": {
            "analysis_frequency": "30m",
            "min_confidence": 70
        }
    }
)
```

---

## 7. Best Practices

### Do's ✅

#### 1. Be Specific
```markdown
❌ Bad: "Analyze the market"
✅ Good: "Analyze BTC/USDT using RSI, MACD, and volume. Determine if current price action indicates a bullish or bearish trend."
```

#### 2. Define Output Format
```markdown
❌ Bad: "What do you think?"
✅ Good: "Respond in JSON: {\"signal\": \"BUY\"|\"SELL\"|\"HOLD\", \"confidence\": 0-100}"
```

#### 3. Set Clear Criteria
```markdown
❌ Bad: "Is this a good trade?"
✅ Good: "BUY if: RSI < 30 AND price > EMA200. SELL if: RSI > 70 OR stop loss hit."
```

#### 4. Include Context
```markdown
❌ Bad: "Current price: {{price}}"
✅ Good: 
"Current BTC/USDT: ${{price}}
24h High/Low: ${{high_24h}} / ${{low_24h}}
Volume: ${{volume_24h}}
Trend: Price {{trend_direction}} 200 EMA"
```

#### 5. Test Thoroughly
- Test with various market conditions
- Verify JSON response format
- Check edge cases (extreme RSI, low volume, etc.)

### Don'ts ❌

#### 1. Don't Be Vague
```markdown
❌ "Tell me about Bitcoin"
✅ "Analyze BTC/USDT trend based on current technical indicators"
```

#### 2. Don't Over-Complicate
```markdown
❌ 2000-word essay with every possible indicator
✅ Focus on 3-5 key indicators that matter most
```

#### 3. Don't Forget Error Handling
```markdown
✅ Good Prompt:
"If any indicator is unavailable, use the best available data and note the limitation in your response."
```

#### 4. Don't Ignore Token Limits
```markdown
❌ Sending 10,000 words of news articles
✅ Summarize top 5 headlines in 500 words
```

---

## 📝 Prompt Templates Library

### Template 1: Simple Trend Follower

```markdown
System: You are a trend-following trader. Only trade with the trend.

User: 
Price: ${{price}}
200 EMA: ${{ema_200}}
RSI: {{rsi}}

Signal: BUY if price > EMA AND RSI < 70
        SELL if price < EMA OR RSI > 70
        
JSON response required.
```

### Template 2: News-Driven Trader

```markdown
System: You analyze crypto news for trading signals.

User:
Latest Headlines:
{{news_headlines}}

Sentiment Analysis:
{{sentiment_score}}

Determine if news is:
- VERY BULLISH → BUY
- BULLISH → HOLD/BUY
- NEUTRAL → HOLD
- BEARISH → HOLD/SELL  
- VERY BEARISH → SELL
```

### Template 3: Risk-Adjusted Entry

```markdown
System: You calculate optimal entry, stop loss, and take profit.

User:
Current Price: ${{price}}
Support: ${{support}}
Resistance: ${{resistance}}
ATR: {{atr}}

Calculate:
1. Entry price (near support)
2. Stop loss (below support)
3. Take profit (near resistance)
4. Risk/Reward ratio

Only suggest trade if R:R > 2:1
```

---

## 🎯 Next Steps

- **[Multi-Pair Trading →](./06-multi-pair-trading.md)** - Scale to multiple pairs
- **[Publishing Bot →](./07-publishing-to-marketplace.md)** - Share your creation
- **[Risk Management →](./08-risk-management.md)** - Protect capital

---

## 🆘 Troubleshooting

### "AI responses are inconsistent"
```
Fix:
1. Lower temperature to 0.1-0.3
2. Add more specific criteria
3. Use few-shot examples
4. Test with multiple scenarios
```

### "JSON parsing errors"
```
Fix:
1. Explicitly request JSON format
2. Provide JSON schema example
3. Add validation in bot code
4. Use structured output (if supported)
```

### "AI ignores my instructions"
```
Fix:
1. Be more explicit and direct
2. Use imperative language ("Analyze", "Calculate", "Determine")
3. Repeat important instructions
4. Use formatting (**, ##, lists)
```

---

**Next**: [Multi-Pair Trading Guide →](./06-multi-pair-trading.md)

