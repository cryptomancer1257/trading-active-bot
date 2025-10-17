# 🔧 Fix: Bot Type Auto-Detection from Template

## 🐛 Problem

Khi tạo bot từ template `universal_futures_signals_bot`, `bot_type` vẫn là `LLM` thay vì `SIGNALS_FUTURES`.

### Root Cause

**Frontend** gửi request với `bot_type = 'LLM'` (mặc định hoặc user chọn).

**Backend logic cũ** trong `core/crud.py`:
```python
# ❌ OLD LOGIC - WRONG
if bot_type and 'bot_type' not in filtered_bot_dict:
    filtered_bot_dict['bot_type'] = bot_type
```

**Vấn đề:**
- Condition `'bot_type' not in filtered_bot_dict` check xem key có tồn tại không
- Nhưng `bot_dict` từ frontend **ĐÃ CÓ** `bot_type = 'LLM'`
- Nên auto-detection **KHÔNG CHẠY** vì key đã tồn tại!

## ✅ Solution

**Force override** `bot_type` dựa trên template name:

```python
# ✅ NEW LOGIC - CORRECT
if bot_type:
    # Force override - template determines bot_type
    filtered_bot_dict['bot_type'] = bot_type
    logger.info(f"✅ Force override bot_type for template '{template}' → {bot_type}")
```

**Key Changes:**
1. ❌ Remove condition: `'bot_type' not in filtered_bot_dict`
2. ✅ **Always override** khi template có mapping
3. ✅ Template name là **source of truth** cho bot_type

## 📊 Comparison

| Scenario | Frontend sends | OLD Logic | NEW Logic |
|----------|---------------|-----------|-----------|
| Template: `universal_futures_signals_bot` | `bot_type='LLM'` | ❌ Keeps `LLM` | ✅ Override to `SIGNALS_FUTURES` |
| Template: `universal_futures_bot` | `bot_type='LLM'` | ❌ Keeps `LLM` | ✅ Override to `FUTURES` |
| Template: `universal_spot_bot` | `bot_type='TECHNICAL'` | ❌ Keeps `TECHNICAL` | ✅ Override to `SPOT` |
| No template | `bot_type='LLM'` | ✅ Keeps `LLM` | ✅ Keeps `LLM` |

## 🎯 Expected Behavior

### When Creating Bot with Template:

**Request:**
```json
{
  "name": "My Signals Bot",
  "template": "universal_futures_signals_bot",
  "bot_type": "LLM"  // ← Frontend value (will be overridden)
}
```

**Result:**
```json
{
  "id": 123,
  "name": "My Signals Bot",
  "bot_type": "SIGNALS_FUTURES",  // ← Overridden by template
  "code_path": "bot_files/universal_futures_signals_bot.py"
}
```

## 🔍 Template Mapping

```python
TEMPLATE_BOT_TYPE_MAPPING = {
    'universal_futures_signals_bot': 'SIGNALS_FUTURES',  # ✨ Signals-only
    'universal_futures_bot': 'FUTURES',                  # Active trading
    'universal_spot_bot': 'SPOT',                        # Spot trading
}
```

## 📝 Implementation Details

**File:** `core/crud.py`  
**Function:** `create_bot()`  
**Lines:** ~267-287

```python
# 🎯 AUTO-SET CODE_PATH for template bots (local files)
template = bot_dict.get('template') or bot_dict.get('templateFile')
if template:
    # Map template name to local file path
    TEMPLATE_FILE_MAPPING = { ... }
    
    # Template-specific bot_type mapping
    TEMPLATE_BOT_TYPE_MAPPING = {
        'universal_futures_signals_bot': 'SIGNALS_FUTURES',
        ...
    }
    
    code_path = TEMPLATE_FILE_MAPPING.get(template)
    if code_path:
        filtered_bot_dict['code_path'] = code_path
        
        # ✅ Force override bot_type based on template
        bot_type = TEMPLATE_BOT_TYPE_MAPPING.get(template)
        if bot_type:
            filtered_bot_dict['bot_type'] = bot_type  # Force override!
            logger.info(f"✅ Force override bot_type for template '{template}' → {bot_type}")
```

## ✅ Testing

### Test Case 1: Create Bot from Template
```python
# Input
bot_data = {
    "template": "universal_futures_signals_bot",
    "bot_type": "LLM"  # Frontend value
}

# Expected Output
{
    "bot_type": "SIGNALS_FUTURES",  # ✅ Overridden
    "code_path": "bot_files/universal_futures_signals_bot.py"
}
```

### Test Case 2: Create Bot without Template
```python
# Input
bot_data = {
    "bot_type": "LLM"  # No template
}

# Expected Output
{
    "bot_type": "LLM"  # ✅ Unchanged
}
```

## 🚀 Impact

**Before Fix:**
- ❌ Template bots có wrong bot_type
- ❌ SIGNALS_FUTURES bots được route như LLM bots
- ❌ Không chạy đúng task handler

**After Fix:**
- ✅ Template bots có correct bot_type
- ✅ SIGNALS_FUTURES bots được route đúng
- ✅ Task scheduling hoạt động chính xác

## 📌 Related Files

1. **`core/crud.py`** - Auto-detection logic
2. **`core/models.py`** - BotType enum
3. **`core/schemas.py`** - BotType schema
4. **`core/tasks.py`** - Task routing based on bot_type
5. **`api/endpoints/bots.py`** - Bot creation endpoints

## 🎉 Summary

**Problem:** Template auto-detection không hoạt động vì frontend đã pass `bot_type`  
**Solution:** Force override `bot_type` dựa trên template name  
**Result:** Template name là source of truth cho bot_type  

---

**Fixed:** 2025-10-18  
**Version:** 1.1  
**Status:** ✅ Production Ready

