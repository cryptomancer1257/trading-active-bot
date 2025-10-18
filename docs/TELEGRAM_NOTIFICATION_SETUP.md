# Telegram Notification Setup Guide

## Vấn đề
Bot SIGNALS_FUTURES không gửi được Telegram notification vì:
- ❌ `telegram_chat_id` = NULL trong database
- ✅ `social_telegram` = "@chaulaode" (username có rồi)

Logs:
```
[2025-10-18 04:35:46,989: WARNING] No telegram_chat_id found in user settings for user 7
```

## Giải pháp: Start Telegram Bot

### Bước 1: Tìm Telegram Bot
Kiểm tra bot token trong `.env`:
```bash
grep TELEGRAM_BOT_TOKEN .env
```

Hoặc check trong code:
```bash
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('TELEGRAM_BOT_TOKEN'))"
```

### Bước 2: Lấy Bot Username
Sử dụng bot token để query Telegram API:
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

Response sẽ có:
```json
{
  "ok": true,
  "result": {
    "id": 123456789,
    "is_bot": true,
    "first_name": "YourBotName",
    "username": "your_bot_username"  ← Đây là bot username
  }
}
```

### Bước 3: Start Chat với Bot
1. Mở Telegram app
2. Search bot: `@your_bot_username`
3. Nhấn **Start** hoặc gửi message: `/start`

### Bước 4: Bot tự động lưu Chat ID
Telegram service sẽ tự động:
```python
# services/telegram_service.py line 153-156
if user_setting.telegram_chat_id != chat_id:
    user_setting.telegram_chat_id = chat_id  # ← Lưu vào DB
    updated = True
    print(f"📱 Updated chat_id for user {user_name}: {chat_id}")
```

### Bước 5: Verify trong Database
```bash
mysql -h 127.0.0.1 -P 3307 -u botuser -p bot_marketplace \
  -e "SELECT id, social_telegram, telegram_chat_id FROM user_settings WHERE id = 7;"
```

**Trước:**
```
+----+-----------------+------------------+
| id | social_telegram | telegram_chat_id |
+----+-----------------+------------------+
|  7 | @chạulaode      | NULL             |
+----+-----------------+------------------+
```

**Sau khi /start:**
```
+----+-----------------+------------------+
| id | social_telegram | telegram_chat_id |
+----+-----------------+------------------+
|  7 | @chạulaode      | 123456789        |  ← Chat ID đã được lưu!
+----+-----------------+------------------+
```

## Logic trong Code

### 1. Telegram Service xử lý `/start`
```python
# services/telegram_service.py

async def handle_telegram_message(self, body: dict):
    message = body.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))
    user_name = message.get("from", {}).get("username")
    
    # Tìm user theo telegram username
    user_settings = crud.get_users_setting_by_telegram_username(db, telegram_username=user_name)
    
    # Lưu chat_id vào database
    for user_setting in user_settings:
        if user_setting.telegram_chat_id != chat_id:
            user_setting.telegram_chat_id = chat_id  # ← Key step
            db.commit()
    
    if text.startswith("/start"):
        return await self.handle_start_command(chat_id)
```

### 2. Bot gửi notification
```python
# bot_files/universal_futures_signals_bot.py

async def _send_signal_notification(self, signal: Action, analysis: Dict):
    # Notification service cần telegram_chat_id
    results = await self.notification_manager.send_signal(
        signal_type=signal_type,
        symbol=self.trading_pair,
        data=signal_data,
        user_config=self.user_notification_config  # ← Cần có telegram_chat_id
    )
```

### 3. Notification Service check chat_id
```python
# services/telegram_service.py

def send_signal_telegram(self, chat_id: str, signal_data: dict):
    if not chat_id:
        logger.warning(f"No telegram_chat_id found for user")  # ← Lỗi này!
        return
    
    # Gửi message
    self.send_telegram_message(chat_id, formatted_message)
```

## Commands Available

Sau khi `/start`, user có thể dùng:

### `/query_signals`
Liệt kê tất cả bot signals (PASSIVE mode) của user:
```
📊 Signal Bots (PASSIVE)
━━━━━━━━━━━━━━━━━━━
🤖 Bot Name: Universal Futures Signals Entity-006
   Bot ID: 124
   Sub ID: 780
   Rent Date: 15/10 11:16
   
[▶️ Run Manual] [📈 View Stats]
```

### `/query_active`
Liệt kê tất cả bot trading (ACTIVE mode) của user

## Troubleshooting

### Vấn đề: Bot không reply sau `/start`
**Nguyên nhân:** Telegram service không chạy hoặc webhook/polling không hoạt động

**Giải pháp:**
```bash
# Check service đang chạy
ps aux | grep main.py

# Check mode (webhook vs polling)
grep DEVELOPMENT_MODE .env

# Restart service
pkill -f main.py
python3 main.py
```

### Vấn đề: Bot reply nhưng chat_id vẫn NULL
**Nguyên nhân:** Username trong Telegram không khớp với `social_telegram` trong database

**Check:**
```sql
SELECT id, social_telegram FROM user_settings WHERE id = 7;
```

**Fix:**
```sql
UPDATE user_settings 
SET social_telegram = '@correct_username' 
WHERE id = 7;
```

Sau đó gửi `/start` lại.

## Summary

| Bước | Action | Kết quả |
|------|--------|---------|
| 1 | Lấy bot username | `@your_bot_username` |
| 2 | Start chat trên Telegram | Gửi `/start` |
| 3 | Bot lưu chat_id | `telegram_chat_id` ≠ NULL |
| 4 | Bot signals chạy | Notification sent ✅ |

**Current Status:**
- User 7: `@chạulaode` → `telegram_chat_id = NULL` ❌
- Cần: Gửi `/start` cho bot → `telegram_chat_id = <numeric_id>` ✅

