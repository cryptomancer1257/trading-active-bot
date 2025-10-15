# 📊 Position Monitoring & Performance Tracking System

## 🎯 Overview

Comprehensive system để monitor open positions, track P&L, và tự động close positions khi TP/SL hit.

---

## ✅ What's Implemented

### 1. **Enhanced Transaction Table** (Migration 027)

#### New Fields Added:
```sql
-- Identity & Tracking
user_principal_id       VARCHAR(255)   -- Marketplace user tracking
prompt_id               INT            -- Track which prompt was used

-- Entry Details
entry_time              DATETIME       -- Precise entry timestamp
position_side           ENUM('LONG', 'SHORT')

-- Exit Details
exit_price              DECIMAL(20,8)  -- Close price
exit_time               DATETIME       -- Close timestamp
exit_reason             ENUM('TP_HIT', 'SL_HIT', 'MANUAL', 'TIMEOUT', 'LIQUIDATION', 'TRAILING_STOP')

-- P&L Tracking
pnl_usd                 DECIMAL(20,8)  -- Profit/Loss in USD
pnl_percentage          DECIMAL(10,4)  -- P&L as percentage
is_winning              BOOLEAN        -- Win/loss flag
realized_pnl            DECIMAL(20,8)  -- Final realized P&L
unrealized_pnl          DECIMAL(20,8)  -- Current open P&L

-- Performance Metrics
risk_reward_ratio       DECIMAL(10,4)  -- Planned RR (e.g., 3.0 for 1:3)
actual_rr_ratio         DECIMAL(10,4)  -- Actual RR achieved
strategy_used           VARCHAR(100)   -- LLM strategy name

-- Trading Costs
fees_paid               DECIMAL(20,8)  -- Trading fees
slippage                DECIMAL(10,4)  -- Price slippage %

-- Duration & Monitoring
trade_duration_minutes  INT            -- How long position held
last_updated_price      DECIMAL(20,8)  -- Current market price
```

#### Updated Status Enum:
```sql
'PENDING'     -- Order placed, not filled
'EXECUTED'    -- Order filled (legacy)
'OPEN'        -- Position currently open ✨ NEW
'CLOSED'      -- Position closed ✨ NEW
'STOPPED_OUT' -- Stopped out by SL ✨ NEW
'FAILED'      -- Order failed
'CANCELLED'   -- Order cancelled
```

---

### 2. **Position Monitor Service** (`services/position_monitor.py`)

#### Core Functions:

**`get_open_transactions(bot_id)`**
- Lấy tất cả transactions với `status='OPEN'`
- Filter theo bot_id (optional)

**`check_order_status_from_exchange(symbol, order_id)`**
- Check order status từ Binance API: `futures_get_order()`
- Returns order info hoặc None

**`get_current_position(symbol)`**
- Lấy position hiện tại từ Binance: `futures_position_information()`
- Returns position data nếu `positionAmt != 0`

**`calculate_pnl(entry_price, current_price, quantity, position_side)`**
- Tính P&L theo position side (LONG/SHORT)
- Returns: `{pnl_usd, pnl_percentage}`

**`check_tp_sl_hit(transaction, current_price)`**
- Check nếu TP hoặc SL hit
- Returns: `'TP_HIT'`, `'SL_HIT'`, hoặc `None`

**`update_transaction_on_close(transaction, exit_price, exit_reason, current_time)`**
- Update transaction khi close position
- Calculate final P&L, RR ratio, trade duration
- Set `status='CLOSED'`
- Commit to database

**`update_unrealized_pnl(transaction, current_price)`**
- Update `unrealized_pnl` và `last_updated_price`
- Dùng cho monitoring open positions

**`monitor_open_positions(bot_id=None)`** ⭐ MAIN FUNCTION
- Check tất cả open positions
- Update unrealized P&L
- Check TP/SL hit → close nếu cần
- Returns summary: `{total_checked, positions_closed, positions_updated, errors}`

---

### 3. **Celery Tasks for Automation** (`core/tasks.py`)

#### Task 1: `monitor_open_positions_task()` 🔄 PERIODIC
**Chức năng:**
- Monitor tất cả open positions
- Check TP/SL hit
- Update unrealized P&L
- Close positions tự động

**Schedule:** Every 3 minutes (Celery Beat)

**Workflow:**
```python
1. Get all open transactions (status='OPEN')
2. For each transaction:
   a. Get current position from Binance
   b. Get current market price
   c. Check if TP/SL hit:
      - If hit → close position, update DB
      - Else → update unrealized_pnl
   d. Trigger performance updates
3. Return summary
```

---

#### Task 2: `update_bot_performance_metrics(bot_id)` 📈 ON DEMAND
**Chức năng:**
- Calculate bot performance metrics
- Update bot metadata

**Triggered:** When position closes

**Metrics Calculated:**
```python
- total_trades        # Tổng số lệnh
- winning_trades      # Số lệnh thắng
- losing_trades       # Số lệnh thua
- win_rate           # Tỷ lệ thắng (%)
- total_pnl          # Tổng P&L ($)
- avg_pnl            # P&L trung bình
- avg_win            # Trung bình lệnh thắng
- avg_loss           # Trung bình lệnh thua
- profit_factor      # (avg_win * wins) / (avg_loss * losses)
```

**Saved to:** `bot.metadata['performance']`

---

#### Task 3: `update_prompt_performance_metrics(prompt_id)` 📊 ON DEMAND
**Chức năng:**
- Calculate prompt effectiveness
- Update PromptUsageStats

**Triggered:** When position closes

**Metrics:**
```python
- total_trades       # Số lệnh dùng prompt này
- winning_trades     # Số lệnh thắng
- win_rate          # Tỷ lệ thắng
- total_pnl         # Tổng P&L
- avg_pnl           # P&L trung bình
```

**Saved to:** `PromptUsageStats` table

---

#### Task 4: `update_risk_management_performance(bot_id)` 🎯 ON DEMAND
**Chức năng:**
- Analyze risk management effectiveness

**Triggered:** When position closes

**Metrics:**
```python
- tp_hit_rate           # % positions closed by TP
- sl_hit_rate           # % positions closed by SL
- manual_exit_rate      # % closed manually
- avg_planned_rr        # Average planned risk-reward
- avg_actual_rr         # Average achieved risk-reward
- rr_achievement_rate   # How well RR targets met
- avg_slippage         # Average slippage
```

---

### 4. **Updated Bot Code** (`bot_files/binance_futures_bot.py`)

#### Enhanced `save_transaction_to_db()`:

**Now saves:**
```python
# Identity
user_id, user_principal_id, bot_id, subscription_id, prompt_id

# Trade Details
action, position_side, symbol, quantity, entry_price, entry_time, leverage

# Risk Management
stop_loss, take_profit, risk_reward_ratio (auto-calculated)

# LLM Strategy
strategy_used, confidence, reason

# Status
status='OPEN'  # Changed from 'PENDING'
```

**Risk-Reward Auto-Calculation:**
```python
if stop_loss and take_profit:
    risk = abs(entry_price - stop_loss)
    reward = abs(take_profit - entry_price)
    risk_reward_ratio = reward / risk  # e.g., 3.0 for 1:3 RR
```

---

### 5. **Celery Beat Schedule** (`utils/celery_app.py`)

**New Queues:**
```python
'monitoring'  # Position monitoring tasks
'analytics'   # Performance calculation tasks
```

**New Beat Schedule:**
```python
'monitor-open-positions': {
    'task': 'core.tasks.monitor_open_positions_task',
    'schedule': 180.0  # Every 3 minutes
}
```

---

## 🔄 Complete Workflow

### Event 1: TRADE OPENED (Bot executes trade)

```
1. Bot calls setup_position() → Places order on Binance
2. Order filled
3. Bot calls save_transaction_to_db(trade_result)
4. Transaction saved with:
   ✅ status = 'OPEN'
   ✅ entry_price, entry_time, position_side
   ✅ stop_loss, take_profit, risk_reward_ratio
   ✅ prompt_id, strategy_used
   ✅ bot_id, subscription_id
```

---

### Event 2: POSITION MONITORING (Every 3 minutes - Celery Beat)

```
1. Celery Beat triggers: monitor_open_positions_task()
2. PositionMonitor.monitor_open_positions():
   
   For each OPEN transaction:
   ├─ Get current position from Binance
   ├─ Get current market price
   ├─ Calculate unrealized P&L
   ├─ Check if TP/SL hit:
   │  ├─ TP hit? → Close position, exit_reason='TP_HIT'
   │  ├─ SL hit? → Close position, exit_reason='SL_HIT'
   │  └─ None hit? → Update unrealized_pnl
   │
   └─ If closed:
      ├─ Update transaction:
      │  ├─ status = 'CLOSED'
      │  ├─ exit_price, exit_time, exit_reason
      │  ├─ pnl_usd, pnl_percentage, is_winning
      │  ├─ realized_pnl, actual_rr_ratio
      │  └─ trade_duration_minutes
      │
      └─ Trigger async tasks:
         ├─ update_bot_performance_metrics(bot_id)
         ├─ update_prompt_performance_metrics(prompt_id)
         └─ update_risk_management_performance(bot_id)
```

---

### Event 3: PERFORMANCE UPDATES (Triggered on position close)

```
update_bot_performance_metrics(bot_id):
├─ Query all CLOSED transactions for bot
├─ Calculate: win_rate, total_pnl, profit_factor, etc.
└─ Save to bot.metadata['performance']

update_prompt_performance_metrics(prompt_id):
├─ Query all CLOSED transactions using this prompt
├─ Calculate: win_rate, avg_pnl, total_trades
└─ Update PromptUsageStats table

update_risk_management_performance(bot_id):
├─ Analyze: TP hit rate, SL hit rate, RR achievement
└─ Return risk metrics
```

---

## 🚀 How to Use

### 1. **Start Celery Worker with Monitoring Queue**

```bash
# Terminal 1: Worker for monitoring
celery -A utils.celery_app worker --loglevel=info -Q monitoring,analytics

# Terminal 2: Beat scheduler
celery -A utils.celery_app beat --loglevel=info
```

### 2. **Monitor Positions Manually (Testing)**

```python
from services.position_monitor import PositionMonitor
from core.database import SessionLocal
from binance.client import Client

# Initialize
db = SessionLocal()
client = Client(api_key, api_secret)
monitor = PositionMonitor(db, client)

# Monitor all positions
results = monitor.monitor_open_positions()
print(results)
# Output: {'total_checked': 5, 'positions_closed': 2, 'positions_updated': 3, 'errors': []}
```

### 3. **Check Bot Performance**

```python
from core.tasks import update_bot_performance_metrics

# Calculate performance for bot ID 52
metrics = update_bot_performance_metrics(52)
print(metrics)
# Output: {'bot_id': 52, 'total_trades': 10, 'win_rate': 70.0, 'total_pnl': 1250.50, 'profit_factor': 2.8}
```

### 4. **Query Open Positions**

```python
from core.database import SessionLocal
from core import models

db = SessionLocal()

# Get all open positions
open_positions = db.query(models.Transaction).filter(
    models.Transaction.status == 'OPEN'
).all()

for tx in open_positions:
    print(f"Bot {tx.bot_id}: {tx.symbol} {tx.position_side} @ ${tx.entry_price}")
    print(f"  Unrealized P&L: ${tx.unrealized_pnl or 0:.2f}")
```

---

## 📊 Binance API Endpoints Used

### 1. **Check Order Status**
```python
order = client.futures_get_order(
    symbol='BTCUSDT',
    orderId=12345
)
# Returns: {status, avgPrice, executedQty, ...}
```

### 2. **Get Current Position**
```python
positions = client.futures_position_information(symbol='BTCUSDT')
# Returns: [{positionAmt, entryPrice, markPrice, unrealizedProfit, ...}]
```

### 3. **Get Open Orders**
```python
open_orders = client.futures_get_open_orders(symbol='BTCUSDT')
# Returns: List of open orders
```

---

## 🎯 Benefits

### For Developers:
✅ **Auto TP/SL Management** - Không cần manually monitor  
✅ **Real-time P&L** - Track unrealized profit/loss  
✅ **Performance Analytics** - Win rate, profit factor tự động  
✅ **Prompt Testing** - A/B test different strategies  
✅ **Risk Management** - Analyze RR achievement, slippage  

### For Users:
✅ **Transparent Tracking** - See all trade history with P&L  
✅ **Automatic Execution** - TP/SL hit → auto close  
✅ **Performance Metrics** - Know which bots/prompts work best  

---

## 🔧 Configuration

### Environment Variables Required:

```bash
# Binance API (for monitoring)
BINANCE_MAINNET_API_KEY=your_api_key
BINANCE_MAINNET_API_SECRET=your_api_secret

# Database
DATABASE_URL=mysql+pymysql://user:pass@localhost:3307/bot_marketplace

# Redis (Celery)
REDIS_URL=redis://localhost:6379/0
```

### Celery Beat Schedule (Adjustable):

```python
# utils/celery_app.py
'monitor-open-positions': {
    'task': 'core.tasks.monitor_open_positions_task',
    'schedule': 180.0  # Change to 60.0 for every 1 minute, 300.0 for 5 minutes
}
```

---

## 📝 Database Schema

### Transactions Table (After Migration 027):
```
mysql> DESCRIBE transactions;
+-------------------------+------------------+------+-----+---------+
| Field                   | Type             | Null | Key | Default |
+-------------------------+------------------+------+-----+---------+
| id                      | int              | NO   | PRI | NULL    |
| user_id                 | int              | YES  | MUL | NULL    | ← Nullable now
| user_principal_id       | varchar(255)     | YES  | MUL | NULL    | ← NEW
| bot_id                  | int              | YES  | MUL | NULL    |
| subscription_id         | int              | YES  | MUL | NULL    |
| prompt_id               | int              | YES  | MUL | NULL    | ← NEW
| action                  | varchar(10)      | YES  |     | NULL    |
| position_side           | enum(...)        | YES  |     | NULL    | ← NEW
| symbol                  | varchar(20)      | YES  |     | NULL    |
| quantity                | decimal(20,8)    | YES  |     | NULL    |
| entry_price             | decimal(20,8)    | YES  |     | NULL    |
| entry_time              | datetime         | YES  | MUL | NULL    | ← NEW
| exit_price              | decimal(20,8)    | YES  |     | NULL    | ← NEW
| exit_time               | datetime         | YES  | MUL | NULL    | ← NEW
| exit_reason             | enum(...)        | YES  |     | NULL    | ← NEW
| pnl_usd                 | decimal(20,8)    | YES  |     | NULL    | ← NEW
| pnl_percentage          | decimal(10,4)    | YES  |     | NULL    | ← NEW
| is_winning              | tinyint(1)       | YES  | MUL | NULL    | ← NEW
| realized_pnl            | decimal(20,8)    | YES  |     | NULL    | ← NEW
| unrealized_pnl          | decimal(20,8)    | YES  |     | NULL    | ← NEW
| risk_reward_ratio       | decimal(10,4)    | YES  |     | NULL    | ← NEW
| actual_rr_ratio         | decimal(10,4)    | YES  |     | NULL    | ← NEW
| strategy_used           | varchar(100)     | YES  |     | NULL    | ← NEW
| fees_paid               | decimal(20,8)    | YES  |     | 0       | ← NEW
| slippage                | decimal(10,4)    | YES  |     | NULL    | ← NEW
| trade_duration_minutes  | int              | YES  |     | NULL    | ← NEW
| last_updated_price      | decimal(20,8)    | YES  |     | NULL    | ← NEW
| status                  | enum(...)        | YES  | MUL | PENDING |
| created_at              | datetime         | YES  |     | NULL    |
| updated_at              | datetime         | YES  |     | NULL    |
+-------------------------+------------------+------+-----+---------+
```

---

## 🧪 Testing

### Manual Test Position Monitoring:

```bash
# Run monitoring task manually
celery -A utils.celery_app call core.tasks.monitor_open_positions_task
```

### Create Test Open Position:

```python
from core.database import SessionLocal
from core import models
from datetime import datetime
from decimal import Decimal

db = SessionLocal()

test_tx = models.Transaction(
    bot_id=52,
    symbol='BTCUSDT',
    action='BUY',
    position_side='LONG',
    quantity=Decimal('0.001'),
    entry_price=Decimal('50000'),
    entry_time=datetime.now(),
    stop_loss=Decimal('49000'),
    take_profit=Decimal('53000'),
    leverage=10,
    status='OPEN',
    order_id='test123'
)

db.add(test_tx)
db.commit()

print(f"Test transaction created: ID {test_tx.id}")
```

---

## 🎉 Summary

**System bây giờ có:**

✅ **Migration 027** - Enhanced transactions table  
✅ **PositionMonitor** - Service để monitor & close positions  
✅ **4 Celery Tasks** - Monitoring + Performance tracking  
✅ **Celery Beat** - Auto-run monitoring every 3 minutes  
✅ **Enhanced Bot Code** - Save đầy đủ info khi open trade  
✅ **Binance API Integration** - Check order status & positions  

**Next steps để improve:**
- Frontend dashboard để xem performance metrics
- Webhook notifications khi position closed
- Advanced analytics (Sharpe ratio, max drawdown, etc.)
- Multi-exchange support

