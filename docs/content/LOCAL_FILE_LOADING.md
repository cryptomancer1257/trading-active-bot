# 📂 Local File Loading System

## ✅ **GIẢI PHÁP MỚI: HYBRID LOCAL + S3**

Thay vì phức tạp hóa với Development Mode, hệ thống giờ sử dụng **hybrid approach**:

- ✅ **Template Bots** → Load từ local files (fast, debuggable)
- ✅ **User-Uploaded Bots** → Load từ S3 (marketplace, versioning)

---

## 🎯 **CÁCH HOẠT ĐỘNG:**

### **1. Phân loại bot theo `code_path`:**

```python
# Template bots (local files)
code_path = "bot_files/universal_futures_bot.py"
code_path = "bot_files/binance_futures_bot.py"

# User-uploaded bots (S3)
code_path = "bots/123/code/1.0.0/bot.py"
```

### **2. Logic loading trong `initialize_bot`:**

```python
if code_path and not code_path.startswith('bots/'):
    # Template bot → load từ local file
    local_file_path = os.path.join(project_root, code_path)
    if os.path.exists(local_file_path):
        return initialize_bot_from_local_file(subscription, local_file_path)
else:
    # User bot → load từ S3
    return load_from_s3(...)
```

---

## 🔧 **AUTO-SET CODE_PATH KHI TẠO BOT:**

### **Trong `core/crud.py` - `create_bot()`:**

```python
# Map template name → local file path
TEMPLATE_FILE_MAPPING = {
    'universal_futures_bot': 'bot_files/universal_futures_bot.py',
    'binance_futures_bot': 'bot_files/binance_futures_bot.py',
    'binance_futures_rpa_bot': 'bot_files/binance_futures_rpa_bot.py',
    'binance_signals_bot': 'bot_files/binance_signals_bot.py',
}

# Auto-set code_path when creating from template
template = bot_dict.get('template') or bot_dict.get('templateFile')
if template:
    code_path = TEMPLATE_FILE_MAPPING.get(template)
    if code_path:
        filtered_bot_dict['code_path'] = code_path
```

---

## 📊 **FLOW HOÀN CHỈNH:**

### **Flow 1: Tạo bot từ template**

```
User clicks "Create from Template: Universal Futures Bot"
  ↓
Frontend sends: { template: 'universal_futures_bot', ... }
  ↓
Backend (crud.create_bot):
  - Detect template = 'universal_futures_bot'
  - Auto-set code_path = 'bot_files/universal_futures_bot.py'
  - Save to database
  ↓
Database: bot.code_path = 'bot_files/universal_futures_bot.py'
  ↓
Celery executes bot:
  - Check code_path = 'bot_files/universal_futures_bot.py'
  - Path doesn't start with 'bots/' → TEMPLATE BOT
  - Load từ local file: /project_root/bot_files/universal_futures_bot.py
  ↓
Bot runs with LOCAL FILE (fast, debuggable!)
```

### **Flow 2: Upload custom bot**

```
User uploads bot.py via UI
  ↓
Backend (crud.save_bot_with_s3):
  - Upload to S3: bots/123/code/1.0.0/bot.py
  - Set code_path = 'bots/123/code/1.0.0/bot.py'
  ↓
Database: bot.code_path = 'bots/123/code/1.0.0/bot.py'
  ↓
Celery executes bot:
  - Check code_path = 'bots/123/code/1.0.0/bot.py'
  - Path starts with 'bots/' → USER BOT
  - Download từ S3 and execute
  ↓
Bot runs with S3 code (versioned, isolated!)
```

---

## ✅ **LỢI ÍCH:**

### **1. Đơn giản hơn:**
- ❌ Không cần `DEVELOPMENT_MODE` flag
- ❌ Không cần `DEV_BOT_IDS` mapping
- ❌ Không cần environment variables
- ✅ Chỉ cần check `code_path`!

### **2. Debugging dễ dàng:**
- ✅ Template bots luôn load từ local
- ✅ Edit file → Save → Next execution = code mới!
- ✅ Breakpoints hoạt động (PyCharm/VSCode)
- ✅ No S3 upload delay

### **3. Tự động:**
- ✅ Tạo bot từ template → tự động set đúng `code_path`
- ✅ Upload bot mới → tự động dùng S3 path
- ✅ Không cần manual configuration

### **4. Hybrid tốt nhất:**
- ✅ System templates → Local (fast)
- ✅ User uploads → S3 (isolated)
- ✅ Versioning vẫn hoạt động cho user bots
- ✅ Security vẫn đảm bảo

---

## 🎓 **CÁC TEMPLATE ĐƯỢC HỖ TRỢ:**

| Template Name | Local File Path | Exchange Support |
|--------------|----------------|-----------------|
| `universal_futures_bot` | `bot_files/universal_futures_bot.py` | Multi (Binance, Bybit, OKX, Bitget, Huobi, Kraken) |
| `binance_futures_bot` | `bot_files/binance_futures_bot.py` | Binance only |
| `binance_futures_rpa_bot` | `bot_files/binance_futures_rpa_bot.py` | Binance (with RPA) |
| `binance_signals_bot` | `bot_files/binance_signals_bot.py` | Binance signals |

---

## 🔧 **THÊM TEMPLATE MỚI:**

### **Bước 1: Tạo file template**
```bash
touch bot_files/my_new_bot.py
```

### **Bước 2: Update mapping trong `crud.py`**
```python
TEMPLATE_FILE_MAPPING = {
    # ... existing templates
    'my_new_bot': 'bot_files/my_new_bot.py',
    'my_new_bot.py': 'bot_files/my_new_bot.py',
}
```

### **Bước 3: Update frontend `botTemplates`**
```typescript
// frontend/app/creator/forge/page.tsx
const botTemplates = [
  // ... existing templates
  {
    id: 'my_new_bot',
    name: 'My New Bot',
    templateFile: 'my_new_bot.py',
    // ...
  }
]
```

### **Bước 4: Update Zod schema**
```typescript
template: z.enum([
  'universal_futures_bot', 
  'binance_futures_bot',
  'my_new_bot',  // ← Add here
  'custom'
]),
```

**DONE!** Template tự động hoạt động!

---

## 🛠️ **DEBUGGING:**

### **Check code_path của bot:**
```sql
SELECT id, name, code_path FROM bots WHERE id = 55;
```

### **Expected results:**
```
Template bot:
  code_path = 'bot_files/universal_futures_bot.py'

User bot:
  code_path = 'bots/123/code/1.0.0/bot.py'
```

### **Check Celery logs:**
```bash
docker-compose logs celery | grep "LOCAL FILE"
```

**Expected output:**
```
📂 [LOCAL FILE] Loading bot 55 from: bot_files/universal_futures_bot.py
📂 Loading bot from local file: /app/bot_files/universal_futures_bot.py
✅ Found bot class: UniversalFuturesBot
```

---

## 🔄 **MIGRATION CHO EXISTING BOTS:**

Update existing template bots to use local paths:

```sql
-- Update binance futures bots
UPDATE bots 
SET code_path = 'bot_files/binance_futures_bot.py' 
WHERE code_path LIKE '%binance_futures_bot%' 
AND id < 50;  -- Only system templates

-- Update universal futures bots
UPDATE bots 
SET code_path = 'bot_files/universal_futures_bot.py' 
WHERE code_path LIKE '%universal_futures_bot%' 
AND id < 100;  -- Only system templates

-- Verify
SELECT id, name, code_path 
FROM bots 
WHERE code_path LIKE 'bot_files/%';
```

---

## 📦 **DOCKER VOLUMES:**

Docker Compose cần mount bot_files directory:

```yaml
# docker-compose.yml
celery:
  volumes:
    - ./bot_files:/app/bot_files  # ← REQUIRED
    - ./services:/app/services    # For exchange integrations
```

---

## 🎯 **TÓM TẮT:**

| Aspect | Old (Development Mode) | New (Hybrid Local + S3) |
|--------|----------------------|------------------------|
| **Complexity** | High (env vars, flags) | ✅ **Low** (auto-detect) |
| **Setup** | Manual bot ID mapping | ✅ **Automatic** |
| **Templates** | S3 or dev mode | ✅ **Always local** |
| **User Uploads** | S3 | ✅ **S3** (unchanged) |
| **Debugging** | Need dev mode ON | ✅ **Always easy** |
| **Hot Reload** | Need volume mount | ✅ **Built-in** |
| **Versioning** | S3 only | ✅ **User bots only** |

---

## ✨ **KẾT LUẬN:**

**Approach mới ĐƠN GIẢN HƠN VÀ TỐT HƠN NHIỀU!**

- ✅ Không cần development mode flags
- ✅ Templates luôn load từ local (fast + debuggable)
- ✅ User bots vẫn dùng S3 (secure + versioned)
- ✅ Tự động set code_path khi tạo bot
- ✅ Zero configuration required
- ✅ Best of both worlds!

**Đây chính là giải pháp bạn đã đề xuất - và nó HOÀN HẢO!** 🎉

