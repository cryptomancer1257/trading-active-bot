# Enhanced Trading Bot System Guide

## Overview

The enhanced trading bot system provides a complete framework for developing, deploying, and managing trading bots with advanced features:

- **Enhanced CustomBot Framework** - Complete data processing pipeline
- **AWS S3 Integration** - Scalable bot and model storage
- **Multi-Exchange Support** - Trade on multiple exchanges
- **ML/AI Bot Support** - Advanced machine learning capabilities
- **Real-time Execution** - Complete trading lifecycle management

## Key Enhancements

### 1. Enhanced CustomBot Framework

The new `CustomBot` class provides a complete trading pipeline:

```python
class MyTradingBot(CustomBot):
    def execute_algorithm(self, data: pd.DataFrame, timeframe: str, 
                         subscription_config: Dict[str, Any] = None) -> Action:
        """
        Complete algorithm implementation with preprocessed data
        - data: Fully preprocessed market data with all indicators
        - timeframe: Trading timeframe (1m, 5m, 1h, 1d)
        - subscription_config: User-specific configuration
        """
        # Your algorithm logic here
        return Action("BUY", current_price, "Algorithm signal")
```

#### Complete Flow:
1. **Data Crawling** - Automatic market data fetching from exchange
2. **Data Preprocessing** - Technical indicators, feature engineering
3. **Algorithm Execution** - Your trading logic
4. **Risk Management** - Automatic risk checks
5. **Action Generation** - Standardized trading actions

### 2. AWS S3 Integration

All bot code and ML models are stored in AWS S3 with versioning:

```python
# Upload bot code
bot_manager.upload_bot_to_s3(
    bot_id=123,
    code_content=bot_code,
    version="v1.0.0"
)

# Upload ML model
bot_manager.upload_model_to_s3(
    bot_id=123,
    model_data=model_bytes,
    filename="lstm_model.h5",
    model_type="MODEL",
    framework="tensorflow"
)

# Load bot with all dependencies
bot = bot_manager.load_bot_from_s3(
    bot_id=123,
    user_config=config,
    user_api_keys=api_keys
)
```

#### S3 Storage Structure:
```
s3://trading-bot-storage/
├── bots/
│   ├── {bot_id}/
│   │   ├── code/
│   │   │   └── {version}/
│   │   │       └── bot.py
│   │   ├── models/
│   │   │   └── {version}/
│   │   │       ├── model/
│   │   │       │   └── model.h5
│   │   │       ├── weights/
│   │   │       │   └── scaler.pkl
│   │   │       └── config/
│   │   │           └── config.json
│   │   └── metadata/
│   │       └── {version}/
│   │           └── metadata.json
```

### 3. Multi-Exchange Support

Trade on multiple exchanges with unified API:

```python
# Configuration in subscription
subscription_config = {
    "exchange_type": "BINANCE",  # or COINBASE, KRAKEN
    "trading_pair": "BTC/USDT",
    "timeframe": "1h"
}

# Bot automatically gets exchange client
class MyBot(CustomBot):
    def execute_algorithm(self, data, timeframe, subscription_config):
        # Access exchange client
        account_info = self.get_account_info()
        balance = self.get_balance("USDT")
        current_price = self.get_current_price()
        
        # Your trading logic
        return Action("BUY", current_price, "Signal")
```

### 4. ML/AI Bot Development

Enhanced support for ML/AI bots:

```python
class MLBot(CustomBot):
    def __init__(self, config, api_keys):
        super().__init__(config, api_keys)
        self.bot_type = "ML"
        
        # Models are automatically loaded from S3
        if 'models' in config:
            self.model = config['models']['MODEL']
            self.scaler = config['models']['SCALER']
    
    def execute_algorithm(self, data, timeframe, subscription_config):
        # Prepare features
        features = self.prepare_ml_features(data)
        
        # Make prediction
        prediction = self.model.predict(self.scaler.transform(features))
        
        # Convert to trading action
        if prediction > 0.7:
            return Action("BUY", data['close'].iloc[-1], "ML Buy Signal")
        elif prediction < 0.3:
            return Action("SELL", data['close'].iloc[-1], "ML Sell Signal")
        else:
            return Action("HOLD", data['close'].iloc[-1], "ML Hold Signal")
```

## Bot Development Process

### 1. Traditional Technical Analysis Bot

```python
from bot_sdk import CustomBot, Action
import pandas as pd

class RSIBot(CustomBot):
    def __init__(self, config, api_keys):
        super().__init__(config, api_keys)
        self.bot_name = "RSI Trading Bot"
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.rsi_overbought = config.get('rsi_overbought', 70)
    
    def execute_algorithm(self, data, timeframe, subscription_config):
        # Data already includes RSI indicator
        current_rsi = data['rsi'].iloc[-1]
        current_price = data['close'].iloc[-1]
        
        if current_rsi < self.rsi_oversold:
            return Action("BUY", current_price, f"RSI oversold: {current_rsi:.2f}")
        elif current_rsi > self.rsi_overbought:
            return Action("SELL", current_price, f"RSI overbought: {current_rsi:.2f}")
        else:
            return Action("HOLD", current_price, f"RSI neutral: {current_rsi:.2f}")
```

### 2. Machine Learning Bot

```python
from bot_sdk import CustomBot, Action
import numpy as np

class LSTMBot(CustomBot):
    def __init__(self, config, api_keys):
        super().__init__(config, api_keys)
        self.bot_name = "LSTM Price Predictor"
        self.bot_type = "ML"
        self.sequence_length = config.get('sequence_length', 60)
        
        # Load models from S3
        if 'models' in config:
            self.model = config['models']['MODEL']
            self.scaler = config['models']['SCALER']
    
    def execute_algorithm(self, data, timeframe, subscription_config):
        # Prepare features for LSTM
        features = self.prepare_lstm_features(data)
        
        # Make prediction
        prediction = self.model.predict(features)
        confidence = abs(prediction[0][0])
        
        if prediction[0][0] > 0.02 and confidence > 0.7:
            return Action("BUY", data['close'].iloc[-1], f"LSTM prediction: {prediction[0][0]:.4f}")
        elif prediction[0][0] < -0.02 and confidence > 0.7:
            return Action("SELL", data['close'].iloc[-1], f"LSTM prediction: {prediction[0][0]:.4f}")
        else:
            return Action("HOLD", data['close'].iloc[-1], f"LSTM uncertain: {prediction[0][0]:.4f}")
    
    def prepare_lstm_features(self, data):
        # Prepare features for LSTM model
        features = data[['open', 'high', 'low', 'close', 'volume']].values
        scaled_features = self.scaler.transform(features)
        
        # Create sequences
        sequence = scaled_features[-self.sequence_length:]
        return sequence.reshape(1, self.sequence_length, -1)
```

## Deployment Process

### 1. Developer Submits Bot

```python
# 1. Create bot record
bot_data = {
    "name": "My Trading Bot",
    "description": "Advanced trading strategy",
    "bot_type": "ML",
    "category_id": 1,
    "price_per_month": 29.99
}

# 2. Upload bot code to S3
bot_manager.upload_bot_to_s3(
    bot_id=bot.id,
    code_content=bot_code,
    version="v1.0.0"
)

# 3. Upload ML models (if any)
bot_manager.upload_model_to_s3(
    bot_id=bot.id,
    model_data=model_bytes,
    filename="model.h5",
    model_type="MODEL",
    framework="tensorflow"
)

# 4. Upload preprocessor
bot_manager.upload_model_to_s3(
    bot_id=bot.id,
    model_data=scaler_bytes,
    filename="scaler.pkl",
    model_type="WEIGHTS",
    framework="sklearn"
)
```

### 2. User Subscribes and Configures

```python
# User creates subscription
subscription_data = {
    "bot_id": bot.id,
    "exchange_type": "BINANCE",
    "trading_pair": "BTC/USDT",
    "timeframe": "1h",
    "strategy_config": {
        "rsi_period": 14,
        "rsi_oversold": 30,
        "rsi_overbought": 70
    },
    "execution_config": {
        "buy_order_type": "PERCENTAGE",
        "buy_order_value": 10.0,
        "sell_order_type": "ALL"
    },
    "risk_config": {
        "stop_loss_percent": 5.0,
        "take_profit_percent": 10.0,
        "max_position_size": 20.0
    }
}
```

### 3. Automated Execution

```python
# Celery task runs bot
@celery_app.task
def run_bot_logic(subscription_id: int):
    # 1. Load bot from S3 with all dependencies
    bot = bot_manager.load_bot_from_s3(
        bot_id=subscription.bot.id,
        user_config=enhanced_config,
        user_api_keys=user_api_keys
    )
    
    # 2. Execute complete cycle
    signal = bot.execute_full_cycle(
        timeframe=subscription.timeframe,
        subscription_config=subscription_config
    )
    
    # 3. Execute real trades
    if signal.action == "BUY":
        execute_buy_order_with_exchange(db, subscription, signal.value, signal, exchange_client)
    elif signal.action == "SELL":
        execute_sell_order_with_exchange(db, subscription, signal.value, signal, exchange_client)
```

## API Endpoints

### Bot Management
- `POST /api/bots/` - Create new bot
- `POST /api/bots/{bot_id}/upload-code` - Upload bot code to S3
- `POST /api/bots/{bot_id}/upload-model` - Upload ML model to S3
- `GET /api/bots/{bot_id}/versions` - List bot versions
- `GET /api/bots/{bot_id}/download` - Download bot package

### Exchange Management
- `GET /api/exchanges/supported` - List supported exchanges
- `POST /api/exchanges/validate-credentials` - Validate API keys
- `GET /api/exchanges/account-info/{exchange}` - Get account information
- `GET /api/exchanges/balance/{exchange}` - Get account balance

### Subscription Management
- `POST /api/subscriptions/` - Create subscription
- `GET /api/subscriptions/{id}/performance` - Get performance metrics
- `POST /api/subscriptions/{id}/execute` - Force execution
- `GET /api/subscriptions/{id}/trades` - Get trade history

## Configuration

### Environment Variables

```bash
# AWS S3 Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=trading-bot-storage

# Multi-Exchange Configuration
SUPPORTED_EXCHANGES=BINANCE,COINBASE,KRAKEN
DEFAULT_EXCHANGE=BINANCE
EXCHANGE_TESTNET_MODE=true

# Bot Execution
BOT_EXECUTION_TIMEOUT=300
BOT_MAX_MEMORY_MB=512
BOT_MAX_CPU_PERCENT=50
```

### Database Models

Enhanced models support:
- **Bot types**: TECHNICAL, ML, DL, LLM
- **Exchange types**: BINANCE, COINBASE, KRAKEN
- **File storage**: S3 keys and metadata
- **Performance tracking**: Comprehensive metrics

## Security Features

### Bot Code Validation
- AST parsing prevents dangerous code
- Sandboxed execution environment
- Resource limits (CPU, memory, time)
- Allowed imports whitelist

### API Security
- JWT authentication
- Rate limiting
- Input validation
- SQL injection prevention

### Data Protection
- Encrypted API keys
- Secure S3 storage
- Audit logging
- Access controls

## Performance Monitoring

### Bot Performance
- Trade win/loss rates
- P&L tracking
- Risk metrics
- Execution statistics

### System Performance
- API response times
- Database query performance
- S3 operation metrics
- Exchange API latency

## Troubleshooting

### Common Issues

1. **Bot Loading Failed**
   - Check S3 permissions
   - Verify bot code syntax
   - Check model dependencies

2. **Exchange Connection Failed**
   - Validate API credentials
   - Check network connectivity
   - Verify exchange permissions

3. **Trade Execution Failed**
   - Check account balance
   - Verify trading permissions
   - Review risk parameters

### Debugging Tools
- Comprehensive logging
- Performance profiling
- Error tracking
- Real-time monitoring

## Future Enhancements

### Planned Features
- Advanced ML model serving
- Real-time backtesting
- Social trading features
- Advanced risk management
- Mobile app integration

### Scalability Improvements
- Kubernetes deployment
- Multi-region support
- Advanced caching
- Load balancing
- Auto-scaling

This enhanced system provides a production-ready foundation for a comprehensive trading bot marketplace with advanced features and enterprise-grade scalability. 