# 📡 Bot Type: SIGNALS_FUTURES

## 📋 Overview

`SIGNALS_FUTURES` là bot type mới dành riêng cho **signals-only futures trading bots** - bots chỉ phân tích và gửi signals mà **KHÔNG thực hiện trade execution**.

## 🎯 Use Case

- ✅ Crawl data từ exchange API (Binance, Bybit, OKX, Bitget, Huobi, Kraken)
- ✅ Analyze data với LLM (OpenAI/Claude/Gemini) hoặc technical indicators
- ✅ Generate trading signals (BUY/SELL/HOLD)
- ✅ Send notifications qua Telegram/Discord
- ❌ **KHÔNG execute trades** (no position opening/closing)

## 🔧 Implementation

### 1. **Enum Definition**

```python
# core/models.py & core/schemas.py
class BotType(enum.Enum):
    FUTURES = "FUTURES"              # Active futures trading
    SPOT = "SPOT"                    # Active spot trading
    FUTURES_RPA = "FUTURES_RPA"      # RPA-based futures trading
    SIGNALS_FUTURES = "SIGNALS_FUTURES"  # ✨ New: Signals-only futures bot
    # ... other types
```

### 2. **Bot Template**

Template: `universal_futures_signals_bot.py`

**Key Features:**
- Multi-exchange support (Binance, Bybit, OKX, Bitget, Huobi, Kraken)
- LLM analysis integration
- Override `setup_position()` để skip trade execution:

```python
async def setup_position(self, action: Action, confirmation: Any = None, subscription: Any = None):
    """Skip trade execution for signals-only bot"""
    logger.info(f"📡 [SIGNALS BOT] Skipping trade execution - this is a signals-only bot")
    return {
        'status': 'skipped',
        'reason': 'Signals-only bot - no trade execution',
        'signal': action.action,
        'confidence': action.value
    }
```

### 3. **Auto-Detection Logic**

Khi tạo bot từ template `universal_futures_signals_bot`:

```python
# core/crud.py - create_bot()
TEMPLATE_FILE_MAPPING = {
    'universal_futures_signals_bot': 'bot_files/universal_futures_signals_bot.py',
    'universal_futures_signals_bot.py': 'bot_files/universal_futures_signals_bot.py',
}

TEMPLATE_BOT_TYPE_MAPPING = {
    'universal_futures_signals_bot': 'SIGNALS_FUTURES',
    'universal_futures_signals_bot.py': 'SIGNALS_FUTURES',
}
```

**→ Tự động set `bot_type = 'SIGNALS_FUTURES'` và `code_path = 'bot_files/universal_futures_signals_bot.py'`**

### 4. **Task Routing**

```python
# core/tasks.py - schedule_active_bots()
if subscription.bot.bot_type == "SIGNALS_FUTURES":
    # Use run_bot_logic with bot template code
    run_bot_logic.delay(subscription.id)
    logger.info(f"✅ Triggered run_bot_logic for SIGNALS_FUTURES bot")
```

**Flow:**
1. `schedule_active_bots` → Detect `bot_type == SIGNALS_FUTURES`
2. → `run_bot_logic.delay()` → Load bot template
3. → `execute_algorithm()` → Crawl data, analyze, generate signal
4. → `setup_position()` → **Return 'skipped'** (no trade execution)
5. → Send notification via Telegram/Discord

## 📊 Comparison: Bot Types

| Bot Type | Description | Task Handler | Trade Execution | Use Case |
|----------|-------------|--------------|-----------------|----------|
| **PASSIVE** (legacy) | Legacy signal-only | `run_bot_signal_logic` | ❌ No | Old RPA-based signals (Robot Framework) |
| **FUTURES** | Active futures trading | `run_bot_logic` | ✅ Yes | Full automated futures trading |
| **SPOT** | Active spot trading | `run_bot_logic` | ✅ Yes | Full automated spot trading |
| **SIGNALS_FUTURES** | Signals-only futures | `run_bot_logic` | ❌ No | ✨ Modern signals with exchange API |

## 🔍 Key Differences: PASSIVE vs SIGNALS_FUTURES

| Feature | PASSIVE | SIGNALS_FUTURES |
|---------|---------|-----------------|
| Data Source | TradingView (Robot Framework) | Exchange API (direct) |
| Task | `run_bot_signal_logic` | `run_bot_logic` |
| Technology | Selenium + Screenshot analysis | Native API + LLM |
| Performance | Slower (browser automation) | Faster (direct API) |
| Dependencies | Chrome, Robot Framework | Exchange API keys |
| Recommended | ❌ Legacy | ✅ Modern |

## ✅ Benefits

1. **Cleaner Architecture**: Sử dụng chung `run_bot_logic` với active trading bots
2. **Better Performance**: Direct exchange API thay vì browser automation
3. **Easier Maintenance**: Dùng bot template thay vì custom Robot Framework code
4. **Future-Proof**: Dễ mở rộng thêm exchanges và features

## 📝 Example: Creating a Signals Bot

### Via API:

```python
bot_data = {
    "name": "BTC Signals Bot",
    "description": "AI-powered BTC trading signals",
    "template": "universal_futures_signals_bot",  # ✨ Auto-set bot_type
    "trading_pair": "BTC/USDT",
    "timeframes": ["30m", "1h", "4h"],
    "exchange_type": "BINANCE",
    # bot_type will be auto-set to "SIGNALS_FUTURES"
    # bot_mode will be "ACTIVE" (default)
}
```

### Database Result:

```sql
SELECT id, name, bot_type, bot_mode, code_path 
FROM bots 
WHERE id = 121;

-- Result:
-- id: 121
-- name: 📡 Universal Futures Signals Entity - 003
-- bot_type: SIGNALS_FUTURES ✨
-- bot_mode: ACTIVE
-- code_path: bot_files/universal_futures_signals_bot.py
```

## 🚀 Migration

**Migration File:** `migrations/versions/045_add_signals_futures_bot_type.sql`

```sql
-- Add SIGNALS_FUTURES to bot_type (stored as VARCHAR)
-- No ALTER needed - VARCHAR already supports any string value

-- Update existing signal bots
UPDATE bots 
SET bot_type = 'SIGNALS_FUTURES',
    bot_mode = 'ACTIVE'
WHERE code_path LIKE '%universal_futures_signals_bot%';
```

## 🔧 Configuration

**No special configuration needed!** Chỉ cần:

1. Create bot với template `universal_futures_signals_bot`
2. System tự động set `bot_type = 'SIGNALS_FUTURES'`
3. Configure exchange credentials và notification channels
4. Start subscription → Bot sẽ tự động:
   - Crawl data từ exchange
   - Analyze với LLM
   - Send signals qua Telegram/Discord
   - Skip trade execution

## 📌 Summary

**SIGNALS_FUTURES** là bot type hiện đại cho signals-only trading bots:
- ✅ Auto-detection từ template name (`bot_type` được tự động set)
- ✅ Dùng exchange API thay vì browser automation
- ✅ Integrated với LLM analysis
- ✅ Clean architecture với trade execution override
- ✅ Better performance và maintainability
- ✅ Phân biệt rõ ràng với FUTURES (active trading) và PASSIVE (legacy)

---

**Created:** 2025-10-18  
**Version:** 1.0  
**Status:** ✅ Production Ready

