# 🚀 Start Documentation Server

## Quick Start (Easiest Way)

```bash
cd /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace/docs

# Make script executable
chmod +x serve.sh

# Run server
./serve.sh
```

**That's it!** 🎉

Server will start on: **http://localhost:3002**

---

## Manual Start (Alternative)

```bash
cd /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace/docs

# Activate venv
source venv/bin/activate

# Start server
mkdocs serve --dev-addr=0.0.0.0:3002
```

---

## What You'll See

```
🚀 Starting QuantumForge Documentation Server...

📦 Creating virtual environment...
🔧 Activating virtual environment...
📥 Installing dependencies...

✅ Setup complete!

🌐 Starting server on http://0.0.0.0:3002
📖 Access documentation at: http://localhost:3002

Press Ctrl+C to stop the server

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INFO     -  Building documentation...
INFO     -  Cleaning site directory
INFO     -  Documentation built in 2.34 seconds
INFO     -  [16:20:30] Serving on http://0.0.0.0:3002/
```

---

## Access Points

Once running:

- **Homepage**: http://localhost:3002
- **User Guide**: http://localhost:3002/user-guide/
- **Search**: http://localhost:3002/search
- **API Reference**: http://localhost:3002/API_REFERENCE/

---

## Stop Server

Press `Ctrl + C` in the terminal

---

## Troubleshooting

### Port 3002 in use?

```bash
# Kill process on port 3002
lsof -ti:3002 | xargs kill -9

# Then run server again
./serve.sh
```

### Permission denied?

```bash
chmod +x serve.sh
```

### Missing dependencies?

```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## Project Structure

```
docs/
├── serve.sh               ← Simple start script (use this!)
├── mkdocs.yml            ← MkDocs configuration
├── requirements.txt      ← Python dependencies
├── content/              ← All markdown files
│   ├── index.md
│   ├── user-guide/
│   │   ├── 01-getting-started.md
│   │   ├── 02-creating-your-first-bot.md
│   │   └── ...
│   └── ...
├── stylesheets/
│   └── extra.css
├── javascripts/
│   └── extra.js
├── venv/                 ← Virtual environment (auto-created)
└── site/                 ← Build output (auto-created)
```

---

**Ready to start?** Run: `./serve.sh` 🚀

