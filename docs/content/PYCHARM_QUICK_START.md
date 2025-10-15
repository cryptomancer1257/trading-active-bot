# ⚡ PyCharm Celery - Quick Start (5 phút)

## 🎯 SETUP NHANH

### 1️⃣ **Tạo Run Configuration**

```
PyCharm → Run → Edit Configurations → + → Python

Name: Celery Worker
Module name: celery  ← Click "Module name" radio!
Parameters: -A utils.celery_app worker --loglevel=info --pool=solo
Working directory: /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace

Environment variables:
DATABASE_URL=mysql+pymysql://botuser:botpassword123@127.0.0.1:3307/bot_marketplace
REDIS_URL=redis://localhost:6379/0
```

### 2️⃣ **Start Debugging**

```
PyCharm → Run → Debug 'Celery Worker'
```

### 3️⃣ **Set Breakpoint**

```python
# bot_files/universal_futures_bot.py:654
# Click vào line number → chấm đỏ xuất hiện
```

### 4️⃣ **Trigger Bot**

```
Subscribe to bot 55 → Wait for schedule → BOOM! 💥
```

---

## 🔥 TẠI SAO DÙNG PYCHARM?

| Feature | Status |
|---------|--------|
| ✅ Breakpoints | **100%** |
| ✅ Step Through Code | F7, F8 |
| ✅ Variable Inspection | Real-time |
| ✅ Live Reload | Instant |
| ✅ No Docker | Native speed |

---

## 📝 SERVICES STATUS

✅ MySQL: Running on port 3307  
✅ Redis: Running on port 6379  
❌ Celery: **STOPPED** (bạn sẽ chạy trong PyCharm)

---

## 🐛 COMMON ISSUES

**Q: Breakpoint không hit?**  
A: Phải có `--pool=solo` trong Parameters!

**Q: Import errors?**  
A: `pip install -r requirements.txt`

**Q: Cannot connect to DB?**  
A: Check `docker-compose ps` → db và redis phải UP

---

## 🎓 KEYBOARD SHORTCUTS

- **F8**: Step Over
- **F7**: Step Into  
- **F9**: Resume
- **Cmd+F8**: Toggle Breakpoint

---

**📚 Full guide: `docs/PYCHARM_CELERY_SETUP.md`**

**🚀 BẮT ĐẦU NGAY!**

