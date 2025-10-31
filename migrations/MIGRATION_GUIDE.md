# Historical Learning Feature - Migration Guide

This guide provides instructions for running **Migration 061** to add historical learning configuration to bots.

## 📋 Overview

**Migration File**: `migrations/versions/061_add_historical_learning_columns.py`

This migration adds 4 new columns to the `bots` table:
- `historical_learning_enabled` (BOOLEAN, default: FALSE) - Enable/disable historical learning
- `historical_transaction_limit` (INT, default: 25) - Number of transactions to analyze (10, 25, or 50)
- `include_failed_trades` (BOOLEAN, default: TRUE) - Include losing trades for learning
- `learning_mode` (VARCHAR(20), default: 'recent') - Learning strategy: `recent`, `best_performance`, or `mixed`

It also adds:
- Check constraints to ensure data integrity
- Indexes for faster historical data queries
- Support for bot learning from past performance

---

## 🚀 Quick Start

### Option 1: Run Migration Directly (Recommended)

```bash
# Navigate to project directory
cd /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace

# Run migration (uses .env for database credentials)
python3 migrations/versions/061_add_historical_learning_columns.py

# Or set environment variables explicitly
DB_HOST=localhost DB_USER=root DB_PASSWORD=yourpass DB_NAME=bot_marketplace \
python3 migrations/versions/061_add_historical_learning_columns.py
```

**Expected Output:**
```
🧠 Starting Historical Learning Configuration Migration...
  1. Adding historical_learning_enabled...
  2. Adding historical_transaction_limit...
  3. Adding include_failed_trades...
  4. Adding learning_mode...
  5. Adding check constraint for transaction_limit...
  6. Adding check constraint for learning_mode...
  7. Adding index on transactions for historical queries...
  8. Adding index on subscriptions for bot lookups...
✅ Migration 061 completed successfully!

📊 Historical Learning Feature Summary:
   • Bots can now learn from past transaction performance
   • Configurable transaction limit: 10, 25, or 50 transactions
   • Learning modes: recent, best_performance, mixed
   • Optimized indexes for fast historical data queries

🚀 Next Steps:
   1. Restart backend server to load new model columns
   2. Enable feature in UI: Strategies tab → Historical Learning
   3. Bots will automatically pass historical data to LLM
```

### Option 2: Using Migration Runner

```bash
# Run all pending migrations
python3 migrations/migration_runner.py

# Or run specific migration
python3 migrations/migration_runner.py 061
```

---

## 🔄 Rollback

If you need to undo the migration:

```bash
# Rollback using Python script
python3 migrations/versions/061_add_historical_learning_columns.py rollback

# Or with explicit credentials
DB_HOST=localhost DB_USER=root DB_PASSWORD=yourpass DB_NAME=bot_marketplace \
python3 migrations/versions/061_add_historical_learning_columns.py rollback
```

**Expected Output:**
```
🔄 Rolling back Historical Learning Configuration Migration...
  1. Dropping index idx_subscriptions_bot_id...
  2. Dropping index idx_transactions_subscription_exit...
  3. Dropping constraints...
  4. Dropping learning_mode column...
  5. Dropping include_failed_trades column...
  6. Dropping historical_transaction_limit column...
  7. Dropping historical_learning_enabled column...
✅ Migration 061 rolled back successfully!
```

---

## 🧪 Testing the Migration

### Step 1: Pre-Migration Check

```bash
# Check current bots table structure
mysql -u <username> -p <database> -e "DESCRIBE bots;" | grep historical

# Should return empty (no historical columns yet)
```

### Step 2: Run Migration

```bash
python3 migrations/versions/061_add_historical_learning_columns.py
```

### Step 3: Post-Migration Verification

```bash
# Verify columns were added
mysql -u <username> -p <database> -e "DESCRIBE bots;" | grep historical

# Expected output:
# historical_learning_enabled    | tinyint(1)  | NO   |     | 0       |       |
# historical_transaction_limit   | int         | NO   |     | 25      |       |
# include_failed_trades          | tinyint(1)  | NO   |     | 1       |       |
# learning_mode                  | varchar(20) | NO   |     | recent  |       |
```

### Step 4: Test with Bot

```sql
-- Enable historical learning for test bot (ID 140)
UPDATE bots 
SET 
  historical_learning_enabled = TRUE,
  historical_transaction_limit = 25,
  include_failed_trades = TRUE,
  learning_mode = 'recent'
WHERE id = 140;

-- Verify update
SELECT 
  id, 
  name, 
  historical_learning_enabled, 
  historical_transaction_limit,
  learning_mode 
FROM bots 
WHERE id = 140;
```

### Step 5: Execute Bot and Check Logs

```bash
# Execute bot (via scheduler or API)
# Check backend logs for:

📚 Loaded 25 historical transactions for learning
   Mode: recent | Limit: 25

# LLM prompt should now include:
╔══════════════════════════════════════════════════════════════════╗
║ 🧠 HISTORICAL TRANSACTIONS (Learn from Past Performance)        ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## 📊 Migration Details

### Database Changes

#### New Columns in `bots` Table

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| `historical_learning_enabled` | BOOLEAN | FALSE | Enable LLM to learn from past transactions |
| `historical_transaction_limit` | INT | 25 | Number of transactions to analyze (10, 25, or 50) |
| `include_failed_trades` | BOOLEAN | TRUE | Include losing trades for learning |
| `learning_mode` | VARCHAR(20) | 'recent' | Learning strategy: recent, best_performance, mixed |

#### New Constraints

1. **Check Constraint on `historical_transaction_limit`**
   - Ensures value is 10, 25, or 50
   - Prevents invalid transaction limits

2. **Check Constraint on `learning_mode`**
   - Ensures value is 'recent', 'best_performance', or 'mixed'
   - Prevents invalid learning modes

#### New Indexes

1. **`idx_transactions_subscription_exit`** on `transactions` table
   - Columns: `(subscription_id, exit_price, status, exit_time DESC)`
   - Purpose: Fast queries for historical transaction retrieval

2. **`idx_subscriptions_bot_id`** on `subscriptions` table
   - Columns: `(bot_id, status)`
   - Purpose: Fast lookups of bot subscriptions

---

## ⚠️ Troubleshooting

### Issue: Migration fails with "column already exists"

**Solution**: This is expected if migration was partially run. The migration script checks for existing columns and skips them.

```bash
# Re-run migration (safe - will skip existing columns)
python3 migrations/versions/061_add_historical_learning_columns.py
```

### Issue: "Duplicate key name" error for indexes

**Solution**: Indexes may already exist from previous migration attempt.

```bash
# Drop indexes manually and re-run
mysql -u <username> -p <database> -e "
  DROP INDEX IF EXISTS idx_subscriptions_bot_id ON subscriptions;
  DROP INDEX IF EXISTS idx_transactions_subscription_exit ON transactions;
"

# Then re-run migration
python3 migrations/versions/061_add_historical_learning_columns.py
```

### Issue: Backend still doesn't recognize new columns

**Solution**: Restart backend to reload SQLAlchemy models.

```bash
# Kill and restart backend
pkill -f "uvicorn"
uvicorn main:app --reload --port 8000

# Or restart Docker container
docker-compose restart backend
```

### Issue: UI Save button still fails

**Checklist**:
1. ✅ Migration completed successfully
2. ✅ Backend restarted (SQLAlchemy models reloaded)
3. ✅ `core/models.py` has historical learning columns
4. ✅ `core/schemas.py` has historical learning fields in `BotUpdate`
5. ✅ Browser cache cleared (hard refresh: Cmd+Shift+R)

---

## 🎯 After Migration

### 1. Restart Backend

```bash
# Restart to load new model columns
uvicorn main:app --reload --port 8000
```

### 2. Enable in UI

1. Navigate to: `http://localhost:3001/creator/entities/140`
2. Click **"Strategies"** tab
3. Scroll down to **"🧠 Historical Learning Configuration"**
4. **Enable** toggle (should turn purple)
5. Select **"🟡 Balanced (25 transactions)"**
6. Click **"💾 Save Configuration"**
7. ✅ Should see: **"Historical learning configuration saved successfully!"**

### 3. Verify Bot Execution

```bash
# Check backend logs when bot executes
tail -f logs/backend.log

# Should see:
📚 Loaded N historical transactions for learning
   Mode: recent | Limit: 25

# LLM prompt should include historical section with:
# - Performance summary (win rate, avg win/loss)
# - Recent transactions list
# - Learning instructions for LLM
```

---

## 📝 Environment Variables

The migration script uses these environment variables from `.env`:

```bash
DB_HOST=localhost      # Database host
DB_PORT=3306          # Database port
DB_USER=root          # Database username
DB_PASSWORD=yourpass  # Database password
DB_NAME=bot_marketplace  # Database name
```

---

## ✅ Success Criteria

After migration:

- [x] All 4 columns added to `bots` table
- [x] Check constraints enforced
- [x] Indexes created for performance
- [x] Backend can save historical learning config
- [x] UI Save button works
- [x] Bots load historical data on execution
- [x] LLM receives historical transactions in prompt

---

## 📚 Related Documentation

- `docs/HISTORICAL_TRANSACTIONS_LEARNING.md` - Feature documentation
- `docs/HISTORICAL_LEARNING_QUICK_START.md` - Quick start guide
- `FIX_HISTORICAL_SAVE.md` - Troubleshooting save issues
- `services/transaction_service.py` - Historical data service
- `services/llm_integration.py` - LLM prompt integration

---

## 🔗 Migration Sequence

This migration is part of the database migration sequence:

- 059_fix_enum_values_lowercase.sql
- 060_fix_bot_prompts_foreign_key.sql
- **061_add_historical_learning_columns.py** ← You are here
- (Future migrations...)

---

**Need Help?** Check `FIX_HISTORICAL_SAVE.md` for detailed troubleshooting or run tests:

```bash
python3 tests/test_historical_save_fix.py
```
