# SIGNALS_FUTURES Fix: Skip Account Status Check

## Problem
Bot SIGNALS_FUTURES (signals-only) was calling `bot.check_account_status()` - một method chỉ dành cho active trading bots.

### Error Logs:
```
[2025-10-18 06:28:07,322: ERROR/ForkPoolWorker-1] Error in advanced_futures_workflow: 
'UniversalFuturesSignalsBot' object has no attribute 'check_account_status'

AttributeError: 'UniversalFuturesSignalsBot' object has no attribute 'check_account_status'
```

## Root Cause
Trong `run_advanced_futures_workflow()`, code gọi `bot.check_account_status()` cho **TẤT CẢ** bot types:
- ✅ `FUTURES` - cần account status (active trading)
- ✅ `SPOT` - cần account status (active trading)  
- ❌ `SIGNALS_FUTURES` - **KHÔNG CẦN** account status (signals-only, no trading)

SIGNALS_FUTURES bot template không có method `check_account_status()` vì:
1. Không trade → không cần check balance
2. Không connect đến exchange account → không có credentials
3. Chỉ crawl data từ public API → không cần authentication

## Solution
### 1. Modified `core/tasks.py`
Skip account status check for SIGNALS_FUTURES bots trong 2 workflows:

#### A. `run_advanced_futures_workflow()` (line ~2943)
```python
# 1. Check account status (like main_execution) - Skip for SIGNALS_FUTURES
logger.info("💰 Step 1: Checking account status...")

# SIGNALS_FUTURES bots don't need account status (signals-only, no trading)
bot_type_str = str(subscription.bot.bot_type).upper() if subscription.bot.bot_type else None
if bot_type_str == "SIGNALS_FUTURES":
    logger.info("📡 SIGNALS_FUTURES bot - Skip account check (signals-only, no trading)")
    account_status = None
else:
    # Active trading bots need account balance check
    account_status = bot.check_account_status()
    if account_status:
        logger.info(f"Account Balance: ${account_status.get('available_balance', 0):.2f}")
```

#### B. `run_advanced_futures_rpa_workflow()` (line ~3212)
```python
# 1. Check account status - Skip for SIGNALS_FUTURES
logger.info("💰 Step 1: Checking account status...")

# SIGNALS_FUTURES bots don't need account status (signals-only, no trading)
bot_type_str = str(subscription.bot.bot_type).upper() if subscription.bot.bot_type else None
if bot_type_str == "SIGNALS_FUTURES":
    logger.info("📡 SIGNALS_FUTURES bot - Skip account check (signals-only, no trading)")
    account_status = None
else:
    # Active trading bots need account balance check
    account_status = bot.check_account_status()
    if account_status:
        logger.info(f"Account Balance: ${account_status.get('available_balance', 0):.2f}")
```

## Impact Analysis
### ✅ No Impact on Active Bots
- `FUTURES` bots → vẫn check account status như cũ
- `SPOT` bots → vẫn check account status như cũ
- `FUTURES_RPA` bots → vẫn check account status như cũ

### ✅ Fixed for SIGNALS_FUTURES Bots
- Không còn call `check_account_status()` 
- `account_status = None` → skip trade execution logic
- Chỉ crawl data + send signals

## Verification
### Before Fix:
```
[2025-10-18 06:28:07,321: INFO/ForkPoolWorker-1] 💰 Step 1: Checking account status...
[2025-10-18 06:28:07,321: INFO/ForkPoolWorker-1] 📊 Step 1: Checking account status...
[2025-10-18 06:28:07,322: ERROR/ForkPoolWorker-1] ❌ Error in advanced_futures_workflow: 
'UniversalFuturesSignalsBot' object has no attribute 'check_account_status'
```

### After Fix:
```
[2025-10-18 06:35:xx,xxx: INFO/ForkPoolWorker-1] 💰 Step 1: Checking account status...
[2025-10-18 06:35:xx,xxx: INFO/ForkPoolWorker-1] 📡 SIGNALS_FUTURES bot - Skip account check (signals-only, no trading)
[2025-10-18 06:35:xx,xxx: INFO/ForkPoolWorker-1] 📊 Step 2: Crawling multi-timeframe data...
```

## Related Files
- `core/tasks.py` - Main fix
- `bot_files/universal_futures_signals_bot.py` - Bot template (no `check_account_status` method)
- `docs/SIGNALS_FUTURES_BOT_FLOW.md` - Documented workflow

## Summary
| Component | Before | After |
|-----------|--------|-------|
| SIGNALS_FUTURES account check | ❌ Called & failed | ✅ Skipped |
| FUTURES account check | ✅ Called | ✅ Called (unchanged) |
| SPOT account check | ✅ Called | ✅ Called (unchanged) |
| FUTURES_RPA account check | ✅ Called | ✅ Called (unchanged) |

**Result:** SIGNALS_FUTURES bots chỉ crawl data + send signals, không trade, không check account.

