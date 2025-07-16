# Multi-Exchange & ML Bot Integration Guide

## Overview

The Trading Bot Marketplace now supports multiple cryptocurrency exchanges and advanced ML/AI trading bots. This guide explains how to use these new features.

## Supported Exchanges

### Current Integrations
1. **Binance** - Full support (spot, futures, margin trading)
2. **Coinbase Pro** - Spot trading support
3. **Kraken** - Spot trading with basic futures support

### Exchange Capabilities

| Exchange | Spot | Futures | Margin | Stop Loss | Take Profit | Advanced Orders |
|----------|------|---------|--------|-----------|-------------|----------------|
| Binance  | ✅   | ✅      | ✅     | ✅        | ✅          | ✅             |
| Coinbase | ✅   | ❌      | ❌     | ✅        | ❌          | ❌             |
| Kraken   | ✅   | ✅      | ✅     | ✅        | ✅          | ✅             |

## Setup and Configuration

### 1. User API Credentials

Users need to configure API credentials for their chosen exchange:

```python
# In user profile or subscription
{
    "api_key": "your_exchange_api_key",
    "api_secret": "your_exchange_api_secret",
    "exchange_type": "BINANCE"  # or COINBASE, KRAKEN
}
```

### 2. API Endpoints

#### Get Supported Exchanges
```bash
GET /api/exchanges/supported
```

#### Validate Credentials
```bash
POST /api/exchanges/validate-credentials
{
    "exchange_name": "BINANCE",
    "api_key": "your_key",
    "api_secret": "your_secret",
    "testnet": true
}
```

#### Test Connection
```bash
POST /api/exchanges/test-connection
# Same payload as validate-credentials
```

#### Get Account Info
```bash
GET /api/exchanges/account-info/BINANCE
```

### 3. Creating Exchange-Specific Subscriptions

```python
subscription_data = {
    "instance_name": "My BTC Bot",
    "bot_id": 1,
    "exchange_type": "BINANCE",  # Choose exchange
    "trading_pair": "BTC/USDT",
    "timeframe": "1h",
    "strategy_config": {...},
    "execution_config": {...},
    "risk_config": {...}
}
```

## ML Bot Development

### Bot Types

The system now supports different bot types:

1. **TECHNICAL** - Traditional technical analysis bots
2. **ML** - Machine Learning bots
3. **DL** - Deep Learning bots (LSTM, CNN, etc.)
4. **LLM** - Large Language Model bots

### Creating an ML Bot

#### 1. Bot Class Structure

```python
from bot_sdk import CustomBot, Action
import numpy as np
import pandas as pd

class MyMLBot(CustomBot):
    def __init__(self, config: Dict[str, Any], api_keys: Dict[str, str]):
        super().__init__(config, api_keys)
        self.bot_name = "ML Price Predictor"
        
        # Load models from config
        if 'models' in config:
            self.load_models(config['models'])
    
    def load_models(self, models_dict):
        """Load ML models"""
        if 'MODEL' in models_dict:
            self.model = models_dict['MODEL']
        if 'SCALER' in models_dict:
            self.scaler = models_dict['SCALER']
    
    def predict_with_model(self, features):
        """Make predictions using loaded model"""
        if self.model and self.scaler:
            scaled_features = self.scaler.transform(features)
            prediction = self.model.predict(scaled_features)
            return prediction
        return None
    
    def analyze_market(self, market_data: pd.DataFrame) -> Action:
        """Main analysis function"""
        # Prepare features
        features = self.prepare_features(market_data)
        
        # Make ML prediction
        prediction = self.predict_with_model(features)
        
        # Convert to trading action
        if prediction > 0.6:
            return Action("BUY", market_data['close'].iloc[-1], "ML Buy Signal")
        elif prediction < 0.4:
            return Action("SELL", market_data['close'].iloc[-1], "ML Sell Signal")
        else:
            return Action("HOLD", market_data['close'].iloc[-1], "ML Neutral")
```

#### 2. Model File Management

When submitting an ML bot, you can upload multiple files:

```python
# File types supported
FileType.CODE      # Python bot code
FileType.MODEL     # Trained ML model
FileType.WEIGHTS   # Model weights
FileType.CONFIG    # Configuration files
FileType.DATA      # Training data or features
```

#### 3. Supported ML Frameworks

- **TensorFlow/Keras** - For deep learning models
- **PyTorch** - For deep learning models
- **Scikit-learn** - For traditional ML models
- **XGBoost** - For gradient boosting
- **LightGBM** - For gradient boosting

### Bot Submission Process

#### 1. Upload Bot Code

```bash
POST /api/bots/{bot_id}/upload-file
Content-Type: multipart/form-data

file: [bot_code.py]
file_type: "CODE"
description: "Main bot logic"
```

#### 2. Upload ML Models

```bash
POST /api/bots/{bot_id}/upload-file
Content-Type: multipart/form-data

file: [model.h5]
file_type: "MODEL"
model_framework: "tensorflow"
model_type: "LSTM"
description: "Price prediction LSTM model"
```

#### 3. Upload Preprocessor

```bash
POST /api/bots/{bot_id}/upload-file
Content-Type: multipart/form-data

file: [scaler.pkl]
file_type: "WEIGHTS"
model_framework: "sklearn"
description: "Feature scaler"
```

## Exchange Integration Development

### Adding New Exchanges

#### 1. Create Exchange Adapter

```python
from exchange_factory import BaseExchange, ExchangeCapabilities

class MyExchangeAdapter(BaseExchange):
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        super().__init__(api_key, api_secret, testnet)
        # Initialize exchange client
        
    def test_connectivity(self) -> bool:
        # Test connection
        pass
        
    def get_current_price(self, symbol: str) -> float:
        # Get price
        pass
        
    # Implement all required methods...
    
    @property
    def capabilities(self) -> ExchangeCapabilities:
        return ExchangeCapabilities(
            spot_trading=True,
            futures_trading=False,
            # ... other capabilities
        )
```

#### 2. Register Exchange

```python
from exchange_factory import ExchangeFactory

ExchangeFactory.register_exchange("MYEXCHANGE", MyExchangeAdapter)
```

### Exchange-Specific Features

#### Symbol Format Conversion

Each exchange uses different symbol formats:

- **Binance**: `BTCUSDT`
- **Coinbase**: `BTC-USD`
- **Kraken**: `XBTUSD`

The adapters handle these conversions automatically.

#### Order Types

Different exchanges support different order types:

```python
# Check exchange capabilities
capabilities = ExchangeFactory.get_exchange_capabilities("BINANCE")
if capabilities.stop_loss_orders:
    # Can use stop loss orders
    exchange.create_stop_loss_order(...)
```

## Real Trading Integration

### Risk Management

All trades are executed with built-in risk management:

1. **Position Sizing** - Based on account balance and risk settings
2. **Stop Loss** - Automatic stop loss orders where supported
3. **Take Profit** - Automatic profit taking
4. **Max Position Size** - Limits on position size

### Trade Execution Flow

1. **Signal Generation** - Bot analyzes market and generates signal
2. **Risk Check** - System validates trade against risk parameters
3. **Balance Check** - Verifies sufficient balance
4. **Order Placement** - Places order on selected exchange
5. **Trade Tracking** - Monitors position for exit conditions

### Performance Monitoring

```python
# Get subscription performance
GET /api/subscriptions/{subscription_id}/performance

{
    "total_trades": 25,
    "winning_trades": 15,
    "losing_trades": 10,
    "win_rate": 60.0,
    "total_pnl": 150.25,
    "total_pnl_percentage": 15.02,
    "average_trade_duration": "2h 30m",
    "max_drawdown": 5.2,
    "sharpe_ratio": 1.8
}
```

## Best Practices

### For Bot Developers

1. **Model Validation** - Always validate models before deployment
2. **Error Handling** - Implement robust error handling
3. **Logging** - Use comprehensive logging for debugging
4. **Testing** - Test bots extensively in testnet/sandbox
5. **Documentation** - Provide clear configuration schemas

### For Users

1. **Start Small** - Begin with small position sizes
2. **Use Testnet** - Test strategies in sandbox environments first
3. **Monitor Performance** - Regularly review bot performance
4. **Risk Management** - Set appropriate stop losses and position limits
5. **Diversification** - Don't put all funds in one bot/exchange

## Troubleshooting

### Common Issues

#### Exchange Connection Failed
```bash
# Check credentials
POST /api/exchanges/validate-credentials

# Test connection
POST /api/exchanges/test-connection
```

#### Model Loading Error
```bash
# Check bot files
GET /api/bots/{bot_id}/files

# Validate models
POST /api/bots/{bot_id}/test
```

#### Trade Execution Failed
- Check account balance
- Verify trading permissions
- Confirm symbol format
- Check minimum order size

### API Rate Limits

Different exchanges have different rate limits:

- **Binance**: 1200 requests/minute
- **Coinbase**: 10 requests/second
- **Kraken**: Variable based on API key level

The system automatically handles rate limiting.

## Security Considerations

1. **API Keys** - Store encrypted, never log in plaintext
2. **Permissions** - Use minimal required permissions
3. **Testnet** - Always test in sandbox first
4. **Code Validation** - Bot code is validated for security
5. **Resource Limits** - CPU and memory limits enforced

## Support

For issues or questions:

1. Check the logs in the admin dashboard
2. Use the test endpoints to validate setup
3. Review bot performance metrics
4. Contact support with specific error messages

---

This multi-exchange and ML integration provides a powerful foundation for building sophisticated trading strategies across multiple platforms. 