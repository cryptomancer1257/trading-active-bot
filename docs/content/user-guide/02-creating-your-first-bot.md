# 🤖 Creating Your First Trading Bot

Learn how to create a simple yet effective trading bot in QuantumForge Studio. This guide covers everything from choosing templates to deploying your first AI trading entity.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Bot Types Overview](#bot-types-overview)
3. [Creating a Technical Analysis Bot](#creating-a-technical-analysis-bot)
4. [Creating an LLM-Powered Bot](#creating-an-llm-powered-bot)
5. [Bot Configuration](#bot-configuration)
6. [Testing Your Bot](#testing-your-bot)

---

## 1. Quick Start

### Video Tutorial

🎥 **Watch**: [Creating Your First Bot (5 minutes)](https://youtube.com/quantumforge/first-bot)

### Step-by-Step

```
1. Login to Studio → 2. Click "Create Bot" → 3. Choose Template → 
4. Configure → 5. Test → 6. Deploy ✅
```

---

## 2. Bot Types Overview

QuantumForge supports 4 main bot types:

### 📊 Technical Analysis Bots

**Best for**: Classic trading strategies

**Features**:
- Built-in indicators (RSI, MACD, Bollinger Bands, etc.)
- No coding required
- Fast execution
- Low cost

**Use cases**:
- Trend following
- Mean reversion
- Breakout strategies

### 🧠 Machine Learning Bots

**Best for**: Pattern recognition

**Features**:
- Upload your ML models
- Support for scikit-learn, TensorFlow, PyTorch
- Feature engineering
- Model retraining

**Use cases**:
- Price prediction
- Sentiment analysis
- Anomaly detection

### 🤖 LLM-Powered Bots

**Best for**: Market intelligence

**Features**:
- Natural language processing
- News & social media analysis
- Multi-source data fusion
- Contextual decision making

**Use cases**:
- Fundamental analysis
- Event-driven trading
- Market sentiment trading

### 🌐 RPA Bots (Browser Automation)

**Best for**: Complex workflows

**Features**:
- Browser automation (Selenium/Playwright)
- Web scraping
- Multi-step workflows
- Visual verification

**Use cases**:
- Copy trading
- Cross-platform arbitrage
- Manual strategy automation

---

## 3. Creating a Technical Analysis Bot

Let's create a simple **RSI Mean Reversion Bot**.

### Strategy Logic

```
BUY when:
- RSI < 30 (oversold)
- Price above 200 EMA (uptrend)

SELL when:
- RSI > 70 (overbought)
OR
- Take profit hit (+2%)
```

### Step 1: Create Bot

1. Go to **My Bots** → Click **"Create New Bot"**

2. Fill in basic info:
   ```
   Bot Name: RSI Mean Reversion Bot
   Description: Simple RSI strategy for BTC/USDT
   Category: Technical Analysis
   Bot Type: TECHNICAL
   Bot Mode: ACTIVE
   ```

3. Click **"Next"**

### Step 2: Configure Strategy

4. **Trading Settings**:
   ```
   Exchange: Binance
   Trading Pair: BTC/USDT
   Timeframe: 15m
   Trade Type: SPOT
   ```

5. **Strategy Parameters**:
   ```json
   {
     "indicators": {
       "rsi": {
         "period": 14,
         "overbought": 70,
         "oversold": 30
       },
       "ema": {
         "period": 200
       }
     },
     "entry_conditions": [
       "rsi < 30",
       "close > ema_200"
     ],
     "exit_conditions": [
       "rsi > 70",
       "profit >= 2.0"
     ]
   }
   ```

### Step 3: Risk Management

6. **Risk Settings**:
   ```
   Position Size: 10% of balance
   Max Position: $1000
   Stop Loss: 2%
   Take Profit: 2%
   Max Open Trades: 1
   ```

7. **Execution Settings**:
   ```
   Order Type: LIMIT
   Buy Order: -0.1% from current price
   Sell Order: +0.1% from current price
   ```

### Step 4: Save & Deploy

8. Click **"Create Bot"**
9. You'll see: ✅ **"Bot created successfully!"**

---

## 4. Creating an LLM-Powered Bot

Now let's create an **AI Sentiment Trading Bot** using GPT-4.

### Prerequisites

- OpenAI API key (or Anthropic, Gemini)
- LLM Provider configured (see [LLM Integration Guide](./04-llm-integration.md))

### Step 1: Create LLM Provider

1. Go to **LLM Providers** → **"Add Provider"**

2. Fill in details:
   ```
   Provider: OpenAI
   Model: gpt-4-turbo
   API Key: sk-...
   Max Tokens: 4000
   Temperature: 0.3
   ```

3. Click **"Save & Test"**

### Step 2: Create Prompt Template

4. Go to **Prompt Templates** → **"Create Prompt"**

5. **Prompt Configuration**:
   ```
   Title: BTC Market Analysis
   Category: Technical Analysis
   Model: gpt-4-turbo
   System Prompt:
   ---
   You are an expert crypto trader analyzing BTC/USDT.
   Analyze the current market and provide a trading signal.
   
   Consider:
   - Price action
   - Technical indicators
   - Market sentiment
   - Risk/reward ratio
   
   Respond in JSON format:
   {
     "signal": "BUY" | "SELL" | "HOLD",
     "confidence": 0-100,
     "reason": "explanation",
     "entry_price": number,
     "stop_loss": number,
     "take_profit": number
   }
   ```

   ```
   User Prompt:
   ---
   Current Price: {{current_price}}
   24h Change: {{price_change_24h}}%
   RSI(14): {{rsi}}
   MACD: {{macd}}
   Volume: {{volume_24h}}
   
   Recent News:
   {{news_headlines}}
   
   What's your analysis?
   ```

6. **Test the Prompt**:
   - Click **"Test"**
   - Enter sample data
   - Verify response format

### Step 3: Create LLM Bot

7. Go to **My Bots** → **"Create New Bot"**

8. **Basic Info**:
   ```
   Bot Name: AI Sentiment Trader
   Bot Type: LLM
   Bot Mode: ACTIVE
   ```

9. **LLM Configuration**:
   ```
   LLM Provider: OpenAI (GPT-4)
   Prompt Template: BTC Market Analysis
   Analysis Frequency: Every 1 hour
   ```

10. **Trading Settings**:
    ```
    Exchange: Binance
    Trading Pair: BTC/USDT
    Trade Type: SPOT
    ```

11. **Risk Settings**:
    ```
    Min Confidence: 70% (only trade when AI is 70%+ confident)
    Position Size: 5% of balance
    Stop Loss: As suggested by AI
    Take Profit: As suggested by AI
    ```

### Step 4: Save & Backtest

12. Click **"Create Bot"**
13. Run backtest to verify performance

---

## 5. Bot Configuration

### Essential Parameters

#### Trading Configuration

```python
{
  "exchange_type": "BINANCE",      # Exchange to trade on
  "trading_pair": "BTC/USDT",      # Primary trading pair
  "secondary_trading_pairs": [     # Multi-pair trading (optional)
    "ETH/USDT",
    "BNB/USDT"
  ],
  "timeframe": "15m",              # Candle timeframe
  "bot_mode": "ACTIVE",            # ACTIVE or PASSIVE
  "bot_type": "FUTURES",           # SPOT or FUTURES
}
```

#### Execution Configuration

```python
{
  "buy_order_type": "PERCENTAGE",  # PERCENTAGE or FIXED
  "buy_order_value": 100.0,        # 100% = use full allocated capital
  "sell_order_type": "ALL",        # ALL or PERCENTAGE
  "sell_order_value": 100.0,       # 100% = sell entire position
}
```

#### Risk Configuration

```python
{
  "stop_loss_percent": 2.0,        # Stop loss: 2%
  "take_profit_percent": 4.0,      # Take profit: 4%
  "max_position_size": 1000.0,     # Max $1000 per trade
  "risk_per_trade": 1.0,           # Risk 1% of portfolio per trade
  "max_daily_loss": 5.0,           # Stop trading if -5% daily
  "trailing_stop": true,           # Enable trailing stop
  "trailing_stop_percent": 1.0,    # Trail by 1%
}
```

#### Leverage (FUTURES only)

```python
{
  "leverage": 10,                  # 10x leverage
  "leverage_type": "ISOLATED",     # ISOLATED or CROSS
}
```

⚠️ **Warning**: Higher leverage = higher risk!

---

## 6. Testing Your Bot

### Paper Trading (Testnet)

**Always test with fake money first!**

1. **Switch to Testnet**:
   ```
   Settings → Exchange Credentials → Add Testnet Keys
   ```

2. **Create Subscription**:
   ```
   My Bots → [Your Bot] → "Test on Testnet"
   ```

3. **Monitor Performance**:
   - Go to **Active Subscriptions**
   - Watch real-time trades
   - Check P&L

### Backtesting

Test your strategy on historical data:

1. **Start Backtest**:
   ```
   My Bots → [Your Bot] → "Backtest"
   ```

2. **Configure**:
   ```
   Start Date: 2024-01-01
   End Date: 2024-10-01
   Initial Balance: $10,000
   ```

3. **Review Results**:
   ```
   Total Return: +25.5%
   Sharpe Ratio: 1.8
   Max Drawdown: -8.2%
   Win Rate: 65%
   Total Trades: 156
   ```

### Performance Metrics

Key metrics to watch:

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| **Win Rate** | >60% | 50-60% | <50% |
| **Sharpe Ratio** | >1.5 | 1.0-1.5 | <1.0 |
| **Max Drawdown** | <10% | 10-20% | >20% |
| **Profit Factor** | >2.0 | 1.5-2.0 | <1.5 |

---

## 🎯 What's Next?

Your bot is created! Now learn how to optimize it:

- **[Bot Configuration →](./03-bot-configuration.md)** - Fine-tune parameters
- **[LLM Integration →](./04-llm-integration.md)** - Add AI intelligence
- **[Risk Management →](./08-risk-management.md)** - Protect your capital

---

## 📝 Quick Tips

### Do's ✅

- ✅ Always test on testnet first
- ✅ Start with small position sizes
- ✅ Use stop losses
- ✅ Monitor your bot daily
- ✅ Keep API keys secure

### Don'ts ❌

- ❌ Don't use maximum leverage
- ❌ Don't trade without testing
- ❌ Don't ignore risk management
- ❌ Don't share your API keys
- ❌ Don't panic during drawdowns

---

## 🆘 Troubleshooting

### "Bot creation failed"
```
Check:
1. All required fields filled
2. Valid exchange credentials
3. Trading pair exists on exchange
```

### "Backtest shows poor performance"
```
Try:
1. Adjust indicator periods
2. Tighten stop loss
3. Change timeframe
4. Test different pairs
```

### "Bot not executing trades"
```
Verify:
1. Bot status is ACTIVE
2. Subscription is running
3. Exchange credentials valid
4. Sufficient balance
```

---

**Next**: [Bot Configuration Guide →](./03-bot-configuration.md)

