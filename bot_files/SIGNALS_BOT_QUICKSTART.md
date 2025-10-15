# 🚀 Signals Bot - Quick Start Guide

Get your signals bot running in 5 minutes!

## Prerequisites

- Python 3.9+
- MySQL database
- Redis (optional, for caching)

## Step 1: Environment Setup (2 minutes)

### 1.1 Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send command: `/newbot`
3. Choose a name (e.g., "My Trading Signals Bot")
4. Choose a username (e.g., "my_trading_bot")
5. Copy the bot token (looks like: `123456:ABCdefGHIjklMNOpqrsTUVwxyz`)

### 1.2 Get Your Telegram Chat ID

1. Message your bot (send any text)
2. Open browser and visit:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Replace `<YOUR_BOT_TOKEN>` with your actual token
3. Look for `"chat":{"id":123456789...}`
4. Copy the `id` value (your chat ID)

### 1.3 Setup Discord Webhook (Optional)

1. Open your Discord server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Give it a name (e.g., "Trading Signals")
5. Select a channel
6. Click **Copy Webhook URL**

### 1.4 Configure Environment Variables

Create/edit `.env` file in project root:

```bash
# Required: Telegram Bot Token
TELEGRAM_BOT_TOKEN=123456:ABCdefGHIjklMNOpqrsTUVwxyz

# Optional: Discord Webhook
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy

# Optional: LLM API Keys (for AI analysis)
OPENAI_API_KEY=sk-xxx
CLAUDE_API_KEY=sk-ant-xxx
GEMINI_API_KEY=AIzaSyxxx

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0
```

**Note**: If you don't have LLM keys, bot will use technical analysis (RSI, MACD, SMA).

## Step 2: Database Setup (1 minute)

### 2.1 Run Migration to Create Bot Template

```bash
# Navigate to project directory
cd /path/to/trade-bot-marketplace

# Run migration
mysql -u root -p trading_bot_marketplace < migrations/versions/035_add_signals_bot_template.sql
```

This creates the "Universal Futures Signals Bot" template in your database.

### 2.2 Verify Bot Template

```bash
mysql -u root -p trading_bot_marketplace -e "
SELECT id, name, bot_type, status, llm_provider 
FROM bots 
WHERE name LIKE '%Signals%';
"
```

You should see:
```
+----+-------------------------------+----------+-----------+--------------+
| id | name                          | bot_type | status    | llm_provider |
+----+-------------------------------+----------+-----------+--------------+
| XX | Universal Futures Signals Bot | BACKTEST | published | openai       |
+----+-------------------------------+----------+-----------+--------------+
```

## Step 3: Test the Bot (2 minutes)

### 3.1 Run Test Script

```bash
# Make sure you're in project directory
cd /path/to/trade-bot-marketplace

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows

# Install dependencies (if not already)
pip install aiohttp requests

# Run test
python test_signals_bot.py
```

### 3.2 Follow Test Prompts

The test script will:
1. ✅ Check environment variables
2. ✅ Test Telegram bot connection
3. ✅ Test Discord webhook (if configured)
4. ✅ Create bot instance
5. ✅ Crawl market data
6. ✅ Generate trading signal
7. ✅ Send test notification

**Example Test Output**:
```
======================================================================
 🚀 QuantumForge Signals Bot - Test Suite
======================================================================

======================================================================
 🔧 STEP 1: Testing Environment Variables
======================================================================

📋 Required Variables:
  ✅ TELEGRAM_BOT_TOKEN: 123456:ABC...
  
📋 Optional Variables:
  ✅ OPENAI_API_KEY: sk-proj-3Q...
  ✅ REDIS_URL: redis://red...

✅ Environment variables check passed!

======================================================================
 📱 STEP 2: Testing Telegram Bot Connection
======================================================================

✅ Telegram bot connected successfully!
   Bot Name: My Trading Signals Bot
   Username: @my_trading_bot
   Bot ID: 123456789

======================================================================
 🤖 STEP 4: Creating Signals Bot Instance
======================================================================

📝 Enter your Telegram chat ID (or press Enter to skip): 987654321

🔧 Creating bot with config:
   Exchange: BINANCE
   Trading Pair: BTCUSDT
   Timeframes: ['30m', '1h', '4h']
   LLM: openai
   Telegram: ✅
   Discord: ❌ (No webhook)

✅ Bot created successfully!

======================================================================
 🎯 STEP 6: Testing Signal Generation
======================================================================

🤖 Running analysis for BTCUSDT...
   This may take 30-60 seconds with LLM analysis...

✅ Signal generated!
   Action: BUY
   Confidence: 85.0%
   Reason: [LLM-BINANCE] Strong bullish momentum...

📋 Recommendation Details:
   Entry: 50000
   Stop Loss: 49000
   Take Profit: 52000
   Risk/Reward: 1:2
   Strategy: LLM Multi-timeframe Analysis

📢 Notification should be sent to your configured channels!
   Check your Telegram/Discord for the signal
```

## Step 4: Create Subscription (via UI or API)

### Option A: Via Frontend UI

1. Login to marketplace: `http://localhost:3000`
2. Go to **Bot Marketplace**
3. Find "Universal Futures Signals Bot"
4. Click **View Details**
5. Configure:
   - **Trading Pair**: BTC/USDT (or your choice)
   - **Network**: Mainnet (for accurate data)
   - **Primary Trading Pair**: BTC/USDT
   - **Secondary Trading Pairs**: ETH/USDT, SOL/USDT (optional)
6. Click **Rent Bot** (even if it's free, you need to "subscribe")
7. After rental, go to **Settings** → **Notifications**
8. Add your **Telegram Chat ID**

### Option B: Via API

```bash
curl -X POST http://localhost:8000/marketplace/subscription \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "your-bot-api-key",
    "user_principal_id": "your-principal-id",
    "bot_id": "XX",
    "subscription_start": "2025-10-15T00:00:00",
    "subscription_end": "2025-11-15T00:00:00",
    "notify_default_method": "telegram",
    "trading_pair": "BTC/USDT",
    "secondary_trading_pairs": ["ETH/USDT"],
    "trading_network": "mainnet",
    "is_testnet": false
  }'
```

## Step 5: Schedule Bot Execution

### Option A: Cron Job (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to run every hour at :00 minutes
0 * * * * cd /path/to/project && .venv/bin/python -c "
from bot_files.universal_futures_signals_bot import create_universal_futures_signals_bot
import pandas as pd
bot = create_universal_futures_signals_bot('BINANCE', 'your-principal-id', {
    'trading_pair': 'BTCUSDT',
    'user_notification_config': {'telegram_chat_id': '123456789'}
})
bot.execute_algorithm(pd.DataFrame(), '1h')
"
```

### Option B: Python Schedule Script

Create `run_signals_bot.py`:

```python
import schedule
import time
from bot_files.universal_futures_signals_bot import create_universal_futures_signals_bot
import pandas as pd
import os

def run_bot():
    bot = create_universal_futures_signals_bot(
        exchange='BINANCE',
        user_principal_id='your-principal-id',
        config={
            'trading_pair': 'BTCUSDT',
            'timeframes': ['30m', '1h', '4h'],
            'user_notification_config': {
                'telegram_chat_id': os.getenv('MY_TELEGRAM_CHAT_ID')
            }
        }
    )
    signal = bot.execute_algorithm(pd.DataFrame(), '1h')
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {signal.action} - {signal.reason[:50]}")

# Run every hour
schedule.every().hour.at(":00").do(run_bot)

print("🤖 Signals bot scheduler started. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(60)
```

Run it:
```bash
python run_signals_bot.py
```

### Option C: Celery Task (Recommended for Production)

Already integrated! The bot will run automatically via Celery when subscription is active.

## Troubleshooting

### ❌ Problem: "No module named 'bot_files'"

**Solution**: Make sure you're in the project root directory
```bash
cd /path/to/trade-bot-marketplace
python test_signals_bot.py
```

### ❌ Problem: "Telegram bot not found" (HTTP 404)

**Solution**: Double-check your bot token
```bash
# Test manually
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### ❌ Problem: "No notifications received"

**Solution**: 
1. Verify Telegram chat ID is correct
2. Make sure you've messaged your bot first
3. Check bot logs for errors

### ❌ Problem: "LLM analysis failed"

**Solution**: 
- Bot will automatically fallback to technical analysis (RSI, MACD)
- Check if LLM API key is valid
- Verify API key has sufficient credits

### ❌ Problem: "Data crawling failed"

**Solution**:
- Check internet connection
- Exchange API might be down (check status page)
- Try different exchange or trading pair

## What's Next?

1. ✅ **Monitor Signals**: Check Telegram/Discord for signals
2. ✅ **Configure Multiple Pairs**: Create subscriptions for ETH/USDT, SOL/USDT, etc.
3. ✅ **Adjust Timeframes**: Try different combinations (5m, 15m, 1h, 4h)
4. ✅ **Try Different LLMs**: Switch between OpenAI, Claude, Gemini
5. ✅ **Backtest**: Use historical data to validate signals

## Advanced Configuration

### Multiple Trading Pairs

```python
pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
for pair in pairs:
    bot = create_universal_futures_signals_bot(
        'BINANCE', 'your-id', 
        {'trading_pair': pair, 'user_notification_config': {...}}
    )
    bot.execute_algorithm(pd.DataFrame(), '1h')
```

### Custom Notification Format

See `SIGNALS_BOT_README.md` → "Advanced: Custom Notification Templates"

### Multiple Exchanges

```python
exchanges = ['BINANCE', 'BYBIT', 'OKX']
for exchange in exchanges:
    bot = create_universal_futures_signals_bot(
        exchange, 'your-id',
        {'trading_pair': 'BTCUSDT', ...}
    )
    # Run analysis
```

## Support

- 📖 Full Documentation: `bot_files/SIGNALS_BOT_README.md`
- 🐛 Issues: GitHub Issues
- 💬 Community: Discord/Telegram

**Happy Trading! 🚀📈**

