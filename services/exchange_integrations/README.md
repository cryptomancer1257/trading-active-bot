# Exchange Integrations for Universal Futures Bot

Multi-exchange support for futures trading with unified interface.

## Supported Exchanges

| Exchange | Status | API Version | Testnet | Notes |
|----------|--------|-------------|---------|-------|
| **Binance** | ✅ | Futures API | ✅ | Most popular, high liquidity |
| **Bybit** | ✅ | V5 API | ✅ | Popular derivatives platform |
| **OKX** | ✅ | V5 API | ✅ | Requires passphrase |
| **Bitget** | ✅ | V2 API | ✅ | Requires passphrase |
| **Huobi/HTX** | ✅ | Futures API | ✅ | Contract-based (integers) |
| **Kraken** | ✅ | V3 API | ✅ | Fixed leverage, US-regulated |

## Architecture

```
exchange_integrations/
├── __init__.py              # Package exports
├── base_futures_exchange.py # Abstract base class
├── exchange_factory.py      # Factory pattern for exchange selection
├── binance_futures.py       # Binance implementation
├── bybit_futures.py         # Bybit implementation
├── okx_futures.py           # OKX implementation
├── bitget_futures.py        # Bitget implementation
├── huobi_futures.py         # Huobi/HTX implementation
└── kraken_futures.py        # Kraken implementation
```

## Quick Start

### Using the Factory

```python
from services.exchange_integrations import create_futures_exchange

# Create Binance client
binance = create_futures_exchange(
    exchange_name='BINANCE',
    api_key='your_key',
    api_secret='your_secret',
    testnet=True
)

# Create Bybit client
bybit = create_futures_exchange(
    exchange_name='BYBIT',
    api_key='your_key',
    api_secret='your_secret',
    testnet=True
)

# Create OKX client (requires passphrase)
okx = create_futures_exchange(
    exchange_name='OKX',
    api_key='your_key',
    api_secret='your_secret',
    passphrase='your_passphrase',
    testnet=True
)
```

### Using Directly

```python
from services.exchange_integrations.binance_futures import BinanceFuturesIntegration

client = BinanceFuturesIntegration(
    api_key='your_key',
    api_secret='your_secret',
    testnet=True
)

# Get account info
account = client.get_account_info()

# Get positions
positions = client.get_position_info('BTCUSDT')

# Place order
order = client.create_market_order('BTCUSDT', 'BUY', '0.001')
```

## Unified Interface

All exchange clients implement the `BaseFuturesExchange` abstract class with these methods:

### Account & Positions

```python
# Get account information
account_info = client.get_account_info()
# Returns: {'totalWalletBalance': float, 'availableBalance': float, ...}

# Get position information
positions = client.get_position_info(symbol='BTCUSDT')
# Returns: List[FuturesPosition]

# Get positions (alias)
positions = client.get_positions()
```

### Market Data

```python
# Get ticker price
ticker = client.get_ticker('BTCUSDT')
# Returns: {'symbol': str, 'price': str}

# Get kline data
df = client.get_klines('BTCUSDT', '1h', limit=100)
# Returns: DataFrame with columns [timestamp, open, high, low, close, volume]

# Get symbol precision
precision = client.get_symbol_precision('BTCUSDT')
# Returns: {'quantityPrecision': int, 'pricePrecision': int, 'stepSize': str, 'tickSize': str}
```

### Trading

```python
# Set leverage
success = client.set_leverage('BTCUSDT', 10)

# Create market order
order = client.create_market_order('BTCUSDT', 'BUY', '0.001')
# Returns: FuturesOrderInfo

# Create stop loss
sl_order = client.create_stop_loss_order(
    symbol='BTCUSDT',
    side='SELL',
    quantity='0.001',
    stop_price='40000',
    reduce_only=True
)

# Create take profit
tp_order = client.create_take_profit_order(
    symbol='BTCUSDT',
    side='SELL',
    quantity='0.001',
    stop_price='50000',
    reduce_only=True
)

# Create managed orders (SL + TP with partial profit taking)
managed = client.create_managed_orders(
    symbol='BTCUSDT',
    side='SELL',
    quantity='0.001',
    stop_price='40000',
    take_profit_price='50000'
)
```

### Order Management

```python
# Get open orders
orders = client.get_open_orders('BTCUSDT')

# Cancel specific order
success = client.cancel_order('BTCUSDT', order_id='12345')

# Cancel all orders
success = client.cancel_all_orders('BTCUSDT')
```

### Utility

```python
# Test connectivity
is_connected = client.test_connectivity()

# Round quantity to proper precision
rounded_qty = client.round_quantity(0.123456, 'BTCUSDT')

# Normalize symbol format
normalized = client.normalize_symbol('BTC/USDT')
# Returns: 'BTCUSDT' (or exchange-specific format)
```

## Data Classes

### FuturesOrderInfo

```python
@dataclass
class FuturesOrderInfo:
    order_id: str
    client_order_id: str
    symbol: str
    side: str           # 'BUY' or 'SELL'
    type: str           # 'MARKET', 'LIMIT', 'STOP_MARKET', etc.
    quantity: str
    price: str
    status: str         # 'FILLED', 'PENDING', 'CANCELLED', etc.
    executed_qty: str
    time_in_force: str  # 'GTC', 'IOC', 'FOK'
```

### FuturesPosition

```python
@dataclass
class FuturesPosition:
    symbol: str
    side: str           # 'LONG' or 'SHORT'
    size: str
    entry_price: str
    mark_price: str
    pnl: str            # Unrealized PnL
    percentage: str     # PnL percentage
```

## Exchange-Specific Notes

### Binance
- Standard USDT perpetual futures
- Symbol format: `BTCUSDT`
- High liquidity, best API
- **Testnet**: `https://testnet.binancefuture.com`

### Bybit
- Unified trading account (V5 API)
- Symbol format: `BTCUSDT`
- Good derivatives platform
- **Testnet**: `https://api-testnet.bybit.com`

### OKX
- **Requires passphrase** for API auth
- Symbol format for futures: `BTC-USDT-SWAP`
- Unified trading account
- **Demo trading**: Same URL with `x-simulated-trading: 1` header

### Bitget
- **Requires passphrase** for API auth
- Symbol format: `BTCUSDT`
- Growing platform with copy trading
- **Demo trading**: Demo account

### Huobi/HTX
- **Contract-based** futures (integer quantities)
- Symbol format: `BTC-USDT`
- Rebranded from Huobi to HTX
- **Testnet**: `https://api.hbdm.vn`

### Kraken
- **Fixed leverage** per contract (cannot change via API)
- Symbol format: `PF_XBTUSD` (perpetual futures)
- US-regulated exchange
- **Testnet**: `https://demo-futures.kraken.com`

## Adding New Exchanges

To add support for a new exchange:

1. Create new file `your_exchange_futures.py`
2. Inherit from `BaseFuturesExchange`
3. Implement all abstract methods
4. Add to `EXCHANGE_REGISTRY` in `exchange_factory.py`

### Example Template

```python
from .base_futures_exchange import BaseFuturesExchange, FuturesOrderInfo, FuturesPosition
import logging

logger = logging.getLogger(__name__)

class YourExchangeFuturesIntegration(BaseFuturesExchange):
    """Your Exchange Futures API Integration"""
    
    @property
    def exchange_name(self) -> str:
        return "YOUR_EXCHANGE"
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        
        if testnet:
            self.base_url = "https://testnet.yourexchange.com"
        else:
            self.base_url = "https://api.yourexchange.com"
    
    # Implement all abstract methods...
    def test_connectivity(self) -> bool:
        # Implementation
        pass
    
    def get_account_info(self) -> Dict[str, Any]:
        # Implementation
        pass
    
    # ... etc
```

## Error Handling

All methods may raise exceptions:

```python
try:
    order = client.create_market_order('BTCUSDT', 'BUY', '0.001')
except Exception as e:
    logger.error(f"Order failed: {e}")
    # Handle error
```

Common errors:
- `ValueError`: Invalid parameters
- `Exception`: API errors, network issues, authentication failures

## Testing

Test exchange connectivity:

```python
from services.exchange_integrations import create_futures_exchange

# Create client
client = create_futures_exchange('BINANCE', 'key', 'secret', testnet=True)

# Test connectivity
if client.test_connectivity():
    print("✅ Connected successfully")
else:
    print("❌ Connection failed")

# Test account access
try:
    account = client.get_account_info()
    print(f"Balance: {account.get('availableBalance')}")
except Exception as e:
    print(f"Error: {e}")
```

## Performance Considerations

- **Time Sync**: All clients automatically sync with exchange server time
- **Rate Limits**: Respect exchange rate limits (varies by exchange)
- **Caching**: Symbol precision is cached after first fetch
- **Connection Pooling**: Use same client instance for multiple requests

## Security

- API keys are encrypted in database
- Never log sensitive data (keys, secrets)
- Use testnet for development and testing
- Implement proper error handling for production

## Contributing

See main [UNIVERSAL_FUTURES_BOT_GUIDE.md](../../docs/UNIVERSAL_FUTURES_BOT_GUIDE.md) for contribution guidelines.

## License

See LICENSE file for details.

