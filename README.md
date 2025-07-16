# Trading Bot Marketplace

A complete backend marketplace for trading bot rental where developers can submit bots with custom algorithms and users can subscribe to them.

## Features

### Core Features
- **User Management**: Registration, authentication, and profile management
- **Bot Development**: Upload, validate, and manage custom trading bots
- **Bot Marketplace**: Browse, review, and subscribe to approved bots
- **Real-time Trading**: Execute trades based on bot signals
- **Performance Tracking**: Monitor bot and subscription performance
- **Admin Panel**: Comprehensive admin controls for marketplace management

### Advanced Features
- **Bot Validation**: Automatic security and structure validation
- **File Management**: Secure bot code upload and version control
- **Review System**: User reviews and ratings for bots
- **Performance Analytics**: Detailed performance metrics and reports
- **Real-time Monitoring**: Live trading execution and logging
- **Payment Integration**: Ready for payment system integration

## Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **Database**: MySQL with SQLAlchemy ORM
- **Cache/Queue**: Redis with Celery for background tasks
- **Authentication**: JWT tokens with role-based access
- **API Documentation**: OpenAPI/Swagger
- **Containerization**: Docker and docker-compose

## Project Structure

```
bot_marketplace/
├── api/
│   ├── endpoints/
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── bots.py          # Bot management endpoints
│   │   ├── subscriptions.py # Subscription management
│   │   └── admin.py         # Admin endpoints
│   └── __init__.py
├── bots/
│   ├── bot_sdk.py          # Bot SDK framework
│   ├── golden_cross_bot.py # Example bot implementation
│   └── __init__.py
├── bot_manager.py          # Bot lifecycle management
├── crud.py                 # Database operations
├── database.py             # Database configuration
├── models.py               # SQLAlchemy models
├── schemas.py              # Pydantic schemas
├── security.py             # Authentication & authorization
├── tasks.py                # Celery background tasks
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker configuration
├── Dockerfile              # Container definition
└── config.env.example      # Environment configuration template
```

## Setup Instructions

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd bot_marketplace

# Copy environment configuration
cp config.env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Using Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 3. Manual Setup

#### Install Dependencies
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Database Setup
```bash
# Start MySQL and Redis
# Update .env with your database credentials

# Run database migrations
python -c "from database import engine; import models; models.Base.metadata.create_all(bind=engine)"
```

#### Start Services
```bash
# Start API server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start Celery worker (new terminal)
celery -A tasks.celery_app worker --loglevel=info

# Start Celery beat (new terminal)
celery -A tasks.celery_app beat --loglevel=info
```

## API Documentation

### Authentication Endpoints

#### Register User
```http
POST /api/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "role": "USER",
  "developer_name": "John Doe"
}
```

#### Login
```http
POST /api/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=password123
```

### Bot Management Endpoints

#### Get Public Bots
```http
GET /api/bots/?skip=0&limit=10&category_id=1&search=golden
```

#### Submit New Bot (Developer)
```http
POST /api/bots/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Trading Bot",
  "description": "Advanced trading algorithm",
  "category_id": 1,
  "default_config": {
    "short_period": 50,
    "long_period": 200
  }
}
```

#### Upload Bot Code
```http
POST /api/bots/{bot_id}/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <python_file>
```

### Subscription Endpoints

#### Subscribe to Bot
```http
POST /api/subscriptions/
Authorization: Bearer <token>
Content-Type: application/json

{
  "bot_id": 1,
  "instance_name": "My BTC Bot",
  "trading_pair": "BTC/USDT",
  "timeframe": "1h",
  "strategy_config": {
    "short_period": 30,
    "long_period": 100
  },
  "execution_config": {
    "buy_order_type": "PERCENTAGE",
    "buy_order_value": 25.0,
    "sell_order_type": "ALL",
    "sell_order_value": 100.0
  },
  "risk_config": {
    "stop_loss_percent": 5.0,
    "take_profit_percent": 15.0
  }
}
```

#### Get Subscription Performance
```http
GET /api/subscriptions/{subscription_id}/performance?days=30
Authorization: Bearer <token>
```

### Admin Endpoints

#### Get Dashboard Statistics
```http
GET /api/admin/dashboard
Authorization: Bearer <admin_token>
```

#### Approve Bot
```http
PUT /api/admin/bots/{bot_id}/approve
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "bot_id": 1,
  "status": "APPROVED",
  "approval_notes": "Bot approved after review"
}
```

## Bot Development Guide

### Creating a Trading Bot

1. **Inherit from CustomBot**:
```python
from bots.bot_sdk import CustomBot, Action
import pandas as pd
import pandas_ta as ta

class MyTradingBot(CustomBot):
    bot_name = "My Trading Bot"
    bot_description = "Description of your trading strategy"
    
    def __init__(self, bot_config, user_api_keys):
        super().__init__(bot_config, user_api_keys)
        self.param1 = bot_config.get('param1', 50)
        self.param2 = bot_config.get('param2', 200)
    
    def prepare_data(self, candles_df):
        # Prepare technical indicators
        candles_df['sma_short'] = ta.sma(candles_df['close'], length=self.param1)
        candles_df['sma_long'] = ta.sma(candles_df['close'], length=self.param2)
        return candles_df
    
    def predict(self, prepared_df):
        # Generate trading signals
        last_row = prepared_df.iloc[-1]
        prev_row = prepared_df.iloc[-2]
        
        # Golden cross signal
        if (prev_row['sma_short'] <= prev_row['sma_long'] and 
            last_row['sma_short'] > last_row['sma_long']):
            return Action.buy(type="PERCENTAGE", value=100)
        
        # Death cross signal
        elif (prev_row['sma_short'] >= prev_row['sma_long'] and 
              last_row['sma_short'] < last_row['sma_long']):
            return Action.sell(type="PERCENTAGE", value=100)
        
        return Action.hold()
```

2. **Required Methods**:
   - `prepare_data(candles_df)`: Process market data and add indicators
   - `predict(prepared_df)`: Generate trading signals

3. **Configuration Schema**:
```python
config_schema = {
    "type": "object",
    "properties": {
        "param1": {"type": "integer", "minimum": 1, "maximum": 100},
        "param2": {"type": "integer", "minimum": 1, "maximum": 500}
    },
    "required": ["param1", "param2"]
}
```

### Bot Validation

The system automatically validates bots for:
- **Security**: Prevents dangerous imports and functions
- **Structure**: Ensures required methods are implemented
- **Best Practices**: Checks for error handling and documentation

### Testing Your Bot

Use the bot testing endpoint to validate your bot:
```http
POST /api/bots/{bot_id}/test
Authorization: Bearer <token>
Content-Type: application/json

{
  "market_data": [
    {"open": 100, "high": 105, "low": 98, "close": 102, "volume": 1000},
    {"open": 102, "high": 108, "low": 101, "close": 106, "volume": 1200}
  ]
}
```

## Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Database
MYSQL_HOST=localhost
MYSQL_DATABASE=bot_marketplace
MYSQL_USER=bot_user
MYSQL_PASSWORD=your_password

# Security
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Bot Execution
BOT_EXECUTION_TIMEOUT=300
MAX_CONCURRENT_BOTS=10

# Performance
PERFORMANCE_LOG_RETENTION_DAYS=90
```

### User Roles

- **USER**: Can subscribe to bots and manage subscriptions
- **DEVELOPER**: Can create and manage bots + user permissions
- **ADMIN**: Full system access + developer permissions

## Monitoring and Analytics

### Performance Tracking

- **Bot Performance**: Success rates, P&L, drawdown
- **Subscription Metrics**: Active/inactive subscriptions, user engagement
- **System Health**: API response times, error rates

### Logging

- **Application Logs**: Stored in `/logs/bot_marketplace.log`
- **Performance Logs**: Database table for detailed metrics
- **Error Tracking**: Celery task failures and retries

## Security Features

### Bot Code Validation
- Prevents dangerous imports (`os`, `sys`, `subprocess`)
- Blocks access to system attributes
- Validates code structure and required methods

### API Security
- JWT token authentication
- Role-based access control
- Rate limiting
- Input validation with Pydantic

### Data Protection
- Secure file uploads
- SQL injection prevention
- XSS protection

## Deployment

### Production Setup

1. **Environment Configuration**:
```bash
PRODUCTION_MODE=true
DEBUG=false
SECRET_KEY=<strong_secret_key>
```

2. **Database Optimization**:
```bash
# Enable connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
```

3. **Security Hardening**:
```bash
# Enable HTTPS
ENABLE_HTTPS=true
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### Scaling

- **Horizontal Scaling**: Multiple API instances behind load balancer
- **Database Scaling**: Read replicas for better performance
- **Task Distribution**: Multiple Celery workers for bot execution

## API Reference

Complete API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Email: support@botmarketplace.com
- Documentation: [Link to docs]
- Issues: [GitHub Issues]

---

## Quick Start Example

```bash
# 1. Start services
docker-compose up -d

# 2. Create admin user
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "admin123",
    "role": "ADMIN"
  }'

# 3. Login and get token
curl -X POST "http://localhost:8000/api/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=admin123"

# 4. Create bot category
curl -X POST "http://localhost:8000/api/bots/categories/" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Technical Analysis", "description": "Bots using technical indicators"}'

# 5. Check system status
curl "http://localhost:8000/api/admin/dashboard" \
  -H "Authorization: Bearer <token>"
```

The marketplace is now ready for bot development and trading! 