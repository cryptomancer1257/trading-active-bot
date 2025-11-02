# WebSocket Zone Trading Implementation

## 🎯 Overview

A complete WebSocket-based zone trading system that:
1. **Finds trigger zones** using LLM analysis of technical indicators (Celery task, every 1 hour)
2. **Monitors real-time prices** via WebSocket connections to Binance and Bybit
3. **Executes trades** automatically when price enters a trigger zone + LLM confirms

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     WEBSOCKET ZONE TRADING SYSTEM                    │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────────┐    ┌──────────────────────┐
│   Celery Beat        │    │  WebSocket Service   │
│  (Every 1 hour)      │    │  (Real-time monitor) │
└──────────────────────┘    └──────────────────────┘
         │                            │
         │ 1. Find Zones              │ 2. Monitor Prices
         ▼                            ▼
┌──────────────────────┐    ┌──────────────────────┐
│ find_trigger_zones   │    │  WebSocket Manager   │
│     (Celery Task)    │    │                      │
│                      │    │  • Binance WS        │
│ • Crawl OHLCV        │    │  • Bybit WS          │
│ • Calculate          │    │                      │
│   Indicators         │    │ Callbacks:           │
│ • Call LLM           │    │ on_price_update()    │
│ • Save to DB         │    └──────────────────────┘
└──────────────────────┘               │
         │                            │
         │                            │ 3. Price in Zone?
         ▼                            ▼
┌──────────────────────────────────────────────────┐
│             TriggerZone (Database)               │
│                                                  │
│  • zone_type: BUY / SELL                        │
│  • price_min, price_max                         │
│  • confidence (60-100)                          │
│  • status: active / triggered / expired         │
│  • expires_at: +1 hour                          │
└──────────────────────────────────────────────────┘
         │                            
         │ 4. Trigger Detected        
         ▼                            
┌──────────────────────┐              
│  Execute Zone Trade  │              
│                      │              
│ • Fetch latest       │              
│   indicators         │              
│ • Call LLM for       │              
│   final confirmation │              
│ • If approved,       │              
│   setup_position()   │              
│ • Mark zone as       │              
│   'triggered'        │              
└──────────────────────┘              
```

---

## 📦 Components Created

### 1. Database Schema

**File**: `core/models.py`
- `TriggerZone` model: Stores BUY/SELL zones with price ranges, confidence, status

**Migration**: `migrations/versions/062_add_trigger_zones_table.py`
- Creates `trigger_zones` table with indexes

**Migration**: `migrations/versions/063_add_zone_trading_columns.py`
- Adds `zone_trading_enabled` and `zone_update_frequency` to `bots` table

### 2. LLM Integration

**File**: `services/llm_integration.py`
- `find_trigger_zones()`: Analyzes indicators to identify BUY/SELL zones
- `_generate_zone_finding_prompt()`: Creates zone-specific LLM prompt
- `_find_zones_with_openai/claude/gemini()`: Provider-specific implementations

**Output Schema**:
```json
{
  "trigger_zones": [
    {"type": "BUY", "range": [880000, 920000], "confidence": 82},
    {"type": "SELL", "range": [1450000, 1500000], "confidence": 71}
  ],
  "reasoning": "RSI oversold on 1H/2H, strong 4H uptrend"
}
```

### 3. Celery Tasks

**File**: `core/tasks.py`
- `find_trigger_zones_task(subscription_id)`: Finds zones for one subscription
- `schedule_zone_finding_for_all_subscriptions()`: Dispatches tasks for all active bots

**Celery Beat Schedule**: `utils/celery_app.py`
- Runs `schedule_zone_finding_for_all_subscriptions` every 1 hour
- Uses new `zone_trading` queue

### 4. WebSocket Services

**File**: `services/websocket_connectors.py`
- `BinanceFuturesWebSocket`: Connects to Binance, subscribes to miniTicker
- `BybitFuturesWebSocket`: Connects to Bybit, subscribes to tickers
- Auto-reconnect with exponential backoff

**File**: `services/websocket_manager.py`
- `WebSocketManager`: Manages connections, routes price updates
- `_handle_price_update()`: Checks zones, triggers trades
- `_execute_zone_trade()`: Fetches indicators, calls LLM, executes position

**File**: `services/zone_trading_service.py`
- `ZoneTradingService`: Main orchestrator
- Starts WebSocket manager
- Periodically reloads subscriptions (every 5 minutes)
- Provides status and stats methods

### 5. API Endpoints

**File**: `api/endpoints/bots.py`
- `GET /{bot_id}/trigger-zones`: Get active/triggered/expired zones
- `DELETE /{bot_id}/trigger-zones/{zone_id}`: Mark zone as expired
- `GET /{bot_id}/zone-stats`: Get zone statistics

### 6. Startup Script

**File**: `run_websocket_service.py`
- Standalone script to run WebSocket service
- Checks prerequisites (database, migrations)
- Graceful shutdown on Ctrl+C

---

## 🚀 Deployment

### 1. Run Migrations

```bash
# Run migration 062 (TriggerZone table)
python migrations/versions/062_add_trigger_zones_table.py

# Run migration 063 (zone_trading_enabled columns)
python migrations/versions/063_add_zone_trading_columns.py
```

### 2. Start Celery Worker

```bash
celery -A utils.celery_app worker -Q zone_trading -l info
```

### 3. Start Celery Beat

```bash
celery -A utils.celery_app beat -l info
```

### 4. Start WebSocket Service

```bash
python run_websocket_service.py
```

**Expected Output**:
```
======================================================================
🚀 WEBSOCKET ZONE TRADING SERVICE
======================================================================
📍 Environment: production
🔗 Database: bot_marketplace
📊 Redis: redis://localhost:6379/0
======================================================================

🔍 Checking prerequisites...
  ✅ Database connection OK
  ✅ TriggerZone table exists
  ✅ zone_trading_enabled column exists
✅ All prerequisites met

======================================================================
      ✅ WEBSOCKET ZONE TRADING SERVICE STARTING
======================================================================

🚀 Starting WebSocket Manager...
📋 Found 3 active subscriptions with zone trading
📊 Starting Binance WebSocket for 2 symbols
📊 Starting Bybit WebSocket for 1 symbols
🔌 Connecting to Binance Futures WebSocket...
✅ Binance WebSocket connected
💹 BINANCE BTCUSDT @ $68500.00 | 2 active zones
  🎯 ZONE TRIGGER: BUY zone 1 @ $68500.00
    🤖 Executing zone trade for subscription 42...
    📊 Fetching latest indicators...
    🧠 Calling openai LLM for trade confirmation...
    📝 LLM Recommendation: BUY
    💰 Executing BUY trade at $68500.00...
    ✅ Trade executed successfully
  ✅ Zone 1 marked as triggered
```

---

## 🔧 Configuration

### Enable Zone Trading for a Bot

1. **Database** (or via API):
```sql
UPDATE bots 
SET zone_trading_enabled = TRUE,
    zone_update_frequency = 60  -- minutes
WHERE id = 140;
```

2. **API** (PATCH `/api/bots/{bot_id}`):
```json
{
  "zone_trading_enabled": true,
  "zone_update_frequency": 60
}
```

### Bot Requirements

For a bot to use zone trading:
1. ✅ `zone_trading_enabled = TRUE`
2. ✅ Must have active subscription
3. ✅ Bot must implement:
   - `crawl_data()` method
   - `analyze_data()` method (returns multi_timeframe with indicators)
   - `setup_position(llm_result, price)` method

---

## 🔄 Workflow

### Finding Zones (Celery Task - Every 1 Hour)

1. **Celery Beat** triggers `schedule_zone_finding_for_all_subscriptions`
2. For each active subscription with `zone_trading_enabled=true`:
   - Dispatch `find_trigger_zones_task(subscription_id)`
3. **find_trigger_zones_task**:
   - Load subscription and bot
   - Initialize bot instance
   - Crawl OHLCV data (`bot.crawl_data()`)
   - Calculate indicators (`bot.analyze_data()`)
   - Call LLM (`llm_service.find_trigger_zones()`)
   - Save zones to database (status='active', expires_at=+1 hour)
   - Mark old zones as 'expired'

**Example Zones Created**:
```
BUY Zone 1: $68000 - $68500 (confidence: 85%)
BUY Zone 2: $66000 - $66500 (confidence: 72%)
SELL Zone 1: $72000 - $72500 (confidence: 78%)
```

### Monitoring Prices (WebSocket Service - Real-time)

1. **WebSocket Manager** connects to Binance/Bybit
2. **Price Update** received (e.g., BTCUSDT = $68450)
3. **Check Active Zones**:
   - Query `trigger_zones` WHERE symbol='BTCUSDT' AND status='active'
   - Found: BUY Zone 1 ($68000 - $68500)
4. **Price in Range?** YES ($68450 is in $68000-$68500)
5. **Debounce Check**: Not triggered in last 1 minute? YES
6. **Execute Zone Trade**:
   - Fetch latest indicators
   - Call LLM: "Price is at $68450, should we BUY?"
   - LLM: "Yes, BUY with confidence 82%"
   - Execute: `bot.setup_position(llm_result, $68450)`
   - Mark zone as 'triggered'

### One Trigger Per Candle

**Debouncing Logic**:
- Each zone has `last_triggered_at` timestamp
- Only re-trigger if: `now - last_triggered_at > 1 minute`
- Prevents multiple triggers from same zone in short time

---

## 📊 API Usage

### Get Active Zones

```bash
GET /api/bots/140/trigger-zones?status=active

Response:
{
  "success": true,
  "bot_id": 140,
  "zones": [
    {
      "id": 1,
      "zone_type": "BUY",
      "price_min": 68000.0,
      "price_max": 68500.0,
      "confidence": 85,
      "reasoning": "Strong support at $68k, RSI oversold",
      "status": "active",
      "expires_at": "2025-11-01T12:00:00"
    }
  ],
  "total": 1
}
```

### Delete a Zone

```bash
DELETE /api/bots/140/trigger-zones/1

Response:
{
  "success": true,
  "message": "Trigger zone 1 marked as expired",
  "zone_id": 1
}
```

### Get Zone Statistics

```bash
GET /api/bots/140/zone-stats

Response:
{
  "success": true,
  "bot_id": 140,
  "zone_trading_enabled": true,
  "stats": {
    "total_active": 3,
    "buy_zones": 2,
    "sell_zones": 1,
    "triggered_today": 5,
    "expired_today": 8
  }
}
```

---

## 🔍 Monitoring & Logs

### WebSocket Service Logs

Located in: `logs/websocket_service.log`

**Key Events**:
- `🔌 Connecting to Binance/Bybit WebSocket...`
- `✅ WebSocket connected`
- `💹 {exchange} {symbol} @ ${price} | {count} active zones`
- `🎯 ZONE TRIGGER: {type} zone {id} @ ${price}`
- `✅ Trade executed successfully`
- `⚠️ WebSocket disconnected, reconnecting...`

### Celery Task Logs

**Key Events**:
- `🎯 Finding trigger zones for subscription {id}...`
- `📊 Bot: {name} (ID: {id})`
- `✅ Indicators calculated for timeframes: {timeframes}`
- `🤖 Calling {model} LLM to find trigger zones...`
- `🎯 LLM found {count} trigger zones`
- `✅ Saved {count} new trigger zones`

---

## ⚠️ Important Notes

### Performance Considerations

1. **WebSocket Limits**:
   - Binance: Max 1024 connections per IP
   - Bybit: Max 200 subscriptions per connection
   - Solution: Group symbols by exchange, batch subscriptions

2. **LLM Rate Limits**:
   - Zone finding: 1 call per subscription per hour
   - Trade confirmation: 1 call per zone trigger
   - Implement retry with backoff (already done)

3. **Database Queries**:
   - Indexes on `(bot_id, symbol, status)` for fast zone lookups
   - Auto-expire zones after 1 hour
   - Clean up expired zones periodically

### Error Handling

1. **WebSocket Disconnect**:
   - Auto-reconnect with exponential backoff (5s → 10s → 20s → 60s max)
   - Reconnect counter resets on successful connection

2. **LLM Timeout**:
   - Zone finding: Log error, skip this cycle, retry next hour
   - Trade confirmation: Log error, don't execute trade

3. **Zone Expiry**:
   - Zones expire after 1 hour
   - Celery task marks old zones as 'expired' before creating new ones

---

## 🧪 Testing

### Manual Test: Create Test Zone

```python
from core.database import SessionLocal
from core import models
from datetime import datetime, timedelta

db = SessionLocal()

test_zone = models.TriggerZone(
    bot_id=140,
    subscription_id=42,
    symbol='BTCUSDT',
    zone_type='BUY',
    price_min=68000,
    price_max=68500,
    confidence=85,
    reasoning='Test zone for manual testing',
    status='active',
    expires_at=datetime.utcnow() + timedelta(hours=1)
)

db.add(test_zone)
db.commit()
print(f"✅ Test zone created: {test_zone.id}")
```

### Test Zone Trigger

1. Start WebSocket service
2. Wait for price to enter zone range
3. Check logs for trigger event
4. Verify trade execution in transactions table

---

## 📈 Future Enhancements

1. **Frontend UI**:
   - Live zone visualization on chart
   - Enable/disable zone trading toggle
   - Zone history and performance

2. **Advanced Zone Types**:
   - Time-based zones (e.g., only active 9-11 AM)
   - Conditional zones (e.g., "if RSI < 30 AND volume spike")

3. **Multi-zone Strategies**:
   - Zone clusters for DCA (Dollar Cost Averaging)
   - Cascading zones with different position sizes

4. **Performance Analytics**:
   - Zone hit rate (how often zones are triggered)
   - Win rate by zone type
   - Optimal zone width analysis

---

## ✅ Completion Summary

### Files Created/Modified

**Created** (8 files):
1. `services/websocket_manager.py` - WebSocket connection manager
2. `services/websocket_connectors.py` - Binance/Bybit connectors
3. `services/zone_trading_service.py` - Main orchestrator
4. `migrations/versions/062_add_trigger_zones_table.py` - TriggerZone table
5. `migrations/versions/063_add_zone_trading_columns.py` - Bot config columns
6. `run_websocket_service.py` - Startup script
7. `WEBSOCKET_ZONE_TRADING_IMPLEMENTATION.md` - This document

**Modified** (5 files):
1. `core/models.py` - Added `TriggerZone` model, `zone_trading_enabled` fields
2. `core/schemas.py` - Added zone trading fields to `BotUpdate`
3. `services/llm_integration.py` - Added `find_trigger_zones()` method
4. `core/tasks.py` - Added zone finding Celery tasks
5. `utils/celery_app.py` - Added Celery beat schedule and queue
6. `api/endpoints/bots.py` - Added 3 new endpoints for zones

### Features Implemented

✅ **Database Schema**: TriggerZone table with all required fields  
✅ **LLM Integration**: find_trigger_zones() for all 3 providers  
✅ **Celery Tasks**: Zone finding + scheduling tasks  
✅ **WebSocket Service**: Real-time price monitoring  
✅ **Trade Execution**: Automatic zone-triggered trades  
✅ **API Endpoints**: GET zones, DELETE zone, GET stats  
✅ **Error Handling**: Reconnection, retry logic, debouncing  
✅ **Logging**: Comprehensive logging at all levels  
✅ **Documentation**: Complete implementation guide  

---

## 🎉 Ready to Deploy!

The WebSocket Zone Trading system is **fully implemented** and ready for deployment. Follow the deployment steps above to start using it.

For questions or issues, check the logs or contact the development team.

