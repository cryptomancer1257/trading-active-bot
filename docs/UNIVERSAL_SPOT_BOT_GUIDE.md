# Universal Spot Trading Bot Guide

## Overview

The **Universal Spot Bot** is a multi-exchange spot trading bot template that supports:
- ✅ **Multiple Exchanges**: Binance, Bybit, OKX, Bitget, Huobi/HTX, Kraken
- ✅ **Multi-timeframe Analysis**: Analyze multiple timeframes simultaneously
- ✅ **LLM AI Analysis**: OpenAI GPT-4, Claude, Gemini support
- ✅ **Capital Management**: Intelligent position sizing with Kelly Criterion
- ✅ **OCO Orders**: One-Cancels-Other orders for SL/TP (where supported)
- ✅ **No Leverage**: Spot trading only (1x)
- ✅ **Trailing Stop**: Optional trailing stop loss feature

## Key Differences from Futures Bot

### 1. No Leverage
- Spot trading operates at **1x leverage only**
- Position size calculated based on available quote balance
- Less risky than futures trading

### 2. OCO Orders
- Uses **One-Cancels-Other (OCO)** orders for stop loss and take profit
- When one order executes, the other is automatically cancelled
- Supported on Binance, some other exchanges

### 3. Base/Quote Asset Management
- **Base Asset**: The coin you're trading (e.g., BTC, ETH)
- **Quote Asset**: The currency you use to buy/sell (e.g., USDT, BUSD)
- BUY: Spend quote asset to get base asset
- SELL: Sell base asset to get quote asset

### 4. Conservative Capital Management
```python
# Spot-specific settings (lower risk)
'base_position_size_pct': 0.05,      # 5% per trade (vs 2% futures)
'max_position_size_pct': 0.20,       # Max 20% (vs 10% futures)
'max_portfolio_exposure': 0.50,      # Max 50% (vs 30% futures)
'kelly_multiplier': 0.20,            # More conservative (vs 0.25 futures)
```

## Configuration

### Basic Configuration

```python
config = {
    # Exchange Configuration
    'exchange': 'BINANCE',              # BINANCE, BYBIT, OKX, BITGET, HUOBI, KRAKEN
    'trading_pair': 'BTC/USDT',         # Trading pair with slash
    'base_asset': 'BTC',                # Optional: Auto-parsed from trading_pair
    'quote_asset': 'USDT',              # Optional: Auto-parsed from trading_pair
    'testnet': True,                    # Use testnet for testing
    
    # Risk Management
    'stop_loss_pct': 0.02,              # 2% stop loss
    'take_profit_pct': 0.04,            # 4% take profit
    'position_size_pct': 0.10,          # 10% of quote balance per trade
    'min_notional': 10.0,               # Minimum order value ($10)
    
    # Spot-Specific Features
    'use_oco_orders': True,             # Use OCO orders for SL/TP
    'trailing_stop': False,             # Enable trailing stop loss
    'trailing_stop_pct': 0.01,          # 1% trailing distance
    
    # Multi-timeframe Analysis
    'timeframes': ['30m', '1h', '4h'],  # Timeframes to analyze
    'primary_timeframe': '1h',          # Primary decision timeframe
    
    # LLM Configuration
    'use_llm_analysis': True,           # Enable AI analysis
    'llm_provider': 'openai',           # openai, claude, gemini
    'llm_model': 'gpt-4o',              # Specific model
    
    # Capital Management
    'base_position_size_pct': 0.05,
    'max_position_size_pct': 0.20,
    'max_portfolio_exposure': 0.50,
    'sizing_method': 'llm_hybrid'       # llm_hybrid, kelly, fixed, volatility
}
```

## Usage

### 1. Basic Usage with Factory Function

```python
from bot_files.universal_spot_bot import create_universal_spot_bot

# Create bot instance
bot = create_universal_spot_bot(
    exchange='BINANCE',
    user_principal_id='your_principal_id',
    config={
        'trading_pair': 'BTC/USDT',
        'testnet': True,
        'use_llm_analysis': True,
        'llm_provider': 'gemini',
        'llm_model': 'gemini-2.5-flash'
    },
    subscription_id=123
)

# Execute trading cycle
signal = bot.execute_algorithm(data=None, timeframe='1h')

print(f"Signal: {signal.action}")
print(f"Confidence: {signal.value * 100:.1f}%")
print(f"Reason: {signal.reason}")
```

### 2. Manual Instantiation

```python
from bot_files.universal_spot_bot import UniversalSpotBot

config = {
    'exchange': 'BYBIT',
    'trading_pair': 'ETH/USDT',
    'testnet': True,
    'stop_loss_pct': 0.015,
    'take_profit_pct': 0.03,
    'timeframes': ['15m', '1h', '4h'],
    'use_llm_analysis': True
}

bot = UniversalSpotBot(
    config=config,
    user_principal_id='your_principal_id',
    subscription_id=456
)
```

### 3. Check Account Status

```python
# Get account balances and status
account_status = bot.check_account_status()

print(f"Base ({bot.base_asset}): {account_status['base_balance']:.6f}")
print(f"Quote ({bot.quote_asset}): {account_status['quote_balance']:.2f}")
print(f"Total Value: ${account_status['total_value_usdt']:.2f}")
print(f"Current Price: ${account_status['current_price']:.2f}")
```

### 4. Execute Complete Trading Workflow

```python
import asyncio

async def run_spot_bot():
    # 1. Check account status
    account_status = bot.check_account_status()
    if not account_status:
        print("❌ Failed to check account")
        return
    
    # 2. Crawl multi-timeframe data
    multi_tf_data = bot.crawl_data()
    if 'error' in multi_tf_data:
        print(f"❌ Data crawling error: {multi_tf_data['error']}")
        return
    
    # 3. Analyze data
    analysis = bot.analyze_data(multi_tf_data)
    if 'error' in analysis:
        print(f"❌ Analysis error: {analysis['error']}")
        return
    
    # 4. Generate signal
    signal = bot.generate_signal(analysis)
    print(f"📊 Signal: {signal.action} ({signal.value*100:.1f}%)")
    print(f"📝 Reason: {signal.reason}")
    
    # 5. Setup position (if signal is BUY/SELL)
    if signal.action != "HOLD":
        result = await bot.setup_position(signal, analysis)
        
        if result['status'] == 'success':
            print(f"✅ Position opened:")
            print(f"   Action: {result['action']}")
            print(f"   Quantity: {result['quantity']} {bot.base_asset}")
            print(f"   Entry: ${result['entry_price']:.2f}")
            print(f"   Stop Loss: ${result['stop_loss']['price']:.2f}")
            print(f"   Take Profit: ${result['take_profit']['price']:.2f}")
            
            # 6. Save to database
            result['user_principal_id'] = bot.user_principal_id
            result['bot_id'] = bot.bot_id
            result['subscription_id'] = bot.subscription_id
            bot.save_transaction_to_db(result)
        else:
            print(f"❌ Position setup failed: {result.get('message')}")
    else:
        print("⏸️  HOLD - No action taken")

# Run bot
asyncio.run(run_spot_bot())
```

## Supported Exchanges

### 1. Binance (SPOT)
- ✅ Market orders
- ✅ OCO orders (SL/TP)
- ✅ Testnet available
- ✅ High liquidity

### 2. Bybit (SPOT)
- ✅ Market orders
- ✅ Stop loss orders
- ✅ Testnet available
- ✅ Low fees

### 3. OKX (SPOT)
- ✅ Market orders
- ✅ Advanced order types
- ✅ Demo trading
- ✅ Good for Asian markets

### 4. Bitget (SPOT)
- ✅ Market orders
- ✅ Copy trading features
- ✅ Testnet available
- ✅ Growing liquidity

### 5. Huobi/HTX (SPOT)
- ✅ Market orders
- ✅ Conditional orders
- ✅ Testnet available
- ✅ Good for Asian markets

### 6. Kraken (SPOT)
- ✅ Market orders
- ✅ Regulated exchange
- ✅ Good for Europe/US
- ⚠️ Limited testnet

## OCO Orders (One-Cancels-Other)

OCO orders allow you to set both stop loss and take profit simultaneously. When one executes, the other is automatically cancelled.

### How it works:

1. **Buy BTC at market** → Get 0.001 BTC
2. **Place OCO order**:
   - Take Profit: SELL at $70,000 (limit order)
   - Stop Loss: SELL at $65,000 (stop-limit order)
3. If price hits $70,000 → TP executes, SL cancelled
4. If price drops to $65,000 → SL executes, TP cancelled

### Example:

```python
# After BUY order fills
oco_order = spot_client.create_oco_order(
    symbol='BTCUSDT',
    side='SELL',
    quantity='0.001',
    price='70000',              # Take profit price
    stop_price='65000',         # Stop loss trigger
    stop_limit_price='64900'    # Stop limit (slightly below)
)
```

## Capital Management

The bot uses intelligent position sizing based on:

### 1. Fixed Percentage
- Simple: Always use X% of balance
- Example: 10% of $1000 = $100 per trade

### 2. Kelly Criterion
- Optimal sizing based on win rate and risk/reward
- Formula: `f = (p * b - q) / b`
- Where: p = win rate, b = reward/risk, q = 1-p

### 3. Volatility-Based
- Larger positions in low volatility
- Smaller positions in high volatility
- Uses ATR (Average True Range)

### 4. LLM Hybrid (Recommended)
- Combines all methods with LLM confidence
- AI analyzes market conditions
- Most adaptive to changing markets

## Trailing Stop Loss

Trailing stop automatically adjusts as price moves in your favor:

```python
config = {
    'trailing_stop': True,
    'trailing_stop_pct': 0.01  # 1% trailing distance
}
```

**Example:**
- Buy BTC at $65,000
- Trailing stop at 1% = $64,350
- Price rises to $66,000 → Stop adjusts to $65,340
- Price rises to $70,000 → Stop adjusts to $69,300
- If price drops to $69,300 → SELL executed

## Best Practices

### 1. Start with Testnet
```python
config = {'testnet': True}  # Always test first!
```

### 2. Use Small Position Sizes
```python
config = {
    'position_size_pct': 0.05,  # Start with 5%
    'max_position_size_pct': 0.20
}
```

### 3. Enable OCO Orders
```python
config = {'use_oco_orders': True}  # Automatic SL/TP
```

### 4. Multi-timeframe Confirmation
```python
config = {
    'timeframes': ['15m', '1h', '4h'],  # Multiple perspectives
    'primary_timeframe': '1h'
}
```

### 5. Use LLM Analysis
```python
config = {
    'use_llm_analysis': True,
    'llm_provider': 'gemini',        # Cost-effective
    'llm_model': 'gemini-2.5-flash'  # Fast + cheap
}
```

## Common Issues & Solutions

### 1. Insufficient Balance
```
Error: Insufficient USDT balance: $5.00
```
**Solution:** Ensure you have enough quote asset (USDT) for trading

### 2. Minimum Notional
```
Error: Order value $8.00 below minimum $10.00
```
**Solution:** Increase position size or quote balance

### 3. OCO Not Supported
```
Warning: Failed to place OCO order
```
**Solution:** Check if exchange supports OCO orders, or disable:
```python
config = {'use_oco_orders': False}
```

### 4. Insufficient Base Asset (SELL)
```
Error: Insufficient BTC balance: 0.0005
```
**Solution:** Can only SELL if you have the base asset in your account

## Performance Tips

### 1. Optimize Timeframes
- **Scalping**: ['5m', '15m', '1h']
- **Day Trading**: ['15m', '1h', '4h']
- **Swing Trading**: ['1h', '4h', '1d']

### 2. Exchange Selection
- **High Volume**: Binance, Bybit
- **Low Fees**: Bybit, OKX
- **Regulated**: Kraken
- **Asian Markets**: Huobi, OKX

### 3. LLM Model Selection
- **Best Quality**: GPT-4o, Claude Sonnet
- **Best Balance**: Gemini 2.5 Flash
- **Fastest**: GPT-4o Mini, Gemini Flash Lite

## Example Workflows

### Scenario 1: Conservative Spot Trading

```python
bot = create_universal_spot_bot(
    exchange='BINANCE',
    user_principal_id='principal_id',
    config={
        'trading_pair': 'BTC/USDT',
        'testnet': True,
        'stop_loss_pct': 0.02,
        'take_profit_pct': 0.03,
        'position_size_pct': 0.05,      # Only 5%
        'use_oco_orders': True,
        'timeframes': ['1h', '4h', '1d'],
        'use_llm_analysis': True
    }
)
```

### Scenario 2: Aggressive Day Trading

```python
bot = create_universal_spot_bot(
    exchange='BYBIT',
    user_principal_id='principal_id',
    config={
        'trading_pair': 'ETH/USDT',
        'testnet': False,
        'stop_loss_pct': 0.015,
        'take_profit_pct': 0.025,
        'position_size_pct': 0.15,      # 15%
        'use_oco_orders': True,
        'trailing_stop': True,
        'timeframes': ['15m', '1h', '4h'],
        'use_llm_analysis': True,
        'sizing_method': 'llm_hybrid'
    }
)
```

### Scenario 3: Multi-Exchange Portfolio

```python
# Create bots for multiple exchanges
exchanges = ['BINANCE', 'BYBIT', 'OKX']
bots = []

for exchange in exchanges:
    bot = create_universal_spot_bot(
        exchange=exchange,
        user_principal_id='principal_id',
        config={
            'trading_pair': 'BTC/USDT',
            'position_size_pct': 0.05,  # 5% per exchange
            'use_llm_analysis': True
        }
    )
    bots.append(bot)

# Run all bots
for bot in bots:
    signal = bot.execute_algorithm(data=None, timeframe='1h')
    print(f"{bot.exchange_name}: {signal.action}")
```

## Monitoring & Alerts

The bot logs important events:

```python
logger.info(f"✅ SPOT BUY order placed: {order.status}")
logger.info(f"📊 Placing OCO order for SL/TP...")
logger.warning(f"⚠️ Insufficient balance")
logger.error(f"❌ Order failed: {error}")
```

## Database Integration

Transactions are automatically saved to database:

```python
transaction = models.Transaction(
    action='BUY',
    position_side='SPOT',           # Marked as SPOT trade
    symbol='BTCUSDT',
    quantity=Decimal('0.001'),
    entry_price=Decimal('65000'),
    leverage=1,                     # Always 1 for spot
    stop_loss=Decimal('63700'),
    take_profit=Decimal('67600'),
    status='OPEN'
)
```

## Conclusion

The Universal Spot Bot provides a robust, multi-exchange spot trading solution with:
- ✅ Lower risk than futures (no leverage)
- ✅ Intelligent capital management
- ✅ AI-powered analysis
- ✅ Automatic SL/TP with OCO orders
- ✅ Multi-timeframe confirmation

**Start with testnet, use small positions, and gradually increase as you gain confidence!**

---

**Related Documents:**
- [Universal Futures Bot Guide](./UNIVERSAL_FUTURES_BOT_GUIDE.md)
- [Capital Management System](./CAPITAL_MANAGEMENT.md)
- [LLM Integration Guide](./llm_integration_guide.md)
- [Exchange Integration](./EXCHANGE_INTEGRATION.md)

