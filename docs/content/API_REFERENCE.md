# 📚 API Reference Documentation

## Authentication

All API requests require authentication via API key in the header:

```http
X-API-Key: your_api_key_here
```

### API Key Types
- **Marketplace API Key**: `marketplace_dev_api_key_12345` (for bot management)
- **Bot API Key**: Generated per user-bot registration (for execution)

## Base URLs

- **Development**: `http://localhost:8000`
- **Staging**: `https://api-staging.bot-marketplace.com`
- **Production**: `https://api.bot-marketplace.com`

---

## 🏪 Marketplace Management APIs

### Register Bot for User

Creates a new bot registration for a specific user on the marketplace.

**Endpoint**: `POST /bots/register`

**Authentication**: Marketplace API Key required

**Request Body**:
```json
{
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "bot_id": 1,
  "marketplace_name": "Advanced Futures Trading Bot",
  "marketplace_description": "AI-powered bot with LLM integration",
  "price_on_marketplace": "50.00"
}
```

**Response**: `201 Created`
```json
{
  "registration_id": 3,
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "bot_id": 1,
  "api_key": "bot_e8nqg30ry1g42tyix9n0",
  "status": "approved",
  "message": "Bot registered successfully for marketplace with auto-generated API key",
  "registration_details": {
    "marketplace_name": "Advanced Futures Trading Bot",
    "marketplace_description": "AI-powered bot with LLM integration",
    "price_on_marketplace": "50.00",
    "commission_rate": 0.1,
    "registered_at": "2025-08-03T11:30:00",
    "status": "APPROVED"
  }
}
```

**Error Responses**:
```json
// 401 Unauthorized
{
  "detail": "Invalid marketplace API key"
}

// 400 Bad Request
{
  "detail": "User principal ID already has this bot registered"
}

// 422 Validation Error
{
  "detail": [
    {
      "loc": ["body", "user_principal_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

### Get Marketplace Bots

Retrieves list of all approved bots available on marketplace.

**Endpoint**: `GET /bots/marketplace`

**Query Parameters**:
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum records to return (default: 50)

**Response**: `200 OK`
```json
[
  {
    "id": 1,
    "user_principal_id": "marketplace-system",
    "bot_id": 1,
    "api_key": "bot_marketplace_xyz123",
    "status": "approved",
    "marketplace_name": "Advanced Futures Trading Bot",
    "marketplace_description": "AI-powered bot with LLM integration",
    "price_on_marketplace": "50.00",
    "commission_rate": 0.1,
    "registered_at": "2025-08-03T11:30:00",
    "is_featured": true,
    "is_active": true
  }
]
```

---

### Get User Bot Registrations

Retrieves all bot registrations for a specific user.

**Endpoint**: `GET /bots/registrations/{user_principal_id}`

**Path Parameters**:
- `user_principal_id` (string): User's principal ID

**Query Parameters**:
- `bot_id` (int, optional): Filter by specific bot ID

**Response**: `200 OK`
```json
[
  {
    "id": 3,
    "user_id": 4,
    "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
    "instance_name": "My Trading Bot",
    "bot_id": 1,
    "exchange_type": "BINANCE",
    "trading_pair": "BTCUSDT",
    "timeframe": "1h",
    "strategy_config": {},
    "execution_config": {
      "buy_order_type": "USDT_AMOUNT",
      "buy_order_value": 100,
      "sell_order_type": "PERCENTAGE",
      "sell_order_value": 100
    },
    "risk_config": {
      "stop_loss_percent": 2.0,
      "take_profit_percent": 4.0
    },
    "is_testnet": true,
    "status": "ACTIVE",
    "started_at": "2025-08-03T11:00:00",
    "last_run_at": "2025-08-03T11:30:00",
    "total_trades": 5,
    "winning_trades": 3,
    "total_pnl": "125.50"
  }
]
```

---

### Update Bot Registration

Updates an existing bot registration configuration.

**Endpoint**: `PUT /bots/update-registration/{subscription_id}`

**Path Parameters**:
- `subscription_id` (int): Registration ID to update

**Request Body**:
```json
{
  "timeframes": ["1h", "4h"],
  "trade_evaluation_period": 30,
  "starttime": "2025-08-03T12:00:00Z",
  "endtime": "2025-12-31T23:59:59Z",
  "exchange_name": "BINANCE",
  "network_type": "mainnet",
  "trade_mode": "Futures"
}
```

**Response**: `200 OK`
```json
{
  "subscription_id": 3,
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "status": "updated",
  "message": "Bot registration updated successfully",
  "updated_fields": [
    "timeframes",
    "trade_evaluation_period",
    "network_type"
  ]
}
```

---

### Validate Bot API Key

Validates a bot API key and returns registration information.

**Endpoint**: `GET /bots/validate-bot-key/{api_key}`

**Path Parameters**:
- `api_key` (string): Bot API key to validate

**Response**: `200 OK`
```json
{
  "id": 3,
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "bot_id": 1,
  "api_key": "bot_e8nqg30ry1g42tyix9n0",
  "status": "approved",
  "marketplace_name": "User Trading Bot Instance",
  "is_active": true,
  "registered_at": "2025-08-03T11:30:00"
}
```

---

## 🤖 Bot Execution APIs

### Execute Trading Bot

Triggers immediate execution of a trading bot for a user.

**Endpoint**: `POST /api/futures-bot/execute`

**Request Body**:
```json
{
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "config": {
    "trading_pair": "BTCUSDT",
    "leverage": 10,
    "timeframes": ["1h", "4h"],
    "use_llm_analysis": true,
    "auto_confirm": true,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04,
    "position_size_pct": 0.05
  }
}
```

**Response**: `200 OK`
```json
{
  "task_id": "celery-task-uuid-123",
  "status": "started",
  "message": "Trading bot execution started",
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "estimated_completion": "2025-08-03T12:05:00Z",
  "config": {
    "trading_pair": "BTCUSDT",
    "leverage": 10,
    "auto_confirm": true
  }
}
```

---

### Schedule Periodic Trading

Sets up recurring bot execution on a schedule.

**Endpoint**: `POST /api/futures-bot/schedule`

**Request Body**:
```json
{
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "schedule_minutes": 60,
  "config": {
    "trading_pair": "BTCUSDT",
    "leverage": 10,
    "auto_confirm": true
  }
}
```

**Response**: `200 OK`
```json
{
  "schedule_id": "periodic-task-456",
  "status": "scheduled",
  "message": "Periodic trading scheduled successfully",
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "schedule_minutes": 60,
  "next_execution": "2025-08-03T13:00:00Z",
  "total_executions": 0
}
```

---

### Get Task Status

Checks the status of a specific trading task.

**Endpoint**: `GET /api/futures-bot/task-status/{task_id}`

**Path Parameters**:
- `task_id` (string): Celery task ID

**Response**: `200 OK`
```json
{
  "task_id": "celery-task-uuid-123",
  "status": "completed",
  "progress": 100,
  "result": {
    "status": "success",
    "action": "BUY",
    "trading_pair": "BTCUSDT",
    "quantity": "0.01",
    "entry_price": "113598.9",
    "pnl": "+$25.50",
    "execution_time": "2025-08-03T11:45:00Z",
    "stop_loss_price": "111226.32",
    "take_profit_price": "118242.86"
  },
  "started_at": "2025-08-03T11:40:00Z",
  "completed_at": "2025-08-03T11:45:00Z",
  "runtime_seconds": 300
}
```

**Task Status Values**:
- `pending`: Task queued but not started
- `started`: Task is currently running
- `completed`: Task finished successfully
- `failed`: Task encountered an error
- `cancelled`: Task was cancelled

---

### Get Bot Execution Status

Gets overall execution status for a user's bot.

**Endpoint**: `GET /api/futures-bot/status`

**Query Parameters**:
- `user_principal_id` (string): User's principal ID

**Response**: `200 OK`
```json
{
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "active_tasks": 2,
  "completed_tasks": 15,
  "failed_tasks": 1,
  "total_trades": 12,
  "winning_trades": 8,
  "total_pnl": "+$342.75",
  "win_rate": 66.67,
  "last_execution": "2025-08-03T11:45:00Z",
  "next_scheduled": "2025-08-03T13:00:00Z",
  "bot_status": "active"
}
```

---

## 🔐 Exchange Credentials APIs

### Store Exchange Credentials by Principal ID

Stores encrypted exchange API credentials for a user identified by principal ID.

**Endpoint**: `POST /exchange-credentials/store-by-principal`

**Authentication**: Marketplace API Key required

**Request Body**:
```json
{
  "principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "exchange": "BINANCE",
  "api_key": "user_binance_api_key",
  "api_secret": "user_binance_secret_key",
  "api_passphrase": null,
  "is_testnet": true
}
```

**Response**: `201 Created`
```json
{
  "status": "success",
  "message": "Exchange credentials stored successfully",
  "credential_id": 123,
  "principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "exchange": "BINANCE",
  "is_testnet": true,
  "created_at": "2025-08-03T11:30:00Z"
}
```

---

### Get User Trading Status

Retrieves trading status and performance for a user.

**Endpoint**: `GET /exchange-credentials/user-status/{principal_id}`

**Path Parameters**:
- `principal_id` (string): User's principal ID

**Response**: `200 OK`
```json
{
  "principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "exchanges_configured": ["BINANCE"],
  "account_status": {
    "BINANCE": {
      "is_connected": true,
      "is_testnet": true,
      "balance": "13018.54 USDT",
      "open_positions": 1,
      "last_verified": "2025-08-03T11:45:00Z"
    }
  },
  "trading_performance": {
    "total_trades": 12,
    "winning_trades": 8,
    "win_rate": 66.67,
    "total_pnl": "+$342.75",
    "best_trade": "+$85.30",
    "worst_trade": "-$23.10",
    "average_trade_duration": "2h 15m"
  },
  "risk_metrics": {
    "max_drawdown": "5.2%",
    "sharpe_ratio": 1.85,
    "profit_factor": 2.34,
    "recovery_factor": 4.12
  }
}
```

---

## 📊 Analytics & Reporting APIs

### Get Trading Performance

Retrieves detailed performance analytics for a user's trading.

**Endpoint**: `GET /analytics/performance/{principal_id}`

**Query Parameters**:
- `days` (int, optional): Number of days to analyze (default: 30)
- `bot_id` (int, optional): Filter by specific bot

**Response**: `200 OK`
```json
{
  "principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "analysis_period": {
    "start_date": "2025-07-04T00:00:00Z",
    "end_date": "2025-08-03T23:59:59Z",
    "days": 30
  },
  "performance_summary": {
    "total_trades": 45,
    "winning_trades": 32,
    "losing_trades": 13,
    "win_rate": 71.11,
    "gross_profit": "1284.50",
    "gross_loss": "-345.20",
    "net_profit": "939.30",
    "profit_factor": 3.72,
    "max_drawdown": "156.80",
    "max_drawdown_percent": 8.3
  },
  "daily_performance": [
    {
      "date": "2025-08-03",
      "trades": 3,
      "pnl": "+$45.20",
      "win_rate": 66.67
    }
  ],
  "monthly_performance": [
    {
      "month": "2025-08",
      "trades": 12,
      "pnl": "+$342.75",
      "win_rate": 75.0
    }
  ]
}
```

---

### Get Trade History

Retrieves detailed trade history for a user.

**Endpoint**: `GET /analytics/trades/{principal_id}`

**Query Parameters**:
- `limit` (int, optional): Maximum trades to return (default: 100)
- `offset` (int, optional): Number of trades to skip (default: 0)
- `start_date` (string, optional): Start date filter (ISO format)
- `end_date` (string, optional): End date filter (ISO format)

**Response**: `200 OK`
```json
{
  "total_trades": 156,
  "page": 1,
  "per_page": 100,
  "trades": [
    {
      "id": 789,
      "trading_pair": "BTCUSDT",
      "side": "BUY",
      "quantity": "0.01",
      "entry_price": "113598.90",
      "exit_price": "114235.60",
      "entry_time": "2025-08-03T11:40:00Z",
      "exit_time": "2025-08-03T13:15:00Z",
      "pnl": "+$6.37",
      "pnl_percentage": 0.56,
      "stop_loss_price": "111226.32",
      "take_profit_price": "118242.86",
      "exit_reason": "take_profit",
      "bot_id": 1,
      "commission": "$0.23",
      "duration_minutes": 95
    }
  ]
}
```

---

## 🚨 Error Responses

### Standard Error Format

All API errors follow this consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "field": "user_principal_id",
      "reason": "Invalid format"
    },
    "timestamp": "2025-08-03T11:30:00Z",
    "request_id": "req_123456789"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTHENTICATION_FAILED` | 401 | Invalid or missing API key |
| `AUTHORIZATION_FAILED` | 403 | Insufficient permissions |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server internal error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## 🔄 Webhooks

### Trading Event Webhook

Receive real-time notifications for trading events.

**Webhook URL**: Configure in your marketplace settings

**Event Types**:
- `trade.executed`: New trade executed
- `trade.closed`: Trade position closed
- `bot.started`: Bot execution started
- `bot.stopped`: Bot execution stopped
- `error.occurred`: Trading error occurred

**Payload Example**:
```json
{
  "event_type": "trade.executed",
  "timestamp": "2025-08-03T11:45:00Z",
  "event_id": "evt_123456789",
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "data": {
    "trade_id": 789,
    "trading_pair": "BTCUSDT",
    "side": "BUY",
    "quantity": "0.01",
    "price": "113598.90",
    "timestamp": "2025-08-03T11:45:00Z"
  }
}
```

---

## 📈 Rate Limits

### Default Limits

| Endpoint Category | Requests per Minute | Burst Limit |
|------------------|-------------------|-------------|
| Marketplace APIs | 100 | 150 |
| Bot Execution | 60 | 100 |
| Analytics | 200 | 300 |
| Webhooks | 1000 | 1500 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1672531200
```

---

*For additional support, contact the API team or refer to the integration guides.*