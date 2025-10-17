# 📈 Backtesting Guide

Learn how to test your trading strategies on historical data in QuantumForge Studio. This guide covers everything from setting up backtests to analyzing results and transitioning to live trading.

## 📋 Table of Contents

1. [What is Backtesting?](#what-is-backtesting)
2. [Setting Up a Backtest](#setting-up-a-backtest)
3. [Interpreting Results](#interpreting-results)
4. [Avoiding Common Pitfalls](#avoiding-common-pitfalls)
5. [Walk-Forward Analysis](#walk-forward-analysis)
6. [From Backtest to Live](#from-backtest-to-live)

---

## 1. What is Backtesting?

### Overview

**Backtesting** simulates how your trading strategy would have performed using historical market data.

```
Historical Data → Your Strategy → Performance Metrics
    (Past)          (Rules)         (Would-be Results)
```

### Why Backtest?

✅ **Validate Strategy** - Does it actually work?
✅ **Estimate Returns** - Expected profit/loss
✅ **Measure Risk** - Maximum drawdown
✅ **Optimize Parameters** - Find best settings
✅ **Build Confidence** - Trade with conviction

### What Backtest Cannot Do

❌ Guarantee future performance
❌ Account for all real-world scenarios
❌ Predict black swan events
❌ Replace live testing

---

## 2. Setting Up a Backtest

### Via Web Interface

1. Go to **My Bots** → Select bot
2. Click **"Backtest"**
3. Configure backtest parameters
4. Run and analyze results

### Basic Configuration

```python
{
  "backtest_config": {
    # Time Period
    "start_date": "2024-01-01",
    "end_date": "2024-10-01",
    
    # Initial Conditions
    "initial_balance": 10000,
    "currency": "USDT",
    
    # Trading Pair
    "trading_pair": "BTC/USDT",
    "timeframe": "1h",
    
    # Costs
    "commission": 0.001,  # 0.1% per trade
    "slippage": 0.0005   # 0.05% slippage
  }
}
```

### Advanced Configuration

```python
{
  "backtest_config": {
    # Data Source
    "data_source": "BINANCE",
    "use_real_orderbook": false,  # Faster but less accurate
    
    # Execution
    "fill_method": "MARKET",  # or "LIMIT"
    "max_open_positions": 3,
    
    # Multi-Pair
    "secondary_pairs": ["ETH/USDT", "BNB/USDT"],
    
    # Risk Management (test different scenarios)
    "scenarios": [
      {
        "name": "Conservative",
        "risk_per_trade": 1.0,
        "stop_loss": 2.0
      },
      {
        "name": "Aggressive",
        "risk_per_trade": 2.0,
        "stop_loss": 1.5
      }
    ]
  }
}
```

### Via API

```python
import requests

response = requests.post(
    "https://api.quantumforge.ai/bots/{bot_id}/backtest",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "start_date": "2024-01-01",
        "end_date": "2024-10-01",
        "initial_balance": 10000,
        "trading_pair": "BTC/USDT",
        "timeframe": "1h"
    }
)

backtest_id = response.json()["backtest_id"]

# Poll for results
results = requests.get(
    f"https://api.quantumforge.ai/backtests/{backtest_id}"
).json()
```

---

## 3. Interpreting Results

### Key Performance Metrics

#### Total Return

```
Total Return = (Final Balance - Initial Balance) / Initial Balance × 100%

Example:
Initial: $10,000
Final: $12,500
Return = (12,500 - 10,000) / 10,000 = 25%
```

#### Annualized Return

```
Annualized Return = (1 + Total Return)^(365/Days) - 1

Example:
Total Return: 25% over 270 days
Annualized = (1.25)^(365/270) - 1 = 34.5%
```

#### Win Rate

```
Win Rate = Winning Trades / Total Trades × 100%

Example:
100 trades: 65 wins, 35 losses
Win Rate = 65 / 100 = 65%
```

#### Profit Factor

```
Profit Factor = Gross Profit / Gross Loss

Example:
Gross Profit: $5,000
Gross Loss: $2,500
Profit Factor = 5,000 / 2,500 = 2.0

Interpretation:
< 1.0 = Losing strategy
1.0 - 1.5 = Breakeven to marginal
1.5 - 2.0 = Good
> 2.0 = Excellent
```

#### Maximum Drawdown

```
Max Drawdown = (Peak Value - Lowest Value) / Peak Value × 100%

Example:
Peak: $12,000
Trough: $10,200
Drawdown = (12,000 - 10,200) / 12,000 = 15%

Interpretation:
< 10% = Low risk
10-20% = Moderate risk
20-30% = High risk
> 30% = Very high risk
```

#### Sharpe Ratio

```
Sharpe Ratio = (Return - Risk-Free Rate) / Standard Deviation

Example:
Annual Return: 25%
Risk-Free Rate: 3%
Std Dev: 15%
Sharpe = (25 - 3) / 15 = 1.47

Interpretation:
< 1.0 = Poor
1.0 - 2.0 = Good
2.0 - 3.0 = Very good
> 3.0 = Excellent
```

### Sample Backtest Report

```
┌───────────────────────────────────────────────┐
│  Backtest Results: BTC Trend Follower         │
├───────────────────────────────────────────────┤
│  Period: 2024-01-01 to 2024-10-01 (274 days) │
│  Pair: BTC/USDT                               │
│  Timeframe: 1h                                │
│  Initial Balance: $10,000                     │
└───────────────────────────────────────────────┘

📊 Performance Metrics
─────────────────────────────────────────────────
Total Return:        +25.5%
Annualized Return:   +34.2%
Final Balance:       $12,550

CAGR:                +34.2%
Sharpe Ratio:        1.85
Sortino Ratio:       2.34
Calmar Ratio:        3.12

📈 Trade Statistics
─────────────────────────────────────────────────
Total Trades:        156
Winning Trades:      102 (65.4%)
Losing Trades:       54 (34.6%)

Avg Win:             +2.8% ($285)
Avg Loss:            -1.2% ($120)
Largest Win:         +8.5% ($850)
Largest Loss:        -2.5% ($250)

Win/Loss Ratio:      2.38
Profit Factor:       2.15
Expectancy:          +$163 per trade

⚠️ Risk Metrics
─────────────────────────────────────────────────
Max Drawdown:        -8.2% ($820)
Max Drawdown Duration: 12 days
Recovery Time:       8 days

Volatility (Daily):  1.8%
Value at Risk (95%): -2.5%
Conditional VaR:     -3.2%

📅 Monthly Breakdown
─────────────────────────────────────────────────
Jan 2024:  +3.2%  (18 trades, 65% win rate)
Feb 2024:  +2.8%  (16 trades, 63% win rate)
Mar 2024:  +4.1%  (20 trades, 70% win rate)
Apr 2024:  -1.5%  (15 trades, 53% win rate)
May 2024:  +3.8%  (19 trades, 68% win rate)
Jun 2024:  +2.5%  (17 trades, 59% win rate)
Jul 2024:  +5.2%  (21 trades, 71% win rate)
Aug 2024:  +1.8%  (14 trades, 57% win rate)
Sep 2024:  +3.6%  (16 trades, 63% win rate)

✅ Verdict: STRONG PERFORMANCE
```

---

## 4. Avoiding Common Pitfalls

### Pitfall 1: Overfitting

**Problem**: Strategy works great in backtest but fails in live trading

```python
# Overfitted Strategy (BAD)
{
  "rsi_period": 13.7,        # Too specific
  "rsi_buy": 29.3,           # Optimized to perfection
  "rsi_sell": 71.8,
  "ema_period": 197.4,       # Not round numbers = overfitted
  "profit_target": 4.27
}

# Robust Strategy (GOOD)
{
  "rsi_period": 14,          # Standard values
  "rsi_buy": 30,             # Round numbers
  "rsi_sell": 70,
  "ema_period": 200,         # Common EMA
  "profit_target": 4.0
}
```

**Solution**: Keep parameters simple and standard

### Pitfall 2: Look-Ahead Bias

**Problem**: Using future data that wouldn't be available in real-time

```python
❌ Bad:
if next_candle.close > current_candle.close:
    buy()  # Can't know next candle in advance!

✅ Good:
if current_candle.close > ema_200:
    buy()  # Using only past data
```

### Pitfall 3: Survivorship Bias

**Problem**: Only testing on currently active pairs

```python
❌ Bad:
Test only on: BTC, ETH, BNB (survivors)

✅ Good:
Test on: BTC, ETH, BNB, + delisted coins
Include failed projects for realistic results
```

### Pitfall 4: Ignoring Transaction Costs

```python
❌ Bad:
{
  "commission": 0,
  "slippage": 0
}
# Results: +50% return (unrealistic!)

✅ Good:
{
  "commission": 0.001,  # 0.1%
  "slippage": 0.0005   # 0.05%
}
# Results: +25% return (realistic)
```

### Pitfall 5: Insufficient Data

```python
❌ Bad:
Backtest period: 1 month (30 days)
Not enough data!

✅ Good:
Backtest period: 6-12 months minimum
Include different market conditions
```

---

## 5. Walk-Forward Analysis

### What is Walk-Forward?

More robust than simple backtest:

```
Traditional Backtest:
├─ Train on ALL data
└─ Test on SAME data (overfitting risk)

Walk-Forward:
├─ Month 1-3: Train
├─ Month 4: Test
├─ Month 2-4: Re-train
├─ Month 5: Test
└─ Repeat...
```

### Implementation

```python
{
  "walk_forward_config": {
    "training_period": 90,   # 90 days training
    "testing_period": 30,    # 30 days testing
    "step_size": 30,         # Move forward 30 days
    "reoptimize": true       # Re-optimize each period
  }
}

# Example timeline:
# Train: Jan-Mar, Test: Apr
# Train: Feb-Apr, Test: May
# Train: Mar-May, Test: Jun
# ...
```

### Interpreting Results

```
Walk-Forward Efficiency = Live Performance / Backtest Performance

Example:
Backtest Return: 30%
Walk-Forward Return: 24%
Efficiency = 24 / 30 = 80%

Interpretation:
> 70% = Good (strategy is robust)
50-70% = Acceptable
< 50% = Overfitted (revise strategy)
```

---

## 6. From Backtest to Live

### Step-by-Step Process

#### Step 1: Backtest (Historical Data)

```python
Period: 12 months
Result: +25% return, 65% win rate
Verdict: Promising ✅
```

#### Step 2: Walk-Forward Analysis

```python
Efficiency: 75%
Consistent across periods: Yes
Verdict: Robust ✅
```

#### Step 3: Paper Trading (Testnet)

```python
Duration: 1 month
Real-time data: Yes
Real money: No
Result: +2.8% (similar to backtest)
Verdict: Ready for live ✅
```

#### Step 4: Live Trading (Small Capital)

```python
Capital: $1,000 (10% of full amount)
Duration: 1 month
Monitor closely
Result: +2.5%
Verdict: Scale up ✅
```

#### Step 5: Full Live Trading

```python
Capital: $10,000 (full amount)
Continue monitoring
Compare live vs backtest results
```

### Tracking Live vs Backtest

```python
GET /bots/{bot_id}/performance/comparison

{
  "backtest": {
    "return": 25.5,
    "win_rate": 65.4,
    "sharpe": 1.85,
    "max_drawdown": 8.2
  },
  
  "live": {
    "return": 22.3,     # Within 10% of backtest ✅
    "win_rate": 63.1,   # Close ✅
    "sharpe": 1.72,     # Acceptable ✅
    "max_drawdown": 9.5 # Slightly worse (normal)
  },
  
  "deviation": {
    "return": -12.5,    # -12.5% deviation
    "overall": "GOOD"   # Within acceptable range
  }
}
```

### When to Stop/Revise

**Red Flags:**

```python
# Stop trading if:
live_return < (backtest_return * 0.5)  # 50% worse
# OR
live_drawdown > (backtest_drawdown * 1.5)  # 50% more drawdown
# OR
live_win_rate < 50  # Below breakeven

# Revise strategy
```

---

## 📊 Backtest Quality Checklist

### Data Quality
- [ ] Sufficient history (6+ months)
- [ ] Multiple market conditions (bull, bear, sideways)
- [ ] Clean data (no gaps, errors)
- [ ] Realistic execution (commission + slippage)

### Methodology
- [ ] No look-ahead bias
- [ ] No survivorship bias
- [ ] Walk-forward tested
- [ ] Multiple timeframes tested

### Results
- [ ] Consistent across periods
- [ ] Win rate >55%
- [ ] Profit factor >1.5
- [ ] Max drawdown <20%
- [ ] Sharpe ratio >1.0

### Risk Assessment
- [ ] Worst-case scenario analyzed
- [ ] Recovery time acceptable
- [ ] Position sizing validated
- [ ] Stop losses tested

---

## 🎯 Next Steps

After successful backtesting:
1. **[Risk Management](./08-risk-management.md)** - Ensure proper risk controls
2. **[Publish to Marketplace](./07-publishing-to-marketplace.md)** - Share your bot
3. **Monitor Performance** - Track live vs backtest

---

**Next**: [FAQ →](./faq.md)

