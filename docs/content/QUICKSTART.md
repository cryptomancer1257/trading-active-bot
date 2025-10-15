# 🚀 Quick Start - Documentation Server

Start QuantumForge documentation server in **30 seconds**!

## One-Line Install & Run

```bash
cd docs && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && mkdocs serve --dev-addr=0.0.0.0:3002
```

## Step-by-Step (Recommended)

### 1. Navigate to docs folder

```bash
cd /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace/docs
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start server

```bash
mkdocs serve --dev-addr=0.0.0.0:3002
```

### 5. Open browser

```
http://localhost:3002
```

## ✅ Success!

You should see:

```
INFO     -  Building documentation...
INFO     -  Cleaning site directory
INFO     -  Documentation built in 2.34 seconds
INFO     -  [16:20:30] Watching paths for changes: 'docs', 'mkdocs.yml'
INFO     -  [16:20:30] Serving on http://0.0.0.0:3002/
```

**Open**: http://localhost:3002 🎉

---

## 🐳 Docker (Alternative)

```bash
cd docs
docker-compose -f docker-compose.docs.yml up -d
```

**Open**: http://localhost:3002 🎉

---

## 🛑 Stop Server

**Python/MkDocs:**
```bash
Ctrl + C
```

**Docker:**
```bash
docker-compose -f docker-compose.docs.yml down
```

---

## 📝 Next Steps

1. ✅ Browse documentation
2. ✅ Test search functionality
3. ✅ Try dark mode toggle
4. ✅ Edit markdown files (live reload!)
5. ✅ Deploy to production

---

## 🆘 Problems?

### Port 3002 in use?

```bash
# Kill process on port 3002
lsof -ti:3002 | xargs kill -9

# Or use different port
mkdocs serve --dev-addr=0.0.0.0:8080
```

### Missing dependencies?

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Permission denied?

```bash
chmod +x start-docs-server.sh
```

---

**Need help?** → [Full Deployment Guide](./README-DEPLOYMENT.md)

