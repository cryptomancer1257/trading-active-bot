# ⚙️ Bot Configuration Guide

Master all bot configuration parameters to optimize your trading strategy.

## 📋 Table of Contents

1. [Bot Types](#bot-types)
2. [Trading Configuration](#trading-configuration)
3. [Leverage Settings](#leverage-settings)
4. [Execution Configuration](#execution-configuration)
5. [Risk Configuration](#risk-configuration)
6. [Strategy Parameters](#strategy-parameters)
7. [Advanced Settings](#advanced-settings)

---

## 1. Bot Types

### Bot Mode

| Mode | Description | Use Case |
|------|-------------|----------|
| **ACTIVE** | Bot executes trades automatically | Live trading |
| **PASSIVE** | Bot only sends signals, no execution | Signal-only, manual trading |

```python
{
  "bot_mode": "ACTIVE"  # or "PASSIVE"
}
```

### Bot Type

| Type | Description | Trading Style |
|------|-------------|---------------|
| **SPOT** | Spot trading (buy and hold) | Long-only, no leverage |
| **FUTURES** | Futures/perpetual contracts | Long/short, with leverage |
| **TECHNICAL** | Technical analysis based | Indicators, patterns |
| **ML** | Machine learning model | Predictive models |
| **LLM** | AI-powered analysis | GPT, Claude, Gemini |
| **FUTURES_RPA** | Browser automation | Complex workflows |

```python
{
  "bot_type": "FUTURES",
  "bot_mode": "ACTIVE"
}
```

---

## 2. Trading Configuration

### Exchange Selection

**Supported Exchanges:**
- ✅ Binance (SPOT + FUTURES)
- ✅ Bybit (SPOT + FUTURES)
- ✅ OKX (SPOT + FUTURES)
- ✅ Bitget (FUTURES)
- ✅ Huobi (SPOT)

```python
{
  "exchange_type": "BINANCE"  # or "BYBIT", "OKX", etc.
}
```

### Trading Pairs

#### Single Pair Trading

```python
{
  "trading_pair": "BTC/USDT",
  "timeframe": "15m"
}
```

#### Multi-Pair Trading

Trade multiple pairs simultaneously:

```python
{
  "trading_pair": "BTC/USDT",           # Primary pair
  "secondary_trading_pairs": [          # Additional pairs
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT"
  ]
}
```

**Benefits:**
- 🎯 Diversification
- 📈 More trading opportunities
- 🔄 Risk spreading

**Important**: Bot will prioritize primary pair, then trade secondary pairs when primary is busy.

### Timeframes

Available timeframes:

```python
Supported:
- "1m"   # 1 minute
- "5m"   # 5 minutes
- "15m"  # 15 minutes (recommended for most strategies)
- "30m"  # 30 minutes
- "1h"   # 1 hour
- "4h"   # 4 hours
- "1d"   # 1 day
```

**Choosing timeframe**:
- Scalping: 1m, 5m
- Day trading: 15m, 30m, 1h
- Swing trading: 4h, 1d

### Network Type

```python
{
  "is_testnet": false,        # false = Mainnet (real money)
  "trading_network": "mainnet" # or "testnet"
}
```

⚠️ **Always test on testnet first!**

---

## 3. Leverage Settings (FUTURES Only)

### Basic Leverage

```python
{
  "leverage": 10,              # 1x to 125x (depends on exchange)
  "leverage_type": "ISOLATED"  # ISOLATED or CROSS
}
```

### Leverage Types

#### ISOLATED Leverage
- ✅ Risk limited to position margin
- ✅ Won't liquidate entire account
- ✅ Recommended for beginners

```python
{
  "leverage": 5,
  "leverage_type": "ISOLATED",
  "position_margin": 100  # $100 at risk per trade
}
```

#### CROSS Leverage
- ⚠️ Uses entire account balance as margin
- ⚠️ Higher liquidation risk
- ⚠️ For experienced traders only

```python
{
  "leverage": 10,
  "leverage_type": "CROSS"
}
```

### Leverage Recommendations

| Experience | Leverage | Risk Level |
|------------|----------|------------|
| Beginner | 1-3x | Low |
| Intermediate | 3-10x | Medium |
| Advanced | 10-20x | High |
| Expert | 20-50x | Very High |
| **Avoid** | >50x | **Extreme Risk** |

**Example Configuration:**

```python
# Conservative (Recommended)
{
  "leverage": 5,
  "leverage_type": "ISOLATED",
  "risk_percentage": 1.0  # Risk 1% per trade
}

# Aggressive (High Risk)
{
  "leverage": 20,
  "leverage_type": "CROSS",
  "risk_percentage": 2.0  # Risk 2% per trade
}
```

---

## 4. Execution Configuration

### Order Types

```python
{
  "buy_order_type": "PERCENTAGE",  # or "FIXED"
  "buy_order_value": 100.0,        # 100% of allocated capital
  
  "sell_order_type": "ALL",        # or "PERCENTAGE"
  "sell_order_value": 100.0        # Sell entire position
}
```

### Buy Order Configuration

#### Percentage-based
```python
{
  "buy_order_type": "PERCENTAGE",
  "buy_order_value": 50.0  # Use 50% of available capital
}
```

#### Fixed amount
```python
{
  "buy_order_type": "FIXED",
  "buy_order_value": 1000.0  # Always buy $1000 worth
}
```

### Sell Order Configuration

#### Sell all
```python
{
  "sell_order_type": "ALL"  # Close entire position
}
```

#### Partial sell
```python
{
  "sell_order_type": "PERCENTAGE",
  "sell_order_value": 50.0  # Sell 50% of position
}
```

### Order Placement

```python
{
  "order_placement": "LIMIT",     # LIMIT or MARKET
  "limit_offset_percent": 0.1,   # Place limit order 0.1% better
  "order_timeout": 60            # Cancel if not filled in 60s
}
```

---

## 5. Risk Configuration

### Stop Loss & Take Profit

```python
{
  "stop_loss_percent": 2.0,      # Stop loss at -2%
  "take_profit_percent": 4.0,    # Take profit at +4%
  "trailing_stop": true,         # Enable trailing stop
  "trailing_stop_percent": 1.0   # Trail by 1%
}
```

### Trailing Stop Example

```
Entry: $100
Initial Stop Loss: $98 (-2%)
Take Profit: $104 (+4%)

Price moves to $102:
- Trailing Stop activates
- New Stop Loss: $101 (trail by 1%)

Price moves to $105:
- Stop Loss trails to $104
- Profit locked in!
```

### Position Sizing

```python
{
  "max_position_size": 1000.0,     # Max $1000 per trade
  "risk_per_trade": 1.0,           # Risk 1% of portfolio
  "max_open_positions": 3,         # Max 3 simultaneous trades
}
```

### Advanced Risk Controls

```python
{
  "max_daily_loss": 5.0,           # Stop if -5% daily
  "max_weekly_loss": 10.0,         # Stop if -10% weekly
  "max_drawdown": 15.0,            # Stop if -15% from peak
  
  "daily_trade_limit": 10,         # Max 10 trades per day
  "cooldown_after_loss": 3600,     # Wait 1 hour after loss (seconds)
  
  "volatility_filter": true,       # Reduce size in high volatility
  "min_volume_filter": 1000000     # Only trade if volume > $1M
}
```

### Risk Management Modes

#### DEFAULT Mode
```python
{
  "risk_management_mode": "DEFAULT",
  "risk_config": {
    "stop_loss_percent": 2.0,
    "take_profit_percent": 4.0
  }
}
```

#### AI_PROMPT Mode
Let AI decide risk parameters:
```python
{
  "risk_management_mode": "AI_PROMPT",
  "llm_provider_id": 123,
  "prompt_template_id": 456
}
```
AI will dynamically adjust:
- Stop loss based on volatility
- Position size based on confidence
- Take profit based on resistance levels

---

## 6. Strategy Parameters

### Technical Indicators

```python
{
  "strategy_config": {
    "indicators": {
      "rsi": {
        "period": 14,
        "overbought": 70,
        "oversold": 30
      },
      "macd": {
        "fast": 12,
        "slow": 26,
        "signal": 9
      },
      "ema": {
        "periods": [20, 50, 200]
      },
      "bollinger": {
        "period": 20,
        "std_dev": 2
      }
    }
  }
}
```

### Entry Conditions

```python
{
  "entry_conditions": [
    "rsi < 30",                    # Oversold
    "close > ema_200",             # Above long-term trend
    "macd > macd_signal",          # MACD crossover
    "volume > volume_avg * 1.5"    # High volume
  ],
  "entry_logic": "AND"  # All conditions must be true (or "OR")
}
```

### Exit Conditions

```python
{
  "exit_conditions": [
    "rsi > 70",                    # Overbought
    "macd < macd_signal",          # MACD crossunder
    "profit >= 4.0",               # Take profit hit
    "loss >= 2.0"                  # Stop loss hit
  ],
  "exit_logic": "OR"  # Any condition triggers exit
}
```

---

## 7. Advanced Settings

### Signal Frequency

```python
{
  "check_interval": 60,           # Check every 60 seconds
  "min_time_between_trades": 300  # Wait 5 min between trades
}
```

### Notifications

```python
{
  "notifications": {
    "email": true,
    "telegram": true,
    "discord": false,
    
    "notify_on_trade": true,      # Alert on every trade
    "notify_on_error": true,      # Alert on errors
    "notify_on_profit": true,     # Alert when profit target hit
    "notify_on_loss": true        # Alert when stop loss hit
  }
}
```

### Logging & Debug

```python
{
  "log_level": "INFO",            # DEBUG, INFO, WARNING, ERROR
  "save_trade_history": true,
  "save_indicator_values": true,
  "debug_mode": false             # Enable for development
}
```

### Backtesting Configuration

```python
{
  "backtest_config": {
    "start_date": "2024-01-01",
    "end_date": "2024-10-01",
    "initial_balance": 10000,
    "commission": 0.001,          # 0.1% per trade
    "slippage": 0.0005           # 0.05% slippage
  }
}
```

---

## 📝 Complete Configuration Example

### Conservative SPOT Bot

```python
{
  # Basic Settings
  "name": "Conservative BTC Spot Bot",
  "bot_type": "TECHNICAL",
  "bot_mode": "ACTIVE",
  
  # Trading Config
  "exchange_type": "BINANCE",
  "trading_pair": "BTC/USDT",
  "timeframe": "1h",
  "is_testnet": false,
  
  # Execution
  "buy_order_type": "PERCENTAGE",
  "buy_order_value": 100.0,
  "sell_order_type": "ALL",
  
  # Risk Management
  "risk_config": {
    "stop_loss_percent": 3.0,
    "take_profit_percent": 6.0,
    "max_position_size": 500.0,
    "risk_per_trade": 1.0,
    "max_open_positions": 1
  },
  
  # Strategy
  "strategy_config": {
    "indicators": {
      "rsi": {"period": 14},
      "ema": {"periods": [50, 200]}
    },
    "entry_conditions": [
      "rsi < 40",
      "close > ema_200"
    ],
    "exit_conditions": [
      "rsi > 70",
      "profit >= 6.0"
    ]
  }
}
```

### Aggressive FUTURES Bot

```python
{
  # Basic Settings
  "name": "Aggressive ETH Futures Bot",
  "bot_type": "FUTURES",
  "bot_mode": "ACTIVE",
  
  # Trading Config
  "exchange_type": "BYBIT",
  "trading_pair": "ETH/USDT",
  "timeframe": "15m",
  
  # Leverage
  "leverage": 10,
  "leverage_type": "ISOLATED",
  
  # Multi-Pair
  "secondary_trading_pairs": [
    "BTC/USDT",
    "SOL/USDT"
  ],
  
  # Risk Management
  "risk_config": {
    "stop_loss_percent": 1.5,
    "take_profit_percent": 3.0,
    "trailing_stop": true,
    "trailing_stop_percent": 0.8,
    "max_position_size": 2000.0,
    "risk_per_trade": 2.0,
    "max_daily_loss": 5.0
  }
}
```

### LLM-Powered Bot

```python
{
  # Basic Settings
  "name": "AI Trading Bot",
  "bot_type": "LLM",
  "bot_mode": "ACTIVE",
  
  # LLM Config
  "llm_provider_id": 123,
  "prompt_template_id": 456,
  "llm_config": {
    "analysis_frequency": "1h",
    "min_confidence": 75
  },
  
  # Trading Config
  "exchange_type": "BINANCE",
  "trading_pair": "BTC/USDT",
  
  # Risk (AI-controlled)
  "risk_management_mode": "AI_PROMPT",
  "max_position_size": 1000.0
}
```

---

## 🎯 Configuration Best Practices

### For Beginners

```python
✅ Use:
- SPOT trading (no leverage)
- Single pair
- Conservative risk (1% per trade)
- Clear stop losses (2-3%)
- Start with testnet

❌ Avoid:
- Leverage
- Multi-pair trading
- High risk per trade
- No stop losses
```

### For Intermediate

```python
✅ Use:
- Low leverage (3-5x) if using futures
- 2-3 pairs max
- Moderate risk (1-2% per trade)
- Trailing stops
- Backtest thoroughly

❌ Avoid:
- >10x leverage
- >5 pairs simultaneously
- >2% risk per trade
```

### For Advanced

```python
✅ Use:
- Leverage up to 20x (carefully)
- Multi-pair strategies
- Dynamic position sizing
- Advanced risk controls
- AI-driven decisions

❌ Avoid:
- >50x leverage (extreme risk)
- Ignoring risk management
- Over-optimization
```

---

## 🆘 Common Configuration Mistakes

### Mistake #1: No Stop Loss
```python
❌ Bad:
{
  "stop_loss_percent": null  # No protection!
}

✅ Good:
{
  "stop_loss_percent": 2.0,
  "trailing_stop": true
}
```

### Mistake #2: Over-Leveraged
```python
❌ Bad:
{
  "leverage": 100,
  "risk_per_trade": 5.0  # Recipe for disaster
}

✅ Good:
{
  "leverage": 5,
  "leverage_type": "ISOLATED",
  "risk_per_trade": 1.0
}
```

### Mistake #3: Too Many Pairs
```python
❌ Bad:
{
  "secondary_trading_pairs": [
    "ETH/USDT", "BNB/USDT", "SOL/USDT",
    "MATIC/USDT", "AVAX/USDT", "DOT/USDT",
    ... 20 more pairs
  ]
}

✅ Good:
{
  "secondary_trading_pairs": [
    "ETH/USDT",
    "BNB/USDT"
  ]
}
```

---

**Next**: [LLM Integration Guide →](./04-llm-integration.md)

