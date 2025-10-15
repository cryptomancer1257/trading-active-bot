# Shared Template Bot Architecture

## 🎯 Design Decision: Shared Files for Template Bots

**Decision:** Template bots share a single code file. Each bot instance points to the same physical file.

---

## 📊 Architecture Overview

### File Structure
```
bot_files/
  ├── universal_futures_bot.py       ← 1 file, multiple bots use it
  ├── binance_futures_bot.py         ← 1 file, multiple bots use it
  ├── binance_futures_rpa_bot.py
  ├── binance_signals_bot.py
  └── simple_sma_bot.py

Database:
  bot_1: { code_path: "bot_files/universal_futures_bot.py" }
  bot_2: { code_path: "bot_files/universal_futures_bot.py" }  ← Same file!
  bot_3: { code_path: "bot_files/universal_futures_bot.py" }  ← Same file!
```

---

## ✅ Benefits

### 1. **Storage Efficiency**
```
Traditional (1 copy per bot):
  100 bots × 50KB = 5MB

Shared Template:
  100 bots → 1 file = 50KB only
  
Savings: 99% reduction in storage
```

### 2. **Easy Maintenance**
```python
# Fix a bug once → all bots get the fix
def fix_leverage_bug():
    # Edit: bot_files/universal_futures_bot.py
    # Result: All 100 bots using this file are fixed instantly
    pass
```

### 3. **Fast Bot Creation**
```python
# No file copy needed
def create_bot_from_template(template_name):
    # ✅ Just set code_path in database
    bot.code_path = f"bot_files/{template_name}.py"
    # Done! <10ms
    
    # ❌ OLD WAY: Copy file
    # shutil.copy(src, dest)  # ~100ms per bot
```

### 4. **Consistent Behavior**
- All bots using same template version
- No drift between instances
- Predictable behavior

### 5. **Easy Updates**
```bash
# Update template to v2
git pull origin main  # Updates bot_files/universal_futures_bot.py

# All bots automatically use new version on next execution
# No migration needed!
```

---

## 🔧 Implementation

### 1. Bot Creation (API)
```python
# api/endpoints/bots.py

@router.post("/")
def submit_new_bot(bot_in: schemas.BotCreate):
    # Just create database record
    # NO file copy, NO S3 upload
    return crud.create_bot(
        db=db,
        bot=bot_in,
        developer_id=current_user.id
    )
```

### 2. Auto-Set code_path (CRUD)
```python
# core/crud.py

def create_bot(db, bot, developer_id):
    # Check if template is specified
    template = bot.template or bot.templateFile
    
    if template:
        # Map template name → local file path
        TEMPLATE_FILE_MAPPING = {
            'universal_futures_bot': 'bot_files/universal_futures_bot.py',
            'binance_futures_bot': 'bot_files/binance_futures_bot.py',
            # ...
        }
        
        # Set code_path to shared file
        bot.code_path = TEMPLATE_FILE_MAPPING[template]
        logger.info(f"✅ Template bot → {bot.code_path}")
    
    # Save to database
    db_bot = models.Bot(**bot_dict)
    db.add(db_bot)
    db.commit()
    
    return db_bot
```

### 3. Load Bot for Execution (Celery)
```python
# core/tasks.py

def initialize_bot(subscription):
    code_path = subscription.bot.code_path
    
    if code_path and not code_path.startswith('bots/'):
        # Template bot → Load from local file
        project_root = os.path.dirname(os.path.dirname(__file__))
        local_file_path = os.path.join(project_root, code_path)
        
        # Load shared file
        spec = importlib.util.spec_from_file_location("bot_module", local_file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Instantiate bot
        return bot_class(bot_config, api_keys, ...)
    else:
        # Custom bot → Load from S3
        return load_from_s3(...)
```

---

## 🎨 Customization via Config

Each bot instance is customized through database config, NOT code:

### Database Schema
```sql
CREATE TABLE subscriptions (
    id INT PRIMARY KEY,
    bot_id INT,  -- Points to shared template
    user_principal_id VARCHAR(255),
    
    -- ✅ Per-bot configuration
    trading_pair VARCHAR(50),
    execution_config JSON,  -- Trading parameters
    risk_config JSON,       -- Risk management
    is_testnet BOOLEAN,
    
    FOREIGN KEY (bot_id) REFERENCES bots(id)
);
```

### Example Configs
```json
// Bot Instance 1: BTC Aggressive
{
  "trading_pair": "BTC/USDT",
  "execution_config": {
    "leverage": 10,
    "timeframes": ["15m", "1h"],
    "capital_management": {
      "max_position_size": 20,
      "risk_per_trade": 3
    }
  }
}

// Bot Instance 2: ETH Conservative
{
  "trading_pair": "ETH/USDT",
  "execution_config": {
    "leverage": 3,
    "timeframes": ["1h", "4h"],
    "capital_management": {
      "max_position_size": 10,
      "risk_per_trade": 1
    }
  }
}

// Both use: bot_files/universal_futures_bot.py
```

---

## 📊 Current Statistics

**Live System Status:**
```
✅ Template Bots: 14
✅ Shared Files: 2
✅ Average: 7 bots per file

File Usage:
  bot_files/binance_futures_bot.py      → 13 bots
  bot_files/universal_futures_bot.py    → 1 bot
```

**Projected at Scale:**
```
1,000 bots using templates
  Storage: ~200KB (2 files)
  vs. 50MB (1000 copies)
  
  Savings: 99.6% ✅
```

---

## 🔄 Comparison: Template vs Custom Bots

| Feature | Template Bots (Shared) | Custom Bots (Isolated) |
|---------|------------------------|------------------------|
| **File Path** | `bot_files/*.py` | `bots/{dev}/{bot}/*.py` |
| **Storage** | 1 file → N bots | 1 file per bot |
| **Creation Time** | <10ms | ~100ms (file copy) |
| **Updates** | Edit 1 file → all updated | Must update each copy |
| **Customization** | Via config only | Full code control |
| **Upload to S3** | ❌ No | ✅ Yes |
| **Maintenance** | Easy | Complex |
| **Use Case** | Standard strategies | Custom algorithms |

---

## 🚀 Bot Creation Flow

### Template Bot
```
User clicks "Create Bot"
  ↓
Select template: "Universal Futures Bot"
  ↓
Configure: trading_pair, leverage, etc.
  ↓
API: POST /bots/ { template: "universal_futures_bot", ... }
  ↓
Backend: create_bot()
  ↓
Auto-set: code_path = "bot_files/universal_futures_bot.py"
  ↓
Save to database
  ↓
✅ Done! (No file operations)
```

### Custom Bot
```
User clicks "Upload Custom Bot"
  ↓
Upload .py file
  ↓
API: POST /bots/with-code (multipart/form-data)
  ↓
Backend: save_bot_with_s3()
  ↓
Upload file to S3: bots/123/456/v1/custom.py
  ↓
Set: code_path = "bots/123/456/v1/custom.py"
  ↓
Save to database
  ↓
✅ Done! (File in S3)
```

---

## 🛡️ Safety & Isolation

### Process Isolation
Each bot execution runs in its own:
- ✅ Python process (Celery worker)
- ✅ Database session
- ✅ Memory space
- ✅ API key context

**Sharing code file is safe because:**
- Code is read-only
- Each instance has separate config
- State is stored in database, not code
- No global variables between executions

### Example
```python
# bot_files/universal_futures_bot.py

class UniversalFuturesBot:
    def __init__(self, config, api_keys, user_id, subscription_id):
        # ✅ Instance-specific state
        self.trading_pair = config['trading_pair']  # BTC/USDT or ETH/USDT
        self.leverage = config['leverage']          # 5x or 10x
        self.user_id = user_id                      # User A or User B
        self.api_keys = api_keys                    # Different keys
        
        # ✅ Each bot has separate exchange client
        self.futures_client = create_exchange_client(
            config['exchange_type'],
            api_keys
        )
    
    def execute_algorithm(self):
        # ✅ Uses instance-specific config & API keys
        # ✅ No shared state between bots
        pass
```

---

## 📈 Scalability

### Current Scale
```
14 bots → 2 files → 100KB total
```

### At 1,000 Bots
```
1,000 bots → ~5 template files → ~250KB total

Memory:
  1 file loaded × N processes = efficient
  (OS-level file system caching)
  
Performance:
  No degradation with more bots
  Each execution is independent
```

### At 10,000 Bots
```
10,000 bots → ~10 template files → ~500KB total

Still efficient! Scales linearly with templates, not bot count.
```

---

## 🔍 Monitoring

### Check File Usage
```sql
-- See which bots use which files
SELECT 
    code_path,
    COUNT(*) as bot_count
FROM bots
WHERE code_path LIKE 'bot_files/%'
GROUP BY code_path
ORDER BY bot_count DESC;
```

### Find Template Bots
```sql
-- List all template bots
SELECT id, name, code_path, exchange_type
FROM bots
WHERE code_path LIKE 'bot_files/%'
ORDER BY created_at DESC;
```

---

## 🔧 Maintenance Operations

### Update Template
```bash
# 1. Update local file
vim bot_files/universal_futures_bot.py

# 2. Test changes
python -m pytest tests/test_universal_futures_bot.py

# 3. Deploy
git commit -m "Update universal futures bot"
git push

# 4. All bots automatically use new version on next execution
```

### Add New Template
```python
# 1. Create file
# bot_files/my_new_strategy.py

# 2. Register in CRUD
TEMPLATE_FILE_MAPPING = {
    # ...
    'my_new_strategy': 'bot_files/my_new_strategy.py',
}

# 3. Add to frontend templates list
const botTemplates = [
    // ...
    {
        id: 'my_new_strategy',
        name: 'My New Strategy',
        // ...
    }
]
```

---

## ✅ Conclusion

**Shared template approach is optimal for:**
- 📦 **Storage efficiency** (99% savings)
- 🚀 **Fast creation** (<10ms)
- 🔧 **Easy maintenance** (update once → all fixed)
- 📊 **Scalability** (10K+ bots)
- 🎯 **Consistency** (same behavior)

**Custom bot uploads remain available for:**
- 🎨 Full code customization
- 🔬 Experimental strategies
- 🏢 Proprietary algorithms

---

## 📚 Related Files

- **CRUD Logic:** `core/crud.py` → `create_bot()`
- **Task Loader:** `core/tasks.py` → `initialize_bot()`
- **API Endpoint:** `api/endpoints/bots.py` → `submit_new_bot()`
- **Templates:** `bot_files/*.py`
- **Documentation:** `docs/LOCAL_FILE_LOADING.md`

---

*Architecture Approved: October 4, 2025*
*Status: ✅ Production Ready*

