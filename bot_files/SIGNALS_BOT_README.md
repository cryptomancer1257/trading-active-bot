# Universal Futures Signals Bot

Trading signals bot that analyzes markets using LLM AI and sends notifications via Telegram/Discord. **No actual trading execution** - signals only.

## Features

✅ **Multi-Exchange Support**: Binance, Bybit, OKX, Bitget, Huobi, Kraken
✅ **LLM AI Analysis**: OpenAI, Claude, Gemini integration
✅ **Multi-Timeframe Analysis**: 1m to 1M timeframes
✅ **Signal Types**: BUY, SELL, HOLD with confidence levels
✅ **Notification Channels**: Telegram, Discord
✅ **Technical Fallback**: RSI, MACD, SMA, ATR indicators
✅ **Redis Caching**: LLM results cached for efficiency
✅ **Distributed Locking**: Prevents duplicate LLM calls

## Architecture

```
Universal Futures Signals Bot
├── Data Crawling (Public API - No credentials needed)
├── Multi-Timeframe Analysis (LLM + Technical)
├── Signal Generation (BUY/SELL/HOLD)
└── Notification Service
    ├── Telegram Bot
    └── Discord Webhook
```

## Signal Format

### Telegram/Discord Message Example

```
🟢 **BUY SIGNAL - BTC/USDT**

**Exchange:** BINANCE
**Timeframe:** 1h
**Confidence:** 85%

**Entry Price:** 50000
**Stop Loss:** 49000
**Take Profit:** 52000
**Risk/Reward:** 1:2
**Strategy:** LLM Multi-timeframe Analysis

**Analysis:**
Strong bullish momentum with RSI oversold confirmation. 
Multi-timeframe alignment shows uptrend across 30m, 1h, and 4h.

⏰ 2025-10-15 08:48:00
```

## Setup Guide

### 1. Environment Variables

Create `.env` file:

```bash
# LLM API Keys (for analysis)
OPENAI_API_KEY=sk-xxx
CLAUDE_API_KEY=sk-ant-xxx
GEMINI_API_KEY=AIzaSyxxx

# Telegram Bot (for notifications)
TELEGRAM_BOT_TOKEN=123456:ABCxxx

# Discord Webhook (for notifications)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0
```

### 2. Get Telegram Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` command
3. Follow prompts to create bot
4. Copy bot token to `TELEGRAM_BOT_TOKEN`
5. Get your chat ID:
   - Message your bot
   - Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Copy `chat.id` value

### 3. Get Discord Webhook URL

1. Open Discord server settings
2. Go to **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Copy webhook URL
5. Paste to `DISCORD_WEBHOOK_URL`

### 4. Bot Configuration

```python
config = {
    # Exchange settings
    'exchange': 'BINANCE',  # or BYBIT, OKX, etc.
    'trading_pair': 'BTCUSDT',
    
    # Analysis settings
    'timeframes': ['30m', '1h', '4h'],
    'primary_timeframe': '1h',
    'use_llm_analysis': True,
    'llm_provider': 'openai',  # openai, claude, gemini
    'llm_model': 'gpt-4o',
    
    # Notification settings
    'notification_config': {
        'telegram': {
            'bot_token': 'xxx',  # Or use env var
            'enabled': True
        },
        'discord': {
            'webhook_url': 'xxx',  # Or use env var
            'enabled': True
        }
    },
    
    # User notification config
    'user_notification_config': {
        'telegram_chat_id': '123456789',  # User's Telegram chat ID
        'discord_webhook_url': 'https://...'  # User's Discord webhook
    }
}
```

## Usage Examples

### Example 1: Basic Signals Bot

```python
from bot_files.universal_futures_signals_bot import create_universal_futures_signals_bot

# Create bot instance
bot = create_universal_futures_signals_bot(
    exchange='BINANCE',
    user_principal_id='your-principal-id',
    config={
        'trading_pair': 'BTCUSDT',
        'timeframes': ['1h', '4h'],
        'use_llm_analysis': True,
        'user_notification_config': {
            'telegram_chat_id': '123456789'
        }
    }
)

# Run analysis (will send notification if BUY/SELL signal)
import pandas as pd
signal = bot.execute_algorithm(
    data=pd.DataFrame(),  # Not used (bot crawls fresh data)
    timeframe='1h'
)

print(f"Signal: {signal.action} (Confidence: {signal.value*100:.1f}%)")
```

### Example 2: Scheduled Signal Bot

```python
import schedule
import time
from bot_files.universal_futures_signals_bot import create_universal_futures_signals_bot

def run_analysis():
    bot = create_universal_futures_signals_bot(
        exchange='BYBIT',
        user_principal_id='your-id',
        config={
            'trading_pair': 'ETHUSDT',
            'timeframes': ['30m', '1h', '4h'],
            'user_notification_config': {
                'telegram_chat_id': '123456789',
                'discord_webhook_url': 'https://...'
            }
        }
    )
    
    signal = bot.execute_algorithm(pd.DataFrame(), '1h')
    print(f"[{datetime.now()}] {signal.action} - {signal.reason}")

# Run every hour
schedule.every().hour.at(":00").do(run_analysis)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### Example 3: Multiple Trading Pairs

```python
trading_pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT']

for pair in trading_pairs:
    bot = create_universal_futures_signals_bot(
        exchange='BINANCE',
        user_principal_id='your-id',
        config={
            'trading_pair': pair,
            'user_notification_config': {
                'telegram_chat_id': '123456789'
            }
        }
    )
    
    signal = bot.execute_algorithm(pd.DataFrame(), '1h')
    print(f"{pair}: {signal.action} ({signal.value*100:.0f}%)")
```

## Notification Service (Reusable)

The notification service can be used independently in any bot:

```python
from services.notification_service import (
    NotificationManager,
    SignalType
)

# Initialize manager
manager = NotificationManager({
    'telegram': {'bot_token': 'xxx'},
    'discord': {'webhook_url': 'yyy'}
})

# Send signal
signal_data = {
    'exchange': 'BINANCE',
    'confidence': 85,
    'entry_price': '50000',
    'stop_loss': '49000',
    'take_profit': '52000',
    'risk_reward': '1:2',
    'reasoning': 'Strong bullish momentum',
    'strategy': 'LLM Analysis',
    'timeframe': '1h'
}

user_config = {
    'telegram_chat_id': '123456789',
    'discord_webhook_url': 'https://...'
}

# Async send
import asyncio
results = asyncio.run(
    manager.send_signal(
        SignalType.BUY,
        'BTC/USDT',
        signal_data,
        user_config
    )
)

print(f"Sent: {results}")  # {'TelegramNotificationService': True, 'DiscordNotificationService': True}
```

### Send Alerts (Not Trading Signals)

```python
# Send general alert
await manager.send_alert(
    title="⚠️ High Volatility Alert",
    message="BTC volatility increased to 8.5%. Consider adjusting position sizes.",
    user_config=user_config,
    priority="high"  # low/normal/high/urgent
)
```

## Supported Exchanges

| Exchange | Status | Testnet | Notes |
|----------|--------|---------|-------|
| Binance  | ✅     | ✅      | Futures supported |
| Bybit    | ✅     | ✅      | Unified account |
| OKX      | ✅     | ✅      | Futures V5 API |
| Bitget   | ✅     | ❌      | Mainnet only |
| Huobi/HTX| ✅     | ❌      | Mainnet only |
| Kraken   | ✅     | ❌      | Mainnet only |

## LLM Providers

| Provider | Models | Notes |
|----------|--------|-------|
| OpenAI   | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | Best for analysis |
| Claude   | claude-3-5-sonnet, claude-3-opus | Great reasoning |
| Gemini   | gemini-2.5-flash, gemini-2.0-flash | Fast & free tier |
| Groq     | mixtral-8x7b, llama-3 | Ultra-fast |
| Cohere   | command-r-plus | Good for finance |

## Database Schema

No database required! Signals bot operates stateless:
- ✅ Crawls fresh data every run
- ✅ Uses Redis for LLM caching only
- ✅ No user credentials needed (public API)
- ✅ Notifications sent via webhooks/bot API

## Comparison: Trading Bot vs Signals Bot

| Feature | Trading Bot | Signals Bot |
|---------|-------------|-------------|
| **Data Crawling** | ✅ | ✅ |
| **LLM Analysis** | ✅ | ✅ |
| **Signal Generation** | ✅ | ✅ |
| **Account Balance Check** | ✅ | ❌ |
| **Capital Management** | ✅ | ❌ |
| **Execute Trades** | ✅ | ❌ |
| **Notifications** | ❌ | ✅ |
| **Requires Exchange API Keys** | ✅ | ❌ |
| **Database Transactions** | ✅ | ❌ |

## Best Practices

### 1. Signal Frequency
- **High-frequency** (1m, 5m): Many signals, more noise
- **Medium-frequency** (15m, 1h): Balanced signals
- **Low-frequency** (4h, 1d): Few but high-quality signals

**Recommended**: 1h primary + 30m/4h confirmation

### 2. Confidence Threshold
```python
# Only notify if confidence > 70%
if signal.value > 0.7 and signal.action != 'HOLD':
    # Send notification
    pass
```

### 3. Multiple Timeframes
```python
# Best practice: 3 timeframes
config = {
    'timeframes': ['30m', '1h', '4h'],  # Short, medium, long
    'primary_timeframe': '1h'
}
```

### 4. Rate Limiting
- Don't spam notifications
- Use Redis caching (60s default)
- Schedule runs (every hour, not every minute)

### 5. Error Handling
```python
try:
    signal = bot.execute_algorithm(pd.DataFrame(), '1h')
except Exception as e:
    # Send error alert
    await manager.send_alert(
        "⚠️ Bot Error",
        f"Signals bot failed: {e}",
        user_config,
        priority="urgent"
    )
```

## Troubleshooting

### Issue: No notifications received

**Solution**: Check configuration
```python
# Verify Telegram bot token
import requests
token = "YOUR_BOT_TOKEN"
response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
print(response.json())  # Should return bot info

# Verify Discord webhook
response = requests.post(
    "YOUR_WEBHOOK_URL",
    json={"content": "Test message"}
)
print(response.status_code)  # Should be 200 or 204
```

### Issue: LLM analysis fails

**Solution**: Check API keys and fallback
```python
# Test LLM service
from services.llm_integration import create_llm_service

llm_service = create_llm_service({
    'openai_api_key': 'sk-xxx'
})

# If fails, bot will fallback to technical analysis automatically
```

### Issue: Data crawling fails

**Solution**: Check exchange status
```python
# Test exchange connection
from services.exchange_integrations import create_futures_exchange

client = create_futures_exchange(
    exchange_name='BINANCE',
    api_key='',  # Empty for public
    api_secret='',
    testnet=False
)

# Test klines
df = client.get_klines('BTCUSDT', '1h')
print(f"Got {len(df)} candles")
```

## Advanced: Custom Notification Templates

```python
# Override message format in NotificationService
class CustomTelegramService(TelegramNotificationService):
    def _format_signal_message(self, signal_type, symbol, data):
        # Your custom format
        message = f"🚀 {signal_type.value} Alert!\n"
        message += f"Symbol: {symbol}\n"
        message += f"Price: {data['entry_price']}\n"
        # ... custom format
        return message

# Use custom service
from services.notification_service import NotificationManager

manager = NotificationManager({'telegram': {'bot_token': 'xxx'}})
manager.services = [CustomTelegramService({'bot_token': 'xxx'})]
```

## FAQ

**Q: Do I need exchange API keys?**
A: No! Signals bot only uses public market data APIs.

**Q: How much does it cost?**
A: Telegram bots are free. Discord webhooks are free. LLM APIs have free tiers (Gemini: free, OpenAI: pay-per-use).

**Q: Can I use this for live trading?**
A: This is signals-only. For live trading, use `universal_futures_bot.py` instead.

**Q: How accurate are the signals?**
A: Depends on LLM model and market conditions. Always backtest and paper trade first!

**Q: Can I add more notification channels?**
A: Yes! Extend `NotificationService` base class for Email, SMS, Slack, etc.

## Support

- 📖 Documentation: `/docs/user-guide/`
- 🐛 Issues: GitHub Issues
- 💬 Community: Discord/Telegram

## License

MIT License - See LICENSE file for details

