# 🔧 Development Mode Guide

## 📝 Overview

Hệ thống hỗ trợ 2 chế độ load bot code:

### 1. **Production Mode (S3 Storage)** 🏭
- **Khi nào**: Marketplace bots, deployed production
- **Cách thức**: Bot code được upload lên S3 qua UI
- **Versioning**: Mỗi version được lưu riêng trên S3
- **Scaling**: Multi-worker distribution
- **Security**: Isolated user code

### 2. **Development Mode (Local Files)** 🔧
- **Khi nào**: Đang develop/debug bot code
- **Cách thức**: Load trực tiếp từ local filesystem
- **Debugging**: Hỗ trợ breakpoints, live reload
- **Speed**: Không cần upload lên S3
- **Scope**: Chỉ apply cho specific bot IDs

---

## 🚀 Kích Hoạt Development Mode

### **Bước 1: Cấu hình Environment Variables**

Edit `docker-compose.yml` - Celery service:

```yaml
celery:
  environment:
    - DEVELOPMENT_MODE=true          # Enable dev mode
    - DEV_BOT_IDS=55,56,57          # Comma-separated bot IDs
  volumes:
    - ./bot_files:/app/bot_files    # Mount local code
    - ./services:/app/services      # Mount exchange integrations
```

### **Bước 2: Map Bot ID → Local File**

Edit `core/tasks.py` - Function `initialize_bot_from_local`:

```python
LOCAL_BOT_FILES = {
    55: f"{base_path}/universal_futures_bot.py",
    56: f"{base_path}/my_custom_bot.py",
    57: f"{base_path}/another_bot.py",
}
```

### **Bước 3: Restart Celery**

```bash
docker-compose restart celery
```

### **Bước 4: Verify**

Check Celery logs:

```bash
docker-compose logs -f celery | grep "DEV MODE"
```

You should see:
```
🔧 [DEV MODE] Loading bot 55 from LOCAL FILE...
🔧 [DEV MODE] Loading from: /app/bot_files/universal_futures_bot.py
🔧 [DEV MODE] Found bot class: UniversalFuturesBot
🔧 [DEV MODE] Bot initialized with 4 args
```

---

## 🐛 Debugging với Development Mode

### **1. Set Breakpoints**

```python
# bot_files/universal_futures_bot.py

def setup_position(self, action, analysis):
    import pdb; pdb.set_trace()  # ✅ Breakpoint sẽ hoạt động!
    
    # hoặc dùng logging
    logger.info(f"🔍 DEBUG: action={action}, analysis={analysis}")
```

### **2. Attach Debugger (VSCode)**

`.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to Celery",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "/app"
        }
      ]
    }
  ]
}
```

Update `docker-compose.yml`:

```yaml
celery:
  command: python -m debugpy --listen 0.0.0.0:5678 -m celery -A utils.celery_app worker --loglevel=info
  ports:
    - "5678:5678"  # Debugger port
```

### **3. Live Code Changes**

Với local file mounting, mọi thay đổi trong `bot_files/` **TỰ ĐỘNG** được apply!

```bash
# Edit bot_files/universal_futures_bot.py
vim bot_files/universal_futures_bot.py

# Save → Next bot execution sẽ dùng code mới (không cần restart!)
```

> ⚠️ **Lưu ý**: Nếu thay đổi imports hoặc class structure, cần restart Celery:
> ```bash
> docker-compose restart celery
> ```

---

## 🔀 So Sánh 2 Chế Độ

| Feature | Production Mode (S3) | Development Mode (Local) |
|---------|---------------------|------------------------|
| **Use Case** | Marketplace, deployed bots | Development, debugging |
| **Code Source** | S3 bucket | Local filesystem |
| **Upload Required** | ✅ Yes (via UI/API) | ❌ No |
| **Versioning** | ✅ Full versioning | ❌ Single version |
| **Debugging** | ❌ Hard (remote code) | ✅ Easy (local code) |
| **Breakpoints** | ❌ No | ✅ Yes |
| **Live Reload** | ❌ No | ✅ Yes |
| **Multi-Worker** | ✅ Distributed | ⚠️ Need shared volume |
| **Security** | ✅ Isolated | ⚠️ Direct access |
| **Performance** | ⚠️ S3 latency | ✅ Fast (local) |

---

## 📦 Workflow: Dev → Production

### **1. Development Phase** 🔧

```bash
# Enable dev mode
DEVELOPMENT_MODE=true
DEV_BOT_IDS=55

# Edit code locally
vim bot_files/universal_futures_bot.py

# Test with real execution
# → Celery loads from local file
# → Breakpoints work
# → Quick iterations
```

### **2. Testing Phase** 🧪

```bash
# Still in dev mode
# Run multiple test subscriptions
# Check logs, debug issues
# Refine code
```

### **3. Production Deployment** 🚀

```bash
# Upload final version to S3 (via UI or API)
curl -X POST "http://localhost:8000/bots/55/upload" \
  -F "file=@bot_files/universal_futures_bot.py" \
  -F "version=1.0.9"

# Disable dev mode OR remove bot_id from DEV_BOT_IDS
DEVELOPMENT_MODE=false  # All bots use S3

# OR keep dev mode but use different bot IDs
DEV_BOT_IDS=56,57  # Bot 55 now uses S3

# Restart Celery
docker-compose restart celery
```

---

## 🛠️ Advanced: Hybrid Setup

Run **both modes simultaneously**:

```yaml
# docker-compose.yml
services:
  celery-prod:
    # Production Celery (S3)
    environment:
      - DEVELOPMENT_MODE=false
    
  celery-dev:
    # Development Celery (Local files)
    environment:
      - DEVELOPMENT_MODE=true
      - DEV_BOT_IDS=55,56
    volumes:
      - ./bot_files:/app/bot_files
```

Benefits:
- ✅ Production bots unaffected
- ✅ Dev bots get local code
- ✅ Zero downtime testing

---

## 🐞 Troubleshooting

### **Problem 1: Breakpoints không được hit**

**Nguyên nhân**: Bot vẫn load từ S3

**Giải pháp**:
```bash
# Check environment
docker-compose exec celery env | grep DEVELOPMENT_MODE
# Should show: DEVELOPMENT_MODE=true

# Check bot_id mapping
docker-compose logs celery | grep "DEV MODE"
# Should show your bot_id

# Verify file mount
docker-compose exec celery ls -la /app/bot_files/
# Should see universal_futures_bot.py
```

### **Problem 2: Code changes không được apply**

**Nguyên nhân**: Python đã cache module

**Giải pháp**:
```python
# core/tasks.py - initialize_bot_from_local
import importlib
if f"local_bot_{bot_id}" in sys.modules:
    importlib.reload(sys.modules[f"local_bot_{bot_id}"])  # Force reload
```

Or simply restart:
```bash
docker-compose restart celery
```

### **Problem 3: Import errors**

**Nguyên nhân**: Services chưa được mount

**Giải pháp**:
```yaml
# docker-compose.yml
volumes:
  - ./services:/app/services  # ← Add this!
```

---

## 🎯 Recommended Workflow

1. **Always start in Development Mode** for new bots
2. **Test thoroughly** with local files
3. **Use breakpoints and logging** liberally
4. **Upload to S3 only when stable**
5. **Keep dev mode for emergency debugging**

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     DEVELOPMENT MODE                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Developer                                                  │
│      ↓                                                       │
│   Edit bot_files/universal_futures_bot.py  ← Breakpoints!   │
│      ↓                                                       │
│   Docker Volume Mount                                        │
│      ↓                                                       │
│   Celery Worker (DEV_BOT_IDS=55)                           │
│      ├→ Bot 55: Load from /app/bot_files/ ✅               │
│      ├→ Bot 99: Load from S3 (not in list)                 │
│      └→ Bot 100: Load from S3 (not in list)                │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     PRODUCTION MODE                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Developer → UI Upload → S3                                │
│                            ↓                                 │
│                         Celery Worker                        │
│                            ↓                                 │
│                    Download from S3                          │
│                            ↓                                 │
│                      Execute Bot                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Summary

**TẠI SAO dùng S3 làm default?**
- ✅ Marketplace model: Users upload bots
- ✅ Versioning & rollback
- ✅ Multi-worker distribution
- ✅ Security & isolation

**TẠI SAO cần Development Mode?**
- ✅ Fast iteration during development
- ✅ Debugging with breakpoints
- ✅ No upload overhead
- ✅ Live code changes

**KHI NÀO dùng Development Mode?**
- 🔧 Đang develop bot mới
- 🐛 Debug production issues
- 🧪 Testing major changes
- 🚀 Quick prototyping

**KHI NÀO dùng Production Mode?**
- 🏭 Deployed marketplace bots
- 📦 Stable, versioned releases
- 🔒 User-submitted bots (security)
- 📈 Scaling to multiple workers

---

## 🎓 Best Practices

1. **Never enable dev mode for production bots in deployment**
2. **Use dev mode bot_ids ≥ 1000 to avoid conflicts**
3. **Document which bots are in dev mode**
4. **Switch to production mode before sharing bots**
5. **Keep S3 as single source of truth for marketplace**

---

**Happy debugging! 🐛🔧**

