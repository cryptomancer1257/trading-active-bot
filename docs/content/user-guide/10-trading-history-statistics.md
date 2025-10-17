# 📊 Trading History & Statistics

Learn how to view, analyze, and understand your trading performance in QuantumForge Studio.

## 📋 Table of Contents

1. [Accessing Trading History](#accessing-trading-history)
2. [Understanding Trade Data](#understanding-trade-data)
3. [Performance Statistics](#performance-statistics)
4. [Profit & Loss Analysis](#profit--loss-analysis)
5. [Exporting Data](#exporting-data)
6. [Advanced Analytics](#advanced-analytics)

---

## 1. Accessing Trading History

### Via Web Interface

#### Step 1: Navigate to Bot Details
```
Studio → My Bots → Select Bot → Analytics Tab
```

#### Step 2: View Trading History
```
Analytics → Trading History
├─ All Trades
├─ Open Positions
├─ Closed Positions
└─ Pending Orders
```

#### Step 3: Filter and Search
```
Date Range: [Select period]
├─ Last 24 hours
├─ Last 7 days
├─ Last 30 days
├─ Last 3 months
└─ Custom range

Trade Status:
├─ All trades
├─ Profitable only
├─ Losses only
└─ Open positions

Trading Pair:
├─ All pairs
├─ BTC/USDT
├─ ETH/USDT
└─ Custom filter
```

### Via API

```python
import requests

# Get trading history
response = requests.get(
    "https://quantumforge.cryptomancer.ai/api/bots/{bot_id}/trades",
    headers={"Authorization": f"Bearer {YOUR_API_TOKEN}"},
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "status": "closed",
        "limit": 100
    }
)

trades = response.json()
print(f"Found {len(trades)} trades")
```

---

## 2. Understanding Trade Data

### Trade Information

Each trade record contains:

#### Basic Information
```
Trade ID: #12345
Timestamp: 2024-01-15 14:30:25 UTC
Trading Pair: BTC/USDT
Side: BUY / SELL
Type: MARKET / LIMIT / STOP
```

#### Execution Details
```
Quantity: 0.1 BTC
Price: $42,350.00
Total Value: $4,235.00
Fee: $4.24 (0.1%)
Exchange: Binance
```

#### Performance Data
```
Entry Price: $42,350.00
Exit Price: $43,200.00
P&L: +$85.00 (+2.01%)
Duration: 2h 15m
```

### Trade Status Types

| Status | Description | Color |
|--------|-------------|-------|
| **OPEN** | Position is active | 🟢 Green |
| **CLOSED** | Position completed | 🔵 Blue |
| **CANCELLED** | Order was cancelled | 🟡 Yellow |
| **FAILED** | Order failed to execute | 🔴 Red |
| **PENDING** | Order waiting to fill | 🟠 Orange |

---

## 3. Performance Statistics

### Key Metrics

#### Profit & Loss
```
Total P&L: +$1,250.50
Win Rate: 68.5%
Average Win: +$45.20
Average Loss: -$28.50
Profit Factor: 2.15
```

#### Trading Activity
```
Total Trades: 156
Winning Trades: 107
Losing Trades: 49
Open Positions: 3
Cancelled Orders: 12
```

#### Risk Metrics
```
Maximum Drawdown: -$450.00 (-8.5%)
Sharpe Ratio: 1.85
Sortino Ratio: 2.34
Calmar Ratio: 2.78
```

### Performance Breakdown

#### By Time Period
```
Today: +$125.50 (5 trades)
This Week: +$450.20 (23 trades)
This Month: +$1,250.50 (156 trades)
All Time: +$3,450.80 (1,234 trades)
```

#### By Trading Pair
```
BTC/USDT: +$850.30 (45 trades)
ETH/USDT: +$320.20 (32 trades)
SOL/USDT: +$180.00 (28 trades)
Other: +$100.00 (51 trades)
```

#### By Strategy
```
Trend Following: +$650.20 (78 trades)
Mean Reversion: +$420.30 (45 trades)
Breakout: +$180.00 (33 trades)
```

---

## 4. Profit & Loss Analysis

### P&L Components

#### Realized P&L
```
Closed Positions Only
├─ Profitable trades: +$2,450.80
├─ Losing trades: -$1,200.30
└─ Net realized: +$1,250.50
```

#### Unrealized P&L
```
Open Positions Only
├─ Current value: $4,235.00
├─ Entry value: $4,150.00
└─ Unrealized gain: +$85.00
```

#### Total P&L
```
Realized + Unrealized
├─ Realized P&L: +$1,250.50
├─ Unrealized P&L: +$85.00
└─ Total P&L: +$1,335.50
```

### P&L Visualization

#### Daily P&L Chart
```
Jan 2024
├─ Day 1: +$45.20
├─ Day 2: -$12.50
├─ Day 3: +$78.90
├─ Day 4: +$23.40
└─ Day 5: -$8.70
```

#### Cumulative P&L
```
Starting Balance: $10,000.00
├─ After 1 week: $10,450.20
├─ After 1 month: $11,250.50
├─ After 3 months: $12,850.30
└─ Current: $13,335.50
```

---

## 5. Exporting Data

### Export Formats

#### CSV Export
```
File: trading_history_2024-01.csv
Columns:
├─ Date/Time
├─ Trading Pair
├─ Side (Buy/Sell)
├─ Quantity
├─ Price
├─ Total Value
├─ Fee
├─ P&L
└─ Status
```

#### JSON Export
```json
{
  "trades": [
    {
      "id": "12345",
      "timestamp": "2024-01-15T14:30:25Z",
      "pair": "BTC/USDT",
      "side": "BUY",
      "quantity": 0.1,
      "price": 42350.00,
      "total": 4235.00,
      "fee": 4.24,
      "pnl": 85.00,
      "status": "CLOSED"
    }
  ],
  "summary": {
    "total_trades": 156,
    "total_pnl": 1250.50,
    "win_rate": 68.5
  }
}
```

### Export Options

#### Date Range
```
├─ Last 24 hours
├─ Last 7 days
├─ Last 30 days
├─ Last 3 months
├─ Last year
└─ Custom range
```

#### Data Filters
```
├─ All trades
├─ Profitable trades only
├─ Losing trades only
├─ Open positions only
├─ Specific trading pairs
└─ Specific strategies
```

---

## 6. Advanced Analytics

### Performance Analytics

#### Risk-Adjusted Returns
```
Sharpe Ratio: 1.85
├─ Risk-free rate: 2.5%
├─ Portfolio return: 15.2%
├─ Portfolio volatility: 6.8%
└─ Risk-adjusted return: 1.85

Sortino Ratio: 2.34
├─ Downside deviation: 4.2%
├─ Excess return: 12.7%
└─ Downside risk-adjusted: 2.34
```

#### Drawdown Analysis
```
Maximum Drawdown: -$450.00 (-8.5%)
├─ Peak: $5,300.00
├─ Trough: $4,850.00
├─ Recovery time: 12 days
└─ Current drawdown: -$150.00 (-2.8%)
```

### Trading Pattern Analysis

#### Trade Frequency
```
Average trades per day: 5.2
├─ Most active day: Monday (7.8 trades)
├─ Least active day: Sunday (2.1 trades)
├─ Peak hours: 14:00-16:00 UTC
└─ Quiet hours: 02:00-06:00 UTC
```

#### Win/Loss Streaks
```
Longest winning streak: 8 trades
Longest losing streak: 4 trades
Average winning streak: 2.3 trades
Average losing streak: 1.8 trades
```

### Market Condition Analysis

#### Performance by Market Conditions
```
Bull Market: +$850.20 (45 trades, 78% win rate)
Bear Market: -$120.50 (23 trades, 35% win rate)
Sideways Market: +$520.80 (88 trades, 65% win rate)
```

#### Volatility Impact
```
High Volatility: +$320.40 (32 trades, 72% win rate)
Low Volatility: +$180.20 (45 trades, 58% win rate)
Medium Volatility: +$750.90 (79 trades, 68% win rate)
```

---

## 🎯 Key Takeaways

### What to Monitor

#### Daily
- ✅ Check open positions
- ✅ Review new trades
- ✅ Monitor P&L changes
- ✅ Check for errors or failures

#### Weekly
- ✅ Analyze win rate trends
- ✅ Review risk metrics
- ✅ Check drawdown levels
- ✅ Optimize strategy parameters

#### Monthly
- ✅ Comprehensive performance review
- ✅ Compare to benchmarks
- ✅ Adjust risk management
- ✅ Plan strategy improvements

### Red Flags to Watch

#### Performance Issues
```
❌ Win rate below 50%
❌ Average loss > average win
❌ Maximum drawdown > 20%
❌ Sharpe ratio < 1.0
```

#### Risk Issues
```
❌ Too many open positions
❌ High correlation between trades
❌ Excessive leverage usage
❌ Poor risk-adjusted returns
```

---

## 🎯 Next Steps

Now that you understand your trading performance:

**Continue to**: [Risk Management →](./08-risk-management.md)

**Or**: [Strategy Optimization →](./05-prompt-engineering.md)

---

## 🆘 Need Help?

### Understanding Your Data

- 📧 **Support**: support@quantumforge.ai
- 💬 **Community**: [Discord Server](https://discord.gg/quantumforge)
- 📖 **Documentation**: [Analytics API Reference](https://docs.quantumforge.ai/analytics)

### Performance Optimization

- 🎯 **Strategy Review**: [Bot Configuration](./03-bot-configuration.md)
- 📈 **Backtesting**: [Backtesting Guide](./09-backtesting.md)
- 🛡️ **Risk Management**: [Risk Management](./08-risk-management.md)

---

**Ready to optimize your strategy?** → [Next: Risk Management](./08-risk-management.md)
