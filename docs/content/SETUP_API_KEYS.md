# 🔑 API KEYS SETUP GUIDE

Bot đã sẵn sàng chạy! Chỉ cần setup API keys thật:

## 1. 🤖 **OPENAI API KEY**

### Lấy key:
1. Truy cập: https://platform.openai.com/account/api-keys
2. Tạo API key mới
3. Copy key có dạng: `sk-proj-xxxxxxxxxxxxx`

### Set key:
```bash
export OPENAI_API_KEY="sk-proj-your-real-key-here"
```

## 2. 🏦 **BINANCE FUTURES TESTNET API**

### Lấy key:
1. Truy cập: https://testnet.binancefuture.com/
2. Đăng ký/đăng nhập
3. Tạo API Key mới cho Futures
4. Bật **Futures Trading** permissions
5. Copy API Key và Secret Key

### Cập nhật trong bot:
Sửa file `bot_files/binance_futures_bot.py` dòng 1568-1569:

```python
test_api_keys = {
    'api_key': 'YOUR_REAL_API_KEY_HERE',
    'api_secret': 'YOUR_REAL_SECRET_KEY_HERE',
    # ...
}
```

## 3. 🚀 **CHẠY BOT THẬT**

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Set OpenAI key
export OPENAI_API_KEY="sk-proj-your-real-key-here"

# 3. Run bot
python bot_files/binance_futures_bot.py
```

## 4. 🎯 **KẾT QUẢ MONG ĐỢI**

Khi có API keys thật, bot sẽ:
- ✅ Check account balance Binance
- ✅ LLM phân tích 5 timeframes  
- ✅ Generate trading signal BUY/SELL
- ✅ Thực hiện lệnh thật trên Binance Testnet
- ✅ Lưu transaction vào database/file
- ✅ Setup stop loss & take profit tự động

## 5. 🛡️ **SAFETY**

- 🧪 **Testnet**: An toàn, không mất tiền thật
- ⚠️ **Confirmation**: Bot sẽ hỏi trước khi vào lệnh
- 🛑 **Stop Loss**: Tự động đặt SL 2%
- 🎯 **Take Profit**: Tự động đặt TP 4%

## 6. 🔄 **MONITORING**

Sau khi có lệnh, chạy position monitor:
```bash
python position_monitor.py
```

Monitor sẽ:
- 🔍 Check positions mỗi 60 giây
- 🚨 Auto close khi loss > -5%
- 💰 Gợi ý chốt lời khi profit > 3%

---

## 📞 **READY TO GO!**

Bot đã hoàn toàn sẵn sàng. Chỉ cần:
1. Set OpenAI API key thật
2. Set Binance API keys thật  
3. Run: `python bot_files/binance_futures_bot.py`

**🎊 Hệ thống trading tự động hoàn chỉnh!**