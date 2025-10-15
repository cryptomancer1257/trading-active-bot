# Multi-Pair Trading Feature

## Overview
The Multi-Pair Trading feature allows a single subscription to monitor and trade multiple trading pairs with a priority-based system. This enables better diversification and utilization of trading opportunities.

## How It Works

### Priority-Based Trading
Each subscription can have:
- **1 Primary Trading Pair** (required)
- **N Secondary Trading Pairs** (optional, priority ordered)

### Trading Logic
When a Celery task executes:

1. **Check Primary Pair First**
   - If NO open position → Trade this pair (if LLM says BUY + passes risk management)
   - If has open position → Move to step 2

2. **Check Secondary Pairs in Order**
   - Check secondary pair 1: If NO open position → Trade
   - If has open position → Check secondary pair 2
   - Continue until finding an available pair

3. **One Trade Per Execution**
   - Only 1 trading pair is traded per task execution
   - Ensures focused risk management

4. **All Pairs Busy → Wait**
   - If ALL pairs have open positions → HOLD
   - Wait for next task execution
   - Will check again from primary pair

## Database Schema

### Migration: `030_add_secondary_trading_pairs.sql`
```sql
ALTER TABLE subscriptions 
ADD COLUMN secondary_trading_pairs JSON DEFAULT NULL;
```

### Data Structure
```json
{
  "trading_pair": "BTC/USDT",              // Primary pair
  "secondary_trading_pairs": [             // Priority order
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT"
  ]
}
```

## Example Scenario

### Setup
- Primary: BTC/USDT
- Secondary: [ETH/USDT, BNB/USDT, SOL/USDT]

### Execution Timeline

**Task Run #1 (12:00)**
```
Check BTC/USDT: ✅ No OPEN → Trade BTC/USDT
Result: BUY 0.001 BTC @ $80,409
```

**Task Run #2 (12:05)**
```
Check BTC/USDT: ⏭️  OPEN position exists → Skip
Check ETH/USDT: ✅ No OPEN → Trade ETH/USDT
Result: BUY 0.05 ETH @ $3,200
```

**Task Run #3 (12:10)**
```
Check BTC/USDT: ⏭️  OPEN position exists → Skip
Check ETH/USDT: ⏭️  OPEN position exists → Skip
Check BNB/USDT: ✅ No OPEN → Trade BNB/USDT
Result: BUY 2.5 BNB @ $600
```

**Task Run #4 (12:15)**
```
Check BTC/USDT: ⏭️  OPEN position exists → Skip
Check ETH/USDT: ⏭️  OPEN position exists → Skip
Check BNB/USDT: ⏭️  OPEN position exists → Skip
Check SOL/USDT: ✅ No OPEN → Trade SOL/USDT
Result: BUY 10 SOL @ $150
```

**Task Run #5 (12:20)**
```
Check BTC/USDT: ⏭️  OPEN position exists → Skip
Check ETH/USDT: ⏭️  OPEN position exists → Skip
Check BNB/USDT: ⏭️  OPEN position exists → Skip
Check SOL/USDT: ⏭️  OPEN position exists → Skip
Result: HOLD (All pairs busy)
```

**Task Run #6 (12:25) - After BTC position closed**
```
Check BTC/USDT: ✅ No OPEN (position was closed) → Trade BTC/USDT again
Result: BUY 0.001 BTC @ $81,200
```

## Benefits

### 1. Diversification
- Spread risk across multiple assets
- Not limited to single trading pair

### 2. Opportunity Maximization
- Capture signals from multiple markets
- Efficient capital utilization

### 3. Priority Control
- User defines which pairs are most important
- Bot respects priority order

### 4. Risk Management
- Only 1 trade per execution cycle
- Prevents over-leveraging
- Each pair subject to risk checks

## Implementation Details

### Code Changes

#### 1. Database (core/models.py)
```python
class Subscription(Base):
    trading_pair = Column(String(20))  # Primary
    secondary_trading_pairs = Column(JSON)  # List of secondary pairs
```

#### 2. Schema (core/schemas.py)
```python
class SubscriptionBase(BaseModel):
    trading_pair: str  # Primary
    secondary_trading_pairs: Optional[List[str]] = []  # Secondary
```

#### 3. Tasks Logic (core/tasks.py)
```python
# In run_advanced_futures_workflow():
# 1. Build priority list: [primary] + secondary_pairs
# 2. Iterate through pairs
# 3. Check for OPEN positions with SELECT FOR UPDATE (prevent race conditions)
# 4. Trade first available pair
# 5. If all busy → HOLD
```

### Race Condition Prevention
```python
# Use SELECT FOR UPDATE to lock rows
open_positions = db.query(models.Transaction).filter(
    models.Transaction.subscription_id == subscription_id,
    models.Transaction.symbol == trading_pair_normalized,
    models.Transaction.status == 'OPEN'
).with_for_update().all()
```

## Logging

### Enhanced Logs
```
================================================================================
🎯 Step 0: MULTI-PAIR TRADING - Finding available trading pair...
================================================================================

📋 Trading Pairs Priority List:
   1️⃣ Primary: BTC/USDT
   2️⃣ Secondary: ETH/USDT
   3️⃣ Secondary: BNB/USDT
   4️⃣ Secondary: SOL/USDT
   📊 Total pairs to check: 4

🔍 Checking pair 1/4: BTC/USDT (DB: BTCUSDT)
   ⏭️  SKIP: 1 OPEN position(s) found
      - Position #123: BUY 0.001 @ $80409.10, P&L: $5.25

🔍 Checking pair 2/4: ETH/USDT (DB: ETHUSDT)
   ✅ AVAILABLE: No OPEN positions
   🎯 SELECTED for trading: ETH/USDT

================================================================================
🎯 SELECTED TRADING PAIR: ETH/USDT
================================================================================
   Priority: 2 of 4
   Proceeding with LLM analysis for ETH/USDT...
================================================================================
```

## Configuration

### Adding Secondary Pairs

#### Via API
```python
subscription_data = {
    "trading_pair": "BTC/USDT",  # Primary
    "secondary_trading_pairs": [  # Secondary (priority order)
        "ETH/USDT",
        "BNB/USDT",
        "SOL/USDT"
    ]
}
```

#### Via Database
```sql
UPDATE subscriptions
SET secondary_trading_pairs = '["ETH/USDT", "BNB/USDT", "SOL/USDT"]'
WHERE id = 123;
```

## Best Practices

### 1. Pair Selection
- Choose correlated or diversified pairs based on strategy
- Consider liquidity and volatility
- Start with 2-3 pairs, expand gradually

### 2. Priority Order
- Most important pair as primary
- Order secondary by preference or signal strength
- Can reorder based on market conditions

### 3. Risk Management
- Each pair independently checked by risk management
- Daily loss limit applies to ALL pairs combined
- Consider total exposure across all pairs

### 4. Monitoring
- Check logs for pair selection logic
- Monitor P&L per pair in Analytics
- Adjust pair list based on performance

## Limitations

### 1. One Trade Per Cycle
- Bot can only place 1 order per task execution
- This is by design for risk control

### 2. Sequential Checking
- Pairs checked in order, not in parallel
- First available pair is selected

### 3. No Dynamic Reordering
- Priority order is fixed per subscription
- Requires manual update to change priority

## Future Enhancements

### Potential Features
1. **Dynamic Priority** - Reorder based on signal strength
2. **Pair-Specific Risk** - Different risk params per pair
3. **Correlation Analysis** - Avoid trading correlated pairs simultaneously
4. **Performance-Based Selection** - Prioritize high-performing pairs
5. **Time-Based Rotation** - Different pairs for different times

## Testing

### Test Scenario 1: Single Pair
```
Primary: BTC/USDT
Secondary: []
Result: Trades BTC/USDT (legacy behavior)
```

### Test Scenario 2: Multi-Pair with Availability
```
Primary: BTC/USDT (OPEN)
Secondary: [ETH/USDT (AVAILABLE), BNB/USDT]
Result: Trades ETH/USDT
```

### Test Scenario 3: All Busy
```
Primary: BTC/USDT (OPEN)
Secondary: [ETH/USDT (OPEN), BNB/USDT (OPEN)]
Result: HOLD
```

## Support

For questions or issues:
- Check logs for pair selection details
- Verify `secondary_trading_pairs` in database
- Ensure pairs are correctly formatted (e.g., "BTC/USDT")

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-11  
**Status:** Active

