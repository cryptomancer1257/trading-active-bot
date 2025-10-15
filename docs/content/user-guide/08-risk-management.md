# 🛡️ Risk Management Guide

Master risk management to protect your capital and ensure long-term trading success.

## 📋 Table of Contents

1. [Why Risk Management Matters](#why-risk-management-matters)
2. [Core Risk Principles](#core-risk-principles)
3. [Position Sizing](#position-sizing)
4. [Stop Loss & Take Profit](#stop-loss-and-take-profit)
5. [Portfolio Risk Management](#portfolio-risk-management)
6. [AI-Driven Risk Management](#ai-driven-risk-management)
7. [Risk Monitoring](#risk-monitoring)

---

## 1. Why Risk Management Matters

### The Statistics

```
Without Risk Management:
- 90% of traders lose money
- Average loss: -50% to -100%
- Survival time: 3-6 months

With Proper Risk Management:
- 60% of traders profit
- Average loss: -5% to -15%
- Survival time: 5+ years
```

### The Golden Rule

**"Protect your capital first, profits come second"**

```
Example:
$10,000 capital

Scenario A (No risk management):
- 10% loss = $9,000
- Need 11% gain to recover

Scenario B (50% loss):
- $5,000 remaining
- Need 100% gain to recover! 😱

Scenario C (Proper risk, -10% over year):
- $9,000 remaining
- Manageable recovery
```

---

## 2. Core Risk Principles

### Principle 1: Never Risk More Than You Can Afford to Lose

```python
# Calculate safe capital
total_savings = 50000
emergency_fund = 10000
living_expenses = 30000

safe_trading_capital = 50000 - 10000 - 30000 = 10000

# Only trade with $10,000 ✅
```

### Principle 2: The 1-2% Rule

**Never risk more than 1-2% of your capital on a single trade**

```python
capital = 10000
risk_per_trade = 0.01  # 1%

max_risk = 10000 * 0.01 = $100 per trade

# Even if you lose 10 trades in a row:
# Loss = $100 × 10 = $1,000 (10% of capital)
# Remaining: $9,000
# Still in the game! ✅
```

### Principle 3: Risk/Reward Ratio

**Minimum 1:2 ratio (risk $1 to make $2)**

```python
Entry: $100
Stop Loss: $98 (-2% or -$2 risk)
Take Profit: $104 (+4% or +$4 reward)

Risk/Reward = 4 / 2 = 2:1 ✅

# Win Rate Math:
# With 2:1 R:R, you need only 40% win rate to profit!
# 10 trades: 4 wins ($16) - 6 losses ($12) = +$4 profit
```

### Principle 4: Diversification

```python
# Don't put all eggs in one basket

❌ Bad:
all_capital = 10000
btc_position = 10000  # 100% in BTC

✅ Good:
btc_position = 4000   # 40%
eth_position = 3000   # 30%
alt_positions = 2000  # 20%
cash_reserve = 1000   # 10%
```

---

## 3. Position Sizing

### Fixed Dollar Amount

Simple but not optimal:

```python
{
  "position_sizing": "FIXED",
  "position_size": 1000  # Always trade $1000
}

# Problem: Doesn't scale with capital growth
```

### Percentage-Based

Recommended approach:

```python
{
  "position_sizing": "PERCENTAGE",
  "position_percent": 10  # 10% of current capital
}

# Example:
Capital $10,000 → Position = $1,000
Capital grows to $12,000 → Position = $1,200 ✅
Capital drops to $8,000 → Position = $800 ✅
```

### Risk-Based (Kelly Criterion)

Advanced, optimal sizing:

```python
def calculate_position_size(capital, risk_percent, stop_loss_percent):
    """
    Calculate position size based on risk per trade
    """
    risk_amount = capital * (risk_percent / 100)
    position_size = risk_amount / (stop_loss_percent / 100)
    return position_size

# Example:
capital = 10000
risk_percent = 1.0      # Risk 1% ($100)
stop_loss_percent = 2.0 # Stop loss at -2%

position = calculate_position_size(10000, 1.0, 2.0)
# = $100 / 0.02 = $5,000

# Check:
# Position: $5,000
# Stop loss: -2% of $5,000 = -$100 ✅
# Risk: Exactly 1% of capital
```

**Configuration:**

```python
{
  "position_sizing": "RISK_BASED",
  "risk_per_trade": 1.0,        # Risk 1% of capital
  "max_position_size": 5000,    # Safety cap
  "min_position_size": 100      # Minimum trade size
}
```

### Volatility-Adjusted Sizing

Reduce position size in volatile markets:

```python
{
  "position_sizing": "VOLATILITY_ADJUSTED",
  "base_position_percent": 10,
  "volatility_multiplier": true
}

# Low volatility (ATR 2%):
position = 10% * 1.0 = 10%

# High volatility (ATR 5%):
position = 10% * 0.6 = 6%  # Reduced
```

---

## 4. Stop Loss & Take Profit

### Types of Stop Loss

#### 1. Percentage-Based

```python
{
  "stop_loss_type": "PERCENTAGE",
  "stop_loss_percent": 2.0  # Exit at -2%
}

# Example:
Entry: $100
Stop Loss: $98
```

#### 2. ATR-Based (Volatility)

```python
{
  "stop_loss_type": "ATR",
  "atr_multiplier": 2.0  # 2× ATR
}

# Example:
Entry: $100
ATR: $1.50
Stop Loss: $100 - (2 × $1.50) = $97
```

#### 3. Support/Resistance

```python
{
  "stop_loss_type": "TECHNICAL",
  "place_below_support": true,
  "buffer_percent": 0.5  # 0.5% below support
}

# Example:
Entry: $100
Support: $98
Stop Loss: $98 - 0.5% = $97.51
```

#### 4. Trailing Stop

Locks in profits as price moves in your favor:

```python
{
  "stop_loss_type": "TRAILING",
  "initial_stop_percent": 2.0,
  "trailing_percent": 1.0
}

# Example:
Entry: $100
Initial Stop: $98 (-2%)

Price → $102:
  Stop trails to: $101 (-1%)
  
Price → $105:
  Stop trails to: $104
  Profit locked! ✅

Price → $103:
  Stop still at $104
  Exit triggered
  Profit: +4% ✅
```

### Take Profit Strategies

#### 1. Fixed Target

```python
{
  "take_profit_type": "FIXED",
  "take_profit_percent": 4.0  # Exit at +4%
}
```

#### 2. Multiple Targets

```python
{
  "take_profit_type": "SCALED",
  "targets": [
    {"percent": 2.0, "size": 33},  # Sell 33% at +2%
    {"percent": 4.0, "size": 33},  # Sell 33% at +4%
    {"percent": 6.0, "size": 34}   # Sell rest at +6%
  ]
}
```

#### 3. Resistance-Based

```python
{
  "take_profit_type": "RESISTANCE",
  "take_at_resistance": true,
  "buffer_percent": 0.5  # Exit 0.5% before resistance
}
```

---

## 5. Portfolio Risk Management

### Maximum Exposure Limits

```python
{
  # Per-Position Limits
  "max_position_size": 1000,
  "max_positions": 3,
  
  # Total Portfolio Limits
  "max_total_exposure": 3000,      # Max $3k in trades
  "max_leverage_exposure": 10000,  # Max $10k with leverage
  "max_portfolio_risk": 5.0        # Max 5% total risk
}
```

### Correlation Management

Avoid over-exposure to correlated assets:

```python
{
  "correlation_limits": {
    "max_correlated_positions": 2,
    "max_correlation": 0.7,
    "check_interval": "1h"
  }
}

# Example:
# Can't open BTC + ETH + BNB (all correlated)
# Allowed: BTC + SOL (lower correlation)
```

### Drawdown Limits

```python
{
  "drawdown_limits": {
    "max_daily_loss": 2.0,      # Stop if -2% today
    "max_weekly_loss": 5.0,     # Stop if -5% this week
    "max_monthly_loss": 10.0,   # Stop if -10% this month
    "max_peak_drawdown": 15.0   # Stop if -15% from peak
  },
  
  "actions": {
    "on_daily_limit": "STOP_TRADING",
    "on_weekly_limit": "REDUCE_SIZE",
    "on_monthly_limit": "PAUSE_BOT",
    "recovery_threshold": 0.5  # Resume at +0.5%
  }
}
```

### Time-Based Limits

```python
{
  "time_limits": {
    "max_trades_per_day": 10,
    "max_trades_per_week": 30,
    "min_time_between_trades": 300,  # 5 minutes
    "cooldown_after_loss": 1800,     # 30 min after loss
    "trading_hours": {
      "enabled": true,
      "start": "09:00",
      "end": "17:00",
      "timezone": "UTC"
    }
  }
}
```

---

## 6. AI-Driven Risk Management

### Dynamic Risk Adjustment

Let AI adjust risk based on market conditions:

```python
{
  "risk_management_mode": "AI_PROMPT",
  "llm_provider_id": 123,
  "dynamic_risk": {
    "adjust_stop_loss": true,
    "adjust_position_size": true,
    "adjust_take_profit": true
  }
}
```

**AI Prompt Example:**

```markdown
Analyze current market conditions and recommend risk parameters:

Market Data:
- BTC Price: ${{price}}
- Volatility (ATR): {{atr}}
- Volume: {{volume}}
- Trend Strength: {{trend_strength}}
- Market Regime: {{market_regime}}

Current Settings:
- Position Size: $1000
- Stop Loss: -2%
- Take Profit: +4%

Recommend adjusted parameters based on:
1. Current volatility
2. Trend strength
3. Market regime (trending/ranging)

Response format:
{
  "position_size": number,
  "stop_loss_percent": number,
  "take_profit_percent": number,
  "confidence": 0-100,
  "reasoning": "brief explanation"
}
```

### Sentiment-Based Risk

```python
{
  "sentiment_risk_adjustment": {
    "enabled": true,
    "fear_greed_index": true,
    
    "rules": {
      "extreme_fear": {
        "action": "REDUCE_SIZE",
        "multiplier": 0.5
      },
      "extreme_greed": {
        "action": "TIGHTEN_STOPS",
        "stop_loss_percent": 1.5
      }
    }
  }
}
```

---

## 7. Risk Monitoring

### Real-Time Alerts

```python
{
  "risk_alerts": {
    "notify_on": [
      "DAILY_LOSS_50_PERCENT",   # 50% of daily limit
      "POSITION_STOPPED_OUT",
      "MAX_POSITIONS_REACHED",
      "CORRELATION_TOO_HIGH",
      "VOLATILITY_SPIKE"
    ],
    
    "channels": ["EMAIL", "TELEGRAM", "SMS"]
  }
}
```

### Risk Dashboard

Monitor key metrics:

```
┌─────────────────────────────────────────┐
│  Risk Dashboard                         │
├─────────────────────────────────────────┤
│  Daily P&L:        -$45 / -$200 limit   │
│  Weekly P&L:       +$120 / -$500 limit  │
│  Total Exposure:   $2,500 / $3,000 max  │
│  Open Positions:   2 / 3 max            │
│  Portfolio Risk:   2.5% / 5% max        │
│  Drawdown:         -3.2% / -15% max     │
│                                         │
│  Status: ✅ Healthy                     │
└─────────────────────────────────────────┘
```

### Risk Reports

```python
# Weekly Risk Report
GET /risk/reports/weekly

{
  "week": "2024-W41",
  "total_trades": 25,
  "winning_trades": 16,
  "losing_trades": 9,
  "win_rate": 64,
  
  "risk_metrics": {
    "avg_risk_per_trade": 1.2,
    "max_risk_per_trade": 1.5,
    "total_risk_taken": 30.0,
    "total_capital_at_risk": 300
  },
  
  "largest_loss": -15,
  "largest_win": 40,
  "avg_win": 25,
  "avg_loss": -12,
  
  "risk_violations": 0,
  "near_misses": 2
}
```

---

## 📊 Risk Configuration Templates

### Ultra-Conservative

```python
{
  "risk_profile": "ULTRA_CONSERVATIVE",
  
  "position_sizing": {
    "type": "RISK_BASED",
    "risk_per_trade": 0.5  # 0.5% risk
  },
  
  "stop_loss": {
    "type": "PERCENTAGE",
    "percent": 1.0  # Tight 1% stop
  },
  
  "take_profit": {
    "type": "FIXED",
    "percent": 3.0  # 3:1 R:R
  },
  
  "limits": {
    "max_positions": 2,
    "max_daily_loss": 1.0,
    "max_total_exposure": 2000
  }
}
```

### Balanced

```python
{
  "risk_profile": "BALANCED",
  
  "position_sizing": {
    "type": "RISK_BASED",
    "risk_per_trade": 1.0
  },
  
  "stop_loss": {
    "type": "TRAILING",
    "initial_percent": 2.0,
    "trailing_percent": 1.0
  },
  
  "take_profit": {
    "type": "SCALED",
    "targets": [
      {"percent": 2, "size": 50},
      {"percent": 4, "size": 50}
    ]
  },
  
  "limits": {
    "max_positions": 3,
    "max_daily_loss": 2.0,
    "max_total_exposure": 5000
  }
}
```

### Aggressive

```python
{
  "risk_profile": "AGGRESSIVE",
  
  "position_sizing": {
    "type": "RISK_BASED",
    "risk_per_trade": 2.0
  },
  
  "leverage": {
    "enabled": true,
    "max_leverage": 10,
    "type": "ISOLATED"
  },
  
  "stop_loss": {
    "type": "ATR",
    "multiplier": 1.5
  },
  
  "take_profit": {
    "type": "RESISTANCE",
    "take_at_resistance": true
  },
  
  "limits": {
    "max_positions": 5,
    "max_daily_loss": 5.0,
    "max_total_exposure": 10000
  }
}
```

---

## 🎯 Risk Management Checklist

### Before Every Trade

- [ ] Position size ≤ 10% of capital?
- [ ] Risk per trade ≤ 1-2%?
- [ ] Stop loss set?
- [ ] Take profit target defined?
- [ ] Risk/reward ratio ≥ 1:2?
- [ ] Total exposure within limits?
- [ ] Not over-leveraged?

### Daily

- [ ] Check daily P&L vs limit
- [ ] Review open positions
- [ ] Monitor market volatility
- [ ] Check correlation between positions
- [ ] Adjust stops if needed

### Weekly

- [ ] Review win/loss ratio
- [ ] Analyze risk-adjusted returns
- [ ] Check maximum drawdown
- [ ] Evaluate risk parameter effectiveness
- [ ] Adjust strategy if needed

---

## 🆘 Emergency Procedures

### When Things Go Wrong

#### Scenario 1: Hit Daily Loss Limit

```python
Action Plan:
1. STOP all trading immediately
2. Close all open positions (optional)
3. Review what went wrong
4. Don't trade again until next day
5. Analyze and adjust strategy
```

#### Scenario 2: Flash Crash / Black Swan

```python
Emergency Protocol:
1. Activate emergency stop-loss
2. Close high-risk positions
3. Reduce leverage to 1x
4. Move to stablecoins
5. Wait for market stabilization
```

#### Scenario 3: Exchange Issues

```python
Contingency Plan:
1. Have accounts on multiple exchanges
2. Keep some funds in cold wallet
3. Don't keep more than needed on exchange
4. Have manual override capability
```

---

**Next**: [Backtesting Guide →](./09-backtesting.md)

