# 🔄 Multi-Pair Trading Guide

Learn how to trade multiple cryptocurrency pairs simultaneously for better diversification and more opportunities.

## 📋 Table of Contents

1. [What is Multi-Pair Trading?](#what-is-multi-pair-trading)
2. [Benefits & Risks](#benefits-and-risks)
3. [Configuration](#configuration)
4. [Trading Priority](#trading-priority)
5. [Risk Management](#risk-management)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

---

## 1. What is Multi-Pair Trading?

### Overview

Multi-pair trading allows your bot to monitor and trade multiple cryptocurrency pairs simultaneously, increasing opportunities while spreading risk.

```
Single Pair:          Multi-Pair:
┌──────────┐         ┌──────────┐ ┌──────────┐ ┌──────────┐
│ BTC/USDT │         │ BTC/USDT │ │ ETH/USDT │ │ SOL/USDT │
└────┬─────┘         └────┬─────┘ └────┬─────┘ └────┬─────┘
     │                    └──────┬──────┴──────┬──────┘
     ▼                           ▼             
  1 Trade                  3 Trades Possible
  Opportunity              More Opportunities!
```

### How It Works

1. **Primary Pair**: Main trading pair (highest priority)
2. **Secondary Pairs**: Additional pairs (trade when primary is busy)

```python
{
  "trading_pair": "BTC/USDT",           # Primary
  "secondary_trading_pairs": [          # Secondary
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT"
  ]
}
```

---

## 2. Benefits & Risks

### Benefits ✅

#### 1. Diversification
- Spread risk across multiple assets
- Not dependent on single pair performance

#### 2. More Opportunities
- Trade different market conditions
- Capture moves in multiple pairs

#### 3. Better Capital Efficiency
- Use idle capital on secondary pairs
- Maximize trading frequency

#### 4. Reduced Correlation Risk
- If BTC consolidates, ETH might trend
- Different pairs, different opportunities

### Risks ⚠️

#### 1. Increased Complexity
- More positions to monitor
- More complex risk management

#### 2. Higher Capital Requirements
- Need sufficient balance for multiple positions
- Reserve for margin requirements (futures)

#### 3. Correlation Risk
- Crypto pairs often move together
- Not true diversification like stocks/bonds

#### 4. Higher Fees
- More trades = more commissions
- Need higher win rate to compensate

---

## 3. Configuration

### Basic Setup

```python
{
  # Primary pair (highest priority)
  "trading_pair": "BTC/USDT",
  
  # Secondary pairs (optional)
  "secondary_trading_pairs": [
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT"
  ],
  
  # Position limits
  "max_open_positions": 3,  # Max 3 pairs open simultaneously
  "max_capital_per_pair": 1000  # $1000 max per pair
}
```

### Pair Selection Criteria

**Choose pairs with:**
- ✅ High liquidity (>$50M daily volume)
- ✅ Low correlation (different market behaviors)
- ✅ Clear trends or patterns
- ✅ Available on your exchange

**Recommended Combinations:**

```python
# Large Cap Diversification
{
  "trading_pair": "BTC/USDT",
  "secondary_trading_pairs": [
    "ETH/USDT",
    "BNB/USDT"
  ]
}

# DeFi Focus
{
  "trading_pair": "UNI/USDT",
  "secondary_trading_pairs": [
    "AAVE/USDT",
    "LINK/USDT",
    "SNX/USDT"
  ]
}

# Layer 1 Platforms
{
  "trading_pair": "ETH/USDT",
  "secondary_trading_pairs": [
    "SOL/USDT",
    "AVAX/USDT",
    "DOT/USDT"
  ]
}
```

### Advanced Configuration

```python
{
  "trading_pair": "BTC/USDT",
  "secondary_trading_pairs": [
    "ETH/USDT",
    "BNB/USDT"
  ],
  
  # Pair-specific settings
  "pair_configs": {
    "BTC/USDT": {
      "max_position_size": 2000,
      "stop_loss_percent": 2.0,
      "leverage": 5
    },
    "ETH/USDT": {
      "max_position_size": 1500,
      "stop_loss_percent": 2.5,
      "leverage": 3
    },
    "BNB/USDT": {
      "max_position_size": 1000,
      "stop_loss_percent": 3.0,
      "leverage": 3
    }
  },
  
  # Global limits
  "total_max_positions": 3,
  "total_max_capital": 4000
}
```

---

## 4. Trading Priority

### Priority System

Bot trades pairs in priority order:

```
Priority 1: Primary Pair (BTC/USDT)
  ↓ If no signal or position full
Priority 2: Secondary Pair #1 (ETH/USDT)
  ↓ If no signal or position full
Priority 3: Secondary Pair #2 (BNB/USDT)
  ↓ And so on...
```

### Example Flow

```python
# Scenario: Bot checking for trades

Step 1: Check BTC/USDT
  → Signal found → Execute trade ✅
  
Step 2: Check ETH/USDT
  → BTC position already open
  → ETH signal found → Execute trade ✅
  
Step 3: Check BNB/USDT
  → Max positions (2) reached
  → Skip ❌
  
Step 4: BTC position closes
  → Now can trade BNB if signal appears
```

### Manual Priority Override

```python
{
  "trading_priority": [
    "ETH/USDT",   # Trade ETH first
    "BTC/USDT",   # Then BTC
    "SOL/USDT"    # Then SOL
  ]
}
```

---

## 5. Risk Management

### Position Sizing

Allocate capital wisely across pairs:

```python
# Method 1: Equal Allocation
total_capital = 10000
pairs = 4
per_pair = 10000 / 4 = 2500

{
  "max_capital_per_pair": 2500
}

# Method 2: Weighted Allocation
{
  "capital_allocation": {
    "BTC/USDT": 0.4,  # 40% of capital
    "ETH/USDT": 0.3,  # 30%
    "BNB/USDT": 0.2,  # 20%
    "SOL/USDT": 0.1   # 10%
  }
}

# Method 3: Dynamic (based on volatility)
{
  "dynamic_sizing": true,
  "volatility_adjustment": true
}
```

### Global Risk Limits

```python
{
  # Per-pair limits
  "max_capital_per_pair": 1000,
  "max_open_positions": 3,
  
  # Global limits
  "total_max_exposure": 3000,      # Max $3000 across all pairs
  "max_portfolio_risk": 5.0,       # Max 5% portfolio risk
  
  # Stop conditions
  "max_daily_loss": 200,           # Stop all if -$200 daily
  "max_concurrent_losses": 3,      # Stop if 3 pairs losing
  
  # Correlation limits
  "max_correlated_positions": 2    # Max 2 highly correlated pairs
}
```

### Pair Correlation

Monitor correlation to avoid over-exposure:

```python
# High correlation pairs (often move together)
Avoid: BTC + ETH + BNB together
Better: BTC + SOL + MATIC (lower correlation)

# Correlation Matrix Example
       BTC   ETH   BNB   SOL   MATIC
BTC    1.0   0.85  0.78  0.65  0.55
ETH    0.85  1.0   0.82  0.70  0.60
BNB    0.78  0.82  1.0   0.68  0.58
SOL    0.65  0.70  0.68  1.0   0.45
MATIC  0.55  0.60  0.58  0.45  1.0
```

Configure correlation limits:

```python
{
  "max_correlation": 0.7,  # Avoid pairs with >0.7 correlation
  "correlation_check": true
}
```

---

## 6. Best Practices

### Do's ✅

#### 1. Start Small
```python
# Begin with 2-3 pairs
{
  "trading_pair": "BTC/USDT",
  "secondary_trading_pairs": [
    "ETH/USDT"
  ]
}
```

#### 2. Choose Liquid Pairs
```python
# Good pairs (high volume)
pairs = [
  "BTC/USDT",
  "ETH/USDT",
  "BNB/USDT"
]

# Avoid low volume pairs
avoid = [
  "OBSCURECOIN/USDT"  # Low liquidity = wide spreads
]
```

#### 3. Monitor Correlation
```python
{
  "enable_correlation_monitoring": true,
  "rebalance_on_high_correlation": true
}
```

#### 4. Set Global Limits
```python
{
  "total_max_positions": 3,
  "total_max_exposure": 5000,
  "max_daily_trades": 20  # Across all pairs
}
```

### Don'ts ❌

#### 1. Don't Over-Diversify
```python
❌ Bad: Trading 20 pairs
✅ Good: Trading 2-5 pairs
```

#### 2. Don't Ignore Correlation
```python
❌ Bad: BTC + ETH + BNB + LTC (all correlated)
✅ Good: BTC + SOL + MATIC (lower correlation)
```

#### 3. Don't Split Capital Too Thin
```python
❌ Bad: $100 across 10 pairs = $10 per pair
✅ Good: $1000 across 3 pairs = $333 per pair
```

#### 4. Don't Forget Global Risk
```python
❌ Bad: Each pair risking 2% = 10% total risk (5 pairs)
✅ Good: Total portfolio risk capped at 5%
```

---

## 7. Examples

### Example 1: Conservative Multi-Pair

**Goal**: Steady returns with low risk

```python
{
  "name": "Conservative Multi-Pair Bot",
  "bot_type": "TECHNICAL",
  
  # Pairs
  "trading_pair": "BTC/USDT",
  "secondary_trading_pairs": [
    "ETH/USDT",
    "BNB/USDT"
  ],
  
  # Position Management
  "max_open_positions": 2,
  "max_capital_per_pair": 1000,
  
  # Risk
  "risk_config": {
    "stop_loss_percent": 2.0,
    "take_profit_percent": 4.0,
    "max_daily_loss": 100,
    "risk_per_trade": 1.0
  },
  
  # Execution
  "check_interval": 300,  # Check every 5 minutes
  "min_time_between_trades": 600  # 10 min cooldown
}
```

**Expected Performance:**
- Win Rate: 60%
- Risk/Reward: 1:2
- Max Drawdown: <10%
- Monthly Return: 8-12%

### Example 2: Aggressive Multi-Pair (Futures)

**Goal**: High returns, higher risk

```python
{
  "name": "Aggressive Futures Multi-Pair",
  "bot_type": "FUTURES",
  
  # Pairs
  "trading_pair": "BTC/USDT",
  "secondary_trading_pairs": [
    "ETH/USDT",
    "SOL/USDT",
    "MATIC/USDT"
  ],
  
  # Leverage
  "leverage": 10,
  "leverage_type": "ISOLATED",
  
  # Position Management
  "max_open_positions": 3,
  "max_capital_per_pair": 2000,
  
  # Risk
  "risk_config": {
    "stop_loss_percent": 1.5,
    "take_profit_percent": 3.0,
    "trailing_stop": true,
    "trailing_stop_percent": 0.8,
    "max_daily_loss": 5.0,
    "risk_per_trade": 2.0
  }
}
```

**Expected Performance:**
- Win Rate: 55%
- Risk/Reward: 1:2
- Max Drawdown: 15-20%
- Monthly Return: 15-30%

### Example 3: LLM-Powered Multi-Pair

**Goal**: AI-driven pair selection and timing

```python
{
  "name": "AI Multi-Pair Selector",
  "bot_type": "LLM",
  
  # LLM Config
  "llm_provider_id": 123,
  "prompt_template_id": 789,
  
  # Dynamic Pair Selection
  "trading_pair": "BTC/USDT",
  "secondary_trading_pairs": [
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "AVAX/USDT"
  ],
  
  # AI decides which pairs to trade
  "ai_pair_selection": true,
  "max_ai_selected_pairs": 3,
  
  # Risk (AI-controlled)
  "risk_management_mode": "AI_PROMPT",
  "max_open_positions": 3,
  "total_max_exposure": 5000
}
```

**AI Prompt Example:**
```markdown
Analyze the following pairs and select the top 3 to trade:
- BTC/USDT: RSI {{btc_rsi}}, Trend {{btc_trend}}
- ETH/USDT: RSI {{eth_rsi}}, Trend {{eth_trend}}
- SOL/USDT: RSI {{sol_rsi}}, Trend {{sol_trend}}

Consider:
1. Strongest trends
2. Lowest correlation
3. Best risk/reward

Respond with JSON:
{
  "selected_pairs": ["BTC/USDT", "SOL/USDT"],
  "reasoning": "..."
}
```

---

## 📊 Performance Comparison

| Strategy | Pairs | Return (Monthly) | Risk | Complexity |
|----------|-------|------------------|------|------------|
| Single Pair | 1 | 5-8% | Low | Simple |
| Multi-Pair (2-3) | 2-3 | 8-12% | Medium | Medium |
| Multi-Pair (4-6) | 4-6 | 10-15% | High | Complex |
| AI Multi-Pair | Dynamic | 12-20% | High | Advanced |

---

## 🆘 Troubleshooting

### "Too many open positions"
```
Solution:
1. Check max_open_positions setting
2. Close some positions manually
3. Increase capital allocation
```

### "Pairs moving in sync (high correlation)"
```
Solution:
1. Replace correlated pairs
2. Enable correlation monitoring
3. Choose pairs from different sectors
```

### "Low capital utilization"
```
Solution:
1. Reduce max_capital_per_pair
2. Add more secondary pairs
3. Lower entry thresholds
```

---

**Next**: [Publishing to Marketplace →](./07-publishing-to-marketplace.md)

