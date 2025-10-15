# 🚀 PyCharm Celery Worker Setup Guide

## ✅ LỢI ÍCH:
- 🐛 **Breakpoints hoạt động 100%**
- 🔍 **Debug trực tiếp** - Step through code
- ⚡ **Live reload** - Thay đổi code tự động apply
- 📊 **Xem variables** real-time
- 🎯 **Không cần Docker** cho development

---

## 🔧 BƯỚC 1: TẠO RUN CONFIGURATION

**PyCharm → Run → Edit Configurations → Add New (+) → Python**

### **Configuration Details:**

```
Name: Celery Worker (Local Dev)

Script path: 
  → Click "Module name" radio button (IMPORTANT!)
  
Module name:
  celery

Parameters:
  -A utils.celery_app worker --loglevel=info --pool=solo --queues=default,bot_execution,futures_trading,maintenance,notifications,bot_execution_signal

Working directory:
  /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace

Environment variables (click folder icon to add):
  DATABASE_URL=mysql+pymysql://botuser:botpassword123@127.0.0.1:3307/bot_marketplace
  REDIS_URL=redis://localhost:6379/0
  OPENAI_API_KEY=<your_key>
  AWS_ACCESS_KEY_ID=<your_key>
  AWS_SECRET_ACCESS_KEY=<your_secret>
  AWS_S3_BUCKET=<your_bucket>
  
Python interpreter: 
  → Chọn venv của project (hoặc system Python)

Emulate terminal in output console:
  ✅ Check this box
```

> 💡 **QUAN TRỌNG**: 
> - Dùng **Module name: celery** thay vì Script path
> - Phải có `--pool=solo` để debugging hoạt động!
> - Environment variables phải match với Docker config

---

## 🗄️ BƯỚC 2: ĐẢM BẢO SERVICES ĐANG CHẠY

Celery cần MySQL và Redis. Chạy chúng qua Docker:

```bash
# Start only database services
docker-compose up -d db redis

# Verify they're running
docker-compose ps
```

Expected output:
```
NAME                              STATUS
trade-bot-marketplace-db-1        Up
trade-bot-marketplace-redis-1     Up
```

---

## 🐛 BƯỚC 3: SET BREAKPOINTS

Bây giờ bạn có thể set breakpoints **BẤT KỲ ĐÂU**:

### **Ví dụ: Debug Universal Futures Bot**

```python
# bot_files/universal_futures_bot.py

def setup_position(self, action: Action, analysis: Dict[str, Any]) -> Dict[str, Any]:
    # ← Click vào line number này để set breakpoint (chấm đỏ xuất hiện)
    logger.info(f"🔍 Setup position called for {action.action}")
    
    # Khi bot chạy tới đây, PyCharm sẽ DỪNG!
    # Bạn có thể:
    # - Xem giá trị của action, analysis
    # - Step Over (F8), Step Into (F7)
    # - Evaluate expressions
    # - Modify variables và continue
    
    symbol = self.trading_pair.replace('/', '')
    # ... rest of code
```

---

## ▶️ BƯỚC 4: START DEBUGGING

### **Option A: Run Mode (không debug)**
```
PyCharm → Run → Run 'Celery Worker (Local Dev)'
```

### **Option B: Debug Mode (có breakpoints)** ✅ RECOMMENDED
```
PyCharm → Run → Debug 'Celery Worker (Local Dev)'
```

**Console Output:**
```
 -------------- celery@your-machine v5.x.x
--- ***** ----- 
-- ******* ---- Darwin-24.5.0-arm64
- *** --- * --- 
- ** ---------- [config]
- ** ---------- .> app:         utils.celery_app:0x...
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 1 (solo)
-- ******* ---- .> task events: OFF
--- ***** ----- 
 -------------- [queues]
                .> bot_execution
                .> default
                .> futures_trading
                .> maintenance
                .> notifications

[tasks]
  . core.tasks.run_bot_logic
  . core.tasks.schedule_active_bots
  ...

[2025-10-04 09:45:00,123: INFO/MainProcess] Connected to redis://localhost:6379/0
[2025-10-04 09:45:00,124: INFO/MainProcess] celery@your-machine ready.
```

---

## 🎯 BƯỚC 5: TRIGGER BOT EXECUTION

### **Method 1: Schedule tự động**
```bash
# Bot sẽ tự động chạy theo schedule
# Wait for next execution (check subscription schedule)
```

### **Method 2: Manual trigger qua API**
```bash
curl -X POST http://localhost:8000/subscriptions/544/trigger
```

### **Method 3: Qua UI**
```
1. Go to http://localhost:3000
2. Navigate to bot subscription
3. Click "Run Now" or wait for schedule
```

**Khi bot execute:**
```
[2025-10-04 09:46:00,000: INFO/MainProcess] Task core.tasks.run_bot_logic[xxx] received
🔧 [DEV MODE] Loading bot 55 from LOCAL FILE...
🔧 [DEV MODE] Loading from: /Users/.../bot_files/universal_futures_bot.py
🔧 [DEV MODE] Found bot class: UniversalFuturesBot
🔧 [DEV MODE] Bot initialized with 4 args

→ BREAKPOINT HIT! PyCharm sẽ dừng tại line bạn set! 🎯
```

---

## 🔥 BƯỚC 6: DEBUGGING WORKFLOW

Khi breakpoint được hit:

### **Debug Panel (bottom):**
```
Debugger
  Frames:
    ├─ setup_position, universal_futures_bot.py:654
    ├─ run_advanced_futures_workflow, tasks.py:2xxx
    └─ run_bot_logic, tasks.py:9xx
    
  Variables:
    self = <UniversalFuturesBot object>
    action = Action(action='BUY', value=0.85, reason='...')
    analysis = {'signal': 'BUY', 'confidence': 0.85, ...}
    symbol = 'BTCUSDT'
    account_info = {'availableBalance': 9253.83, ...}
```

### **Keyboard Shortcuts:**
- **F8**: Step Over (next line)
- **F7**: Step Into (vào trong function)
- **Shift+F8**: Step Out (ra khỏi function)
- **F9**: Resume Program (continue)
- **Cmd+F8**: Toggle Breakpoint

### **Evaluate Expression:**
```python
# Click "Evaluate Expression" hoặc Alt+F8
# Gõ code tùy ý:

account_info['availableBalance'] * 0.1  # Calculate 10% of balance
analysis.get('confidence', 0) > 0.8     # Check condition
self.leverage * 5                        # Do math
```

---

## 📝 HOT RELOAD - LIVE CODE CHANGES

**Thay đổi code không cần restart Celery!**

```python
# Edit bot_files/universal_futures_bot.py

def setup_position(self, action, analysis):
    # Thêm log mới
    logger.info("🔥 NEW CODE - Testing live reload!")
    
    # Thay đổi logic
    if action.action == "BUY":
        logger.info("🚀 BUY signal detected!")
    
    # ... rest of code
```

**Save file → Next bot execution = code mới được dùng!**

> ⚠️ **Lưu ý**: Nếu thay đổi imports hoặc class structure, cần restart Celery worker.

---

## 🛠️ TROUBLESHOOTING

### **Problem 1: ModuleNotFoundError: No module named 'celery'**

**Solution:**
```bash
pip install -r requirements.txt

# Or specifically:
pip install celery redis sqlalchemy pymysql
```

### **Problem 2: Cannot connect to Redis/MySQL**

**Solution:**
```bash
# Make sure Docker services are running
docker-compose up -d db redis

# Check ports
lsof -i :6379  # Redis
lsof -i :3307  # MySQL
```

### **Problem 3: Breakpoints không được hit**

**Causes & Solutions:**

1. **Không dùng `--pool=solo`**
   ```
   Parameters phải có: --pool=solo
   ```

2. **Đang chạy Docker Celery**
   ```bash
   docker-compose stop celery beat
   ```

3. **Bot không được trigger**
   ```
   - Check subscription active
   - Check schedule time
   - Manual trigger qua API
   ```

4. **File không match**
   ```python
   # Check LOCAL_BOT_FILES mapping in tasks.py
   LOCAL_BOT_FILES = {
       55: f"{base_path}/universal_futures_bot.py",
   }
   ```

### **Problem 4: Environment variables không load**

**Solution:**
```
PyCharm Configuration → Environment variables → Click folder icon
Paste từng dòng:
  DATABASE_URL=mysql+pymysql://botuser:botpassword123@127.0.0.1:3307/bot_marketplace
  REDIS_URL=redis://localhost:6379/0
  ...
```

### **Problem 5: Import errors**

**Solution:**
```
Make sure Working directory is project root:
  /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace

NOT:
  /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace/core
```

---

## 🎓 BEST PRACTICES

1. **Always use Debug mode** để có breakpoints
2. **Set breakpoints trước khi trigger** bot
3. **Use logging liberally** để track execution
4. **Commit code thường xuyên** trước khi test
5. **Stop Docker Celery** khi debug local

---

## 📊 PYCHARM vs DOCKER CELERY

| Feature | Docker Celery | PyCharm Celery |
|---------|--------------|----------------|
| Breakpoints | ❌ Không hoạt động | ✅ **100%** |
| Variable Inspection | ❌ Không | ✅ **Full** |
| Step Through Code | ❌ Không | ✅ **F7, F8** |
| Live Reload | ⚠️ Cần volume mount | ✅ **Instant** |
| Setup Effort | ⚠️ Docker config | ✅ **5 phút** |
| Performance | ⚠️ Container overhead | ✅ **Native** |
| Production-like | ✅ Gần giống production | ⚠️ Local only |

**Recommendation:**
- 🔧 **Development**: PyCharm (this guide)
- 🧪 **Testing**: Docker (giống production)
- 🚀 **Production**: Docker/K8s

---

## 🎯 QUICK START CHECKLIST

- [ ] Stop Docker Celery: `docker-compose stop celery beat`
- [ ] Start DB services: `docker-compose up -d db redis`
- [ ] Create PyCharm configuration (Module: celery, --pool=solo)
- [ ] Add environment variables
- [ ] Set breakpoint in bot file
- [ ] Start Debug mode
- [ ] Trigger bot execution
- [ ] BOOM! Breakpoint hit! 🎉

---

## 📚 ADVANCED: MULTIPLE CONFIGURATIONS

Tạo nhiều configurations cho các scenarios khác nhau:

### **1. Celery Worker (All Queues)**
```
Parameters: -A utils.celery_app worker --loglevel=info --pool=solo
```

### **2. Celery Worker (Futures Only)**
```
Parameters: -A utils.celery_app worker --loglevel=info --pool=solo --queues=futures_trading,bot_execution
```

### **3. Celery Worker (Debug Verbose)**
```
Parameters: -A utils.celery_app worker --loglevel=debug --pool=solo
```

### **4. Celery Beat (Scheduler)**
```
Module: celery
Parameters: -A utils.celery_app beat --loglevel=info
```

---

## 🎉 SUCCESS INDICATORS

Khi setup đúng, bạn sẽ thấy:

1. **Celery starts successfully** ✅
   ```
   [INFO/MainProcess] celery@your-machine ready.
   ```

2. **Bot loads from local file** ✅
   ```
   🔧 [DEV MODE] Loading bot 55 from LOCAL FILE...
   🔧 [DEV MODE] Found bot class: UniversalFuturesBot
   ```

3. **Breakpoint is hit** ✅
   ```
   PyCharm highlights the line in blue
   Variables panel shows values
   Debug console is active
   ```

4. **You can step through code** ✅
   ```
   F8 → Next line
   F7 → Into function
   Variables update in real-time
   ```

---

**🚀 HAPPY DEBUGGING! BẢN ĐẶC BIỆT CHO PYCHARM! 🐛🔧**

**Questions? Check logs:**
```bash
# PyCharm Debug Console (bottom panel)
# Or terminal logs if needed
```

**Need help? Error messages will appear in:**
- PyCharm Debug Console
- Variables panel (for exceptions)
- Evaluate Expression (for testing)

