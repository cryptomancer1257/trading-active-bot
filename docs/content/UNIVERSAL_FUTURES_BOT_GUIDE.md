# Universal Futures Bot Template - Developer Guide

## 📋 Overview

The **Universal Futures Bot Template** is a comprehensive, multi-exchange trading bot that supports futures trading across multiple cryptocurrency exchanges with advanced AI analysis and risk management.

### Supported Exchanges

- ✅ **Binance** - World's largest crypto exchange
- ✅ **Bybit** - Popular derivatives platform
- ✅ **OKX** - Unified trading account (requires passphrase)
- ✅ **Bitget** - Copy trading features (requires passphrase)
- ✅ **Huobi/HTX** - Contract-based futures
- ✅ **Kraken** - US-regulated exchange

### Key Features

- 🌐 **Multi-Exchange Support** - Trade on any supported exchange with unified interface
- 🤖 **LLM AI Analysis** - OpenAI, Claude, Gemini for intelligent trading decisions
- 📊 **Multi-Timeframe Analysis** - Analyze multiple timeframes simultaneously
- 💰 **Capital Management** - Intelligent position sizing and risk management
- 🛡️ **Stop Loss & Take Profit** - Automated risk management
- ⚡ **Leverage Trading** - Configurable leverage (1x-125x depending on exchange)
- 📈 **Technical Indicators** - RSI, MACD, SMA, ATR, and more
- 🔄 **Distributed Locking** - Redis-based to prevent duplicate LLM calls

---

## 🚀 Quick Start

### 1. Basic Usage

```python
from bot_files.universal_futures_bot import create_universal_futures_bot

# Create bot for Binance
bot = create_universal_futures_bot(
    exchange='BINANCE',
    user_principal_id='your-icp-principal-id',
    config={
        'trading_pair': 'BTCUSDT',
        'leverage': 10,
        'testnet': True,
        'timeframes': ['30m', '1h', '4h'],
        'use_llm_analysis': True,
        'llm_model': 'openai'
    }
)

# Crawl market data
data = bot.crawl_data()

# Analyze data
analysis = bot.analyze_data(data)

# Generate trading signal
signal = bot.generate_signal(analysis)

print(f"Signal: {signal.action} with {signal.value*100:.1f}% confidence")
print(f"Reason: {signal.reason}")
```

### 2. Using Different Exchanges

```python
# Bybit
bot_bybit = create_universal_futures_bot(
    exchange='BYBIT',
    user_principal_id='your-principal-id',
    config={'trading_pair': 'BTCUSDT'}
)

# OKX (requires passphrase in database)
bot_okx = create_universal_futures_bot(
    exchange='OKX',
    user_principal_id='your-principal-id',
    config={'trading_pair': 'BTC-USDT-SWAP'}  # OKX format
)

# Bitget (requires passphrase in database)
bot_bitget = create_universal_futures_bot(
    exchange='BITGET',
    user_principal_id='your-principal-id',
    config={'trading_pair': 'BTCUSDT'}
)

# Kraken
bot_kraken = create_universal_futures_bot(
    exchange='KRAKEN',
    user_principal_id='your-principal-id',
    config={'trading_pair': 'PF_XBTUSD'}  # Kraken format
)
```

---

## 📖 Configuration Options

### Complete Configuration Example

```python
config = {
    # Exchange & Trading Pair
    'exchange': 'BINANCE',              # Exchange name
    'trading_pair': 'BTCUSDT',          # Trading pair
    'testnet': True,                    # Use testnet/demo
    
    # Position Management
    'leverage': 10,                     # Leverage multiplier (1-125x)
    'stop_loss_pct': 0.02,             # 2% stop loss
    'take_profit_pct': 0.04,           # 4% take profit
    'position_size_pct': 0.1,          # 10% of balance per trade
    
    # Multi-Timeframe Analysis
    'timeframes': ['30m', '1h', '4h'],  # Timeframes to analyze
    'primary_timeframe': '1h',          # Primary decision timeframe
    
    # LLM Configuration
    'use_llm_analysis': True,           # Enable LLM AI analysis
    'llm_model': 'openai',              # LLM provider (openai/claude/gemini)
    'openai_model': 'gpt-4o',          # Specific OpenAI model
    'claude_model': 'claude-3-5-sonnet-20241022',
    'gemini_model': 'gemini-1.5-pro',
    
    # Capital Management
    'base_position_size_pct': 0.02,    # 2% base position
    'max_position_size_pct': 0.10,     # 10% max position
    'max_portfolio_exposure': 0.30,    # 30% total exposure
    'max_drawdown_threshold': 0.20,    # 20% max drawdown
    'sizing_method': 'llm_hybrid',     # Position sizing method
    
    # Technical Indicators (Fallback)
    'rsi_period': 14,                  # RSI period
    'rsi_oversold': 30,                # RSI oversold threshold
    'rsi_overbought': 70,              # RSI overbought threshold
    
    # Bot Identity
    'bot_id': 1,                       # Bot ID in database
    'subscription_id': 123             # Subscription ID
}

bot = create_universal_futures_bot(
    exchange='BINANCE',
    user_principal_id='your-principal-id',
    config=config,
    subscription_id=123
)
```

### Supported Timeframes

- Minutes: `1m`, `3m`, `5m`, `15m`, `30m`
- Hours: `1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- Days+: `1d`, `3d`, `1w`, `1M`

### Recommended Timeframe Combinations

```python
# Scalping (Short-term)
'timeframes': ['5m', '15m', '1h']

# Day Trading
'timeframes': ['30m', '1h', '4h']  # ✅ Recommended (Default)

# Swing Trading
'timeframes': ['4h', '1d', '1w']

# Position Trading
'timeframes': ['1d', '1w', '1M']
```

---

## 🔐 API Key Setup

### Prerequisites

All exchange API keys must be stored in the database with encryption. The bot retrieves keys using the user's ICP Principal ID.

### 1. Store API Keys via API

```bash
# Store Binance testnet keys
curl -X POST 'http://localhost:8000/exchange-credentials/credentials' \
  -H 'Content-Type: application/json' \
  -d '{
    "principal_id": "your-icp-principal-id",
    "exchange": "BINANCE",
    "api_key": "your_binance_api_key",
    "api_secret": "your_binance_api_secret",
    "is_testnet": true
  }'

# Store OKX keys (with passphrase)
curl -X POST 'http://localhost:8000/exchange-credentials/credentials' \
  -H 'Content-Type: application/json' \
  -d '{
    "principal_id": "your-icp-principal-id",
    "exchange": "OKX",
    "api_key": "your_okx_api_key",
    "api_secret": "your_okx_api_secret",
    "passphrase": "your_okx_passphrase",
    "is_testnet": true
  }'
```

### 2. Exchanges Requiring Passphrase

- **OKX**: Requires passphrase for API authentication
- **Bitget**: Requires passphrase for API authentication

Make sure to include the `passphrase` field when storing credentials for these exchanges.

### 3. Testnet URLs

| Exchange | Testnet URL |
|----------|-------------|
| Binance  | `https://testnet.binancefuture.com` |
| Bybit    | `https://api-testnet.bybit.com` |
| OKX      | Same URL (use demo trading flag) |
| Bitget   | Same URL (demo account) |
| Huobi    | `https://api.hbdm.vn` |
| Kraken   | `https://demo-futures.kraken.com` |

---

## 💼 Complete Trading Workflow

### Full Trading Cycle Example

```python
import asyncio
from bot_files.universal_futures_bot import create_universal_futures_bot

async def run_trading_bot():
    """Complete trading workflow example"""
    
    # 1. Initialize bot
    bot = create_universal_futures_bot(
        exchange='BINANCE',
        user_principal_id='your-principal-id',
        config={
            'trading_pair': 'BTCUSDT',
            'leverage': 10,
            'timeframes': ['30m', '1h', '4h'],
            'use_llm_analysis': True,
            'testnet': True
        }
    )
    
    print("✅ Bot initialized")
    
    # 2. Crawl multi-timeframe data
    print("\n📊 Crawling market data...")
    market_data = bot.crawl_data()
    
    if not market_data.get('timeframes'):
        print("❌ Failed to crawl data")
        return
    
    print(f"✅ Crawled {len(market_data['timeframes'])} timeframes")
    
    # 3. Analyze data
    print("\n🔍 Analyzing market...")
    analysis = bot.analyze_data(market_data)
    
    if 'error' in analysis:
        print(f"❌ Analysis error: {analysis['error']}")
        return
    
    current_price = analysis.get('current_price', 0)
    print(f"✅ Current price: ${current_price:.2f}")
    
    # 4. Generate trading signal
    print("\n🎯 Generating trading signal...")
    signal = bot.generate_signal(analysis)
    
    print(f"Signal: {signal.action}")
    print(f"Confidence: {signal.value*100:.1f}%")
    print(f"Reason: {signal.reason}")
    
    # 5. Execute trade if not HOLD
    if signal.action != "HOLD":
        print(f"\n🚀 Executing {signal.action} trade...")
        
        # Setup position with risk management
        result = await bot.setup_position(signal, analysis)
        
        if result['status'] == 'success':
            print("✅ Position opened successfully")
            print(f"   Entry: ${result['entry_price']:.2f}")
            print(f"   Quantity: {result['quantity']}")
            print(f"   Stop Loss: ${result['stop_loss']['price']:.2f}")
            print(f"   Take Profit: ${result['take_profit']['price']:.2f}")
            print(f"   Leverage: {result['leverage']}x")
            
            # Save to database
            # bot.save_transaction_to_db(result)
        else:
            print(f"❌ Trade failed: {result.get('message')}")
    else:
        print("\n⏸️  No trade signal - HOLD")
    
    print("\n✅ Trading cycle completed")

# Run the bot
if __name__ == "__main__":
    asyncio.run(run_trading_bot())
```

### Output Example

```
✅ Bot initialized
   Exchange: BINANCE
   Trading Pair: BTCUSDT
   Leverage: 10x
   Timeframes: ['30m', '1h', '4h']

📊 Crawling market data...
📊 [1/3] Fetching 200 30m candles for BTCUSDT
✅ [1/3] Got 200 30m candles
📊 [2/3] Fetching 168 1h candles for BTCUSDT
✅ [2/3] Got 168 1h candles
📊 [3/3] Fetching 42 4h candles for BTCUSDT
✅ [3/3] Got 42 4h candles
✅ Crawled 3 timeframes

🔍 Analyzing market...
Analyzed 30m: Price 43250.50
Analyzed 1h: Price 43250.50
Analyzed 4h: Price 43250.50
✅ Current price: $43250.50

🎯 Generating trading signal...
🤖 LLM: BUY (75.0%) - Bullish momentum with strong support...
Signal: BUY
Confidence: 75.0%
Reason: [LLM-BINANCE] Bullish momentum with strong support

🚀 Executing BUY trade...
🧠 Calculating optimal position size...
💰 Capital Management:
   Recommended Size: 5.50%
   Risk Level: MEDIUM
   Method: llm_hybrid
🚀 Opening BUY position on BINANCE:
   Symbol: BTCUSDT
   Quantity: 0.127
   Entry: $43250.50
   Leverage: 10x
✅ Market order placed on BINANCE: FILLED
✅ Managed orders placed on BINANCE
✅ Position opened successfully
   Entry: $43250.50
   Quantity: 0.127
   Stop Loss: $42385.49
   Take Profit: $44980.52
   Leverage: 10x

✅ Trading cycle completed
```

---

## 🔧 Exchange-Specific Notes

### Binance
- Most popular exchange with high liquidity
- Wide range of trading pairs
- Best API documentation
- Recommended for beginners

### Bybit
- Popular for derivatives trading
- Good API performance
- Strong for perpetual futures
- V5 API implementation

### OKX
- **Requires API passphrase** ⚠️
- Unified trading account
- Good liquidity
- Symbol format: `BTC-USDT-SWAP`

### Bitget
- **Requires API passphrase** ⚠️
- Copy trading features
- Growing liquidity
- Competitive fees

### Huobi/HTX
- Contract-based futures (integer quantities)
- Symbol format: `BTC-USDT`
- Asian market focus
- Rebranded to HTX

### Kraken
- **Fixed leverage per contract** ⚠️
- US-regulated
- Symbol format: `PF_XBTUSD` (perpetual futures)
- More conservative trading rules

---

## 📊 Advanced Usage

### Custom Position Sizing

```python
config = {
    'base_position_size_pct': 0.03,     # 3% base position
    'max_position_size_pct': 0.15,      # 15% max position
    'max_portfolio_exposure': 0.40,     # 40% total exposure
    'kelly_multiplier': 0.25,           # Kelly criterion multiplier
    'sizing_method': 'llm_hybrid',      # Hybrid LLM + traditional
    'use_llm_capital_management': True  # Enable LLM recommendations
}
```

### Multiple Bots on Different Exchanges

```python
# Portfolio diversification across exchanges
bots = {
    'binance': create_universal_futures_bot('BINANCE', principal_id),
    'bybit': create_universal_futures_bot('BYBIT', principal_id),
    'okx': create_universal_futures_bot('OKX', principal_id),
}

# Run all bots in parallel
import asyncio

async def run_all_bots():
    tasks = []
    for exchange, bot in bots.items():
        task = asyncio.create_task(trade_on_exchange(bot, exchange))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

async def trade_on_exchange(bot, exchange_name):
    print(f"Running bot on {exchange_name}...")
    data = bot.crawl_data()
    analysis = bot.analyze_data(data)
    signal = bot.generate_signal(analysis)
    
    if signal.action != "HOLD":
        result = await bot.setup_position(signal, analysis)
        return result
    
    return {'status': 'hold', 'exchange': exchange_name}

# Execute
results = asyncio.run(run_all_bots())
```

### Custom LLM Configuration

```python
config = {
    'use_llm_analysis': True,
    'llm_model': 'claude',              # Use Claude instead of OpenAI
    'claude_model': 'claude-3-5-sonnet-20241022',
    'llm_capital_weight': 0.50,         # 50% weight on LLM capital recommendations
}
```

---

## 🛠️ Troubleshooting

### Common Issues

#### 1. "No API credentials found"

**Problem**: Bot can't find exchange API keys in database.

**Solution**:
```bash
# Store credentials via API first
curl -X POST 'http://localhost:8000/exchange-credentials/credentials' \
  -H 'Content-Type: application/json' \
  -d '{
    "principal_id": "your-principal-id",
    "exchange": "BINANCE",
    "api_key": "your_key",
    "api_secret": "your_secret",
    "is_testnet": true
  }'
```

#### 2. "Unsupported exchange"

**Problem**: Exchange name not recognized.

**Solution**: Use one of the supported exchanges:
- BINANCE, BYBIT, OKX, BITGET, HUOBI, HTX, KRAKEN

```python
# Correct
bot = create_universal_futures_bot('BINANCE', principal_id)

# Incorrect
bot = create_universal_futures_bot('binance', principal_id)  # Case-sensitive!
```

#### 3. Timestamp errors (-1021)

**Problem**: Local time not synced with exchange server.

**Solution**: Bot automatically syncs time, but you can manually trigger:
```python
bot.futures_client._sync_server_time()
```

#### 4. "Order would immediately trigger"

**Problem**: Stop loss/take profit prices too close to market price.

**Solution**: Increase percentages in config:
```python
config = {
    'stop_loss_pct': 0.03,      # Increase to 3%
    'take_profit_pct': 0.06,    # Increase to 6%
}
```

#### 5. LLM timeout

**Problem**: LLM analysis takes too long.

**Solution**: 
- Bot has 60s timeout and falls back to technical analysis
- Check Redis connection for caching
- Reduce number of timeframes

---

## 📈 Performance Tips

### 1. Optimize Timeframe Selection

```python
# Fast (3 timeframes) - Recommended
'timeframes': ['30m', '1h', '4h']

# Slower (5 timeframes) - More comprehensive
'timeframes': ['15m', '30m', '1h', '4h', '1d']

# Very slow (7+ timeframes) - Not recommended
'timeframes': ['5m', '15m', '30m', '1h', '2h', '4h', '12h']
```

### 2. Use Redis for Caching

Enable Redis to cache LLM results and prevent duplicate API calls:
```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Set environment variable
export REDIS_URL=redis://localhost:6379/0
```

### 3. Mainnet Data Crawling

Bot automatically uses mainnet for accurate market data even when trading on testnet:
```python
# Testnet for trading, mainnet for data
config = {
    'testnet': True  # Safe trading on testnet with real market data
}
```

---

## 🔒 Security Best Practices

1. **Never hardcode API keys** - Always use database storage
2. **Use testnet first** - Test thoroughly before going live
3. **Start with low leverage** - 5x or less for beginners
4. **Enable stop loss** - Always protect your positions
5. **Monitor positions** - Use position monitoring system
6. **Limit exposure** - Don't risk more than 2-5% per trade
7. **Use encryption** - Database stores API keys encrypted
8. **Rotate keys regularly** - Update API keys periodically

---

## 📚 API Reference

### Factory Function

```python
def create_universal_futures_bot(
    exchange: str,
    user_principal_id: str,
    config: Dict[str, Any] = None,
    subscription_id: int = None
) -> UniversalFuturesBot
```

### Main Methods

```python
# Data crawling
data = bot.crawl_data() -> Dict[str, Any]

# Analysis
analysis = bot.analyze_data(data) -> Dict[str, Any]

# Signal generation
signal = bot.generate_signal(analysis) -> Action

# Position setup
result = await bot.setup_position(signal, analysis) -> Dict[str, Any]

# Trade execution
result = bot.execute_trade(signal, analysis) -> Dict[str, Any]
```

### Exchange Client Methods

```python
# Account info
account = bot.futures_client.get_account_info()

# Positions
positions = bot.futures_client.get_position_info(symbol)

# Orders
order = bot.futures_client.create_market_order(symbol, side, quantity)
sl_order = bot.futures_client.create_stop_loss_order(symbol, side, qty, stop_price)
tp_order = bot.futures_client.create_take_profit_order(symbol, side, qty, tp_price)

# Leverage
bot.futures_client.set_leverage(symbol, leverage)

# Market data
ticker = bot.futures_client.get_ticker(symbol)
klines = bot.futures_client.get_klines(symbol, interval, limit)
```

---

## 🎓 Learning Resources

- [Binance Futures API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [Bybit V5 API Documentation](https://bybit-exchange.github.io/docs/v5/intro)
- [OKX API Documentation](https://www.okx.com/docs-v5/en/)
- [Trading Strategy Guide](./TRADING_SYSTEM_SUMMARY.md)
- [Capital Management Guide](./TECHNICAL_ARCHITECTURE.md)
- [LLM Integration Guide](./LLM_INTEGRATION_SUMMARY.md)

---

## 🤝 Contributing

To add support for a new exchange:

1. Create exchange integration in `services/exchange_integrations/`
2. Inherit from `BaseFuturesExchange`
3. Implement all abstract methods
4. Add to `EXCHANGE_REGISTRY` in `exchange_factory.py`
5. Test thoroughly on testnet
6. Submit pull request with documentation

---

## 📄 License

See LICENSE file for details.

---

## ⚠️ Disclaimer

**Cryptocurrency trading involves significant risk of loss.**

- This bot is for educational purposes
- Test thoroughly on testnet before live trading
- Never invest more than you can afford to lose
- Past performance does not guarantee future results
- The developers are not responsible for trading losses

---

## 📞 Support

For issues, questions, or feature requests:
- GitHub Issues: [Link to repo]
- Documentation: [docs/](./README.md)
- Community: [Discord/Telegram]

Happy trading! 🚀📈

