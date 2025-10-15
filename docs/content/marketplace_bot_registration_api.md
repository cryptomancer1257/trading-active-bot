# Marketplace Bot Registration API Documentation

## Tổng quan

Hệ thống Trade Bot Marketplace cung cấp các API cho phép marketplace bên ngoài đăng ký và quản lý bot cho users thông qua API key authentication.

## Authentication

Tất cả các API endpoint yêu cầu authentication thông qua API key trong header:

```
X-API-Key: your_api_key_here
```

API key phải được cấu hình trong database cho user tương ứng.

## Endpoints

### 1. POST /api/bots/register

Đăng ký bot cho user thông qua marketplace.

**Headers:**
```
Content-Type: application/json
X-API-Key: your_api_key_here
```

**Request Body:**
```json
{
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "bot_id": 1,
  "symbol": "BTC/USDT",
  "timeframes": ["1h", "4h", "1d"],
  "trade_evaluation_period": 60,
  "starttime": "2024-01-01T00:00:00Z",
  "endtime": "2024-12-31T23:59:59Z",
  "exchange_name": "BINANCE",
  "network_type": "testnet",
  "trade_mode": "Spot"
}
```

**Response:**
```json
{
  "subscription_id": 123,
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "bot_id": 1,
  "status": "success",
  "message": "Bot registered successfully for marketplace user",
  "registration_details": {
    "instance_name": "Trading Bot - rdmx6-ja",
    "symbol": "BTC/USDT",
    "timeframes": ["1h", "4h", "1d"],
    "trade_evaluation_period": 60,
    "exchange_name": "BINANCE",
    "network_type": "testnet",
    "trade_mode": "Spot",
    "start_time": "2024-01-01T00:00:00",
    "end_time": "2024-12-31T23:59:59",
    "created_at": "2024-01-15T10:30:00"
  }
}
```

### 2. PUT /api/bots/update-registration/{subscription_id}

Cập nhật thông tin đăng ký bot.

**Headers:**
```
Content-Type: application/json
X-API-Key: your_api_key_here
```

**Request Body:**
```json
{
  "timeframes": ["2h", "6h"],
  "trade_evaluation_period": 120,
  "starttime": "2024-02-01T00:00:00Z",
  "endtime": "2024-11-30T23:59:59Z",
  "exchange_name": "COINBASE",
  "network_type": "mainnet",
  "trade_mode": "Futures"
}
```

**Response:**
```json
{
  "subscription_id": 123,
  "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
  "status": "success",
  "message": "Bot registration updated successfully. Updated fields: timeframes, trade_evaluation_period, exchange_name",
  "updated_fields": ["timeframes", "trade_evaluation_period", "exchange_name"]
}
```

### 3. GET /api/bots/registrations/{user_principal_id}

Lấy danh sách bot đã đăng ký cho user.

**Headers:**
```
X-API-Key: your_api_key_here
```

**Query Parameters:**
- `bot_id` (optional): Filter theo bot ID cụ thể

**Response:**
```json
[
  {
    "id": 123,
    "instance_name": "Trading Bot - rdmx6-ja",
    "user_id": 1,
    "bot_id": 1,
    "status": "ACTIVE",
    "exchange_type": "BINANCE",
    "trading_pair": "BTC/USDT",
    "timeframe": "1h",
    "timeframes": ["1h", "4h", "1d"],
    "trade_evaluation_period": 60,
    "network_type": "testnet",
    "trade_mode": "Spot",
    "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
    "started_at": "2024-01-01T00:00:00",
    "expires_at": "2024-12-31T23:59:59",
    "is_testnet": true,
    "is_trial": false
  }
]
```

## Field Descriptions

### Request Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_principal_id` | string | Yes | Principal ID của ICP user |
| `bot_id` | integer | Yes | ID của bot đã được approve trong hệ thống |
| `symbol` | string | Yes | Trading pair (ví dụ: BTC/USDT, ETH/USDT) |
| `timeframes` | array[string] | Yes | Danh sách timeframes ['1h', '2h', '4h'] |
| `trade_evaluation_period` | integer | Yes | Thời gian bot quan sát và phân tích (phút) |
| `starttime` | datetime | Yes | Thời gian bắt đầu cho thuê |
| `endtime` | datetime | Yes | Thời gian kết thúc cho thuê |
| `exchange_name` | enum | Yes | Sàn giao dịch (BINANCE, COINBASE, KRAKEN, BYBIT, HUOBI) |
| `network_type` | enum | Yes | testnet hoặc mainnet |
| `trade_mode` | enum | Yes | Spot, Margin, hoặc Futures |

### Valid Values

**timeframes:** `1m`, `5m`, `15m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `1w`

**exchange_name:** `BINANCE`, `COINBASE`, `KRAKEN`, `BYBIT`, `HUOBI`

**network_type:** `testnet`, `mainnet`

**trade_mode:** `Spot`, `Margin`, `Futures`

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Bot with ID 999 not found or not approved"
}
```

### 401 Unauthorized
```json
{
  "detail": "API key is required"
}
```

### 404 Not Found
```json
{
  "detail": "Subscription 999 not found or not owned by user"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to register bot: Database connection error"
}
```

## Database Schema Changes

Để hỗ trợ các API này, các trường sau đã được thêm vào bảng `subscriptions`:

- `user_principal_id`: VARCHAR(255) - ICP Principal ID
- `timeframes`: JSON - Danh sách timeframes
- `trade_evaluation_period`: INT - Thời gian phân tích (phút)
- `network_type`: ENUM('testnet', 'mainnet') - Loại mạng
- `trade_mode`: ENUM('Spot', 'Margin', 'Futures') - Chế độ giao dịch

## Migration

Chạy script migration để cập nhật database:

```sql
-- Xem file scripts/migrate_bot_registration.sql
```

## Example Usage

### Đăng ký bot mới
```bash
curl -X POST "https://api.example.com/api/bots/register" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "user_principal_id": "rdmx6-jaaaa-aaaah-qcaiq-cai",
    "bot_id": 1,
    "symbol": "BTC/USDT",
    "timeframes": ["1h", "4h"],
    "trade_evaluation_period": 60,
    "starttime": "2024-01-01T00:00:00Z",
    "endtime": "2024-12-31T23:59:59Z",
    "exchange_name": "BINANCE",
    "network_type": "testnet",
    "trade_mode": "Spot"
  }'
```

### Cập nhật đăng ký
```bash
curl -X PUT "https://api.example.com/api/bots/update-registration/123" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "timeframes": ["2h", "6h"],
    "network_type": "mainnet"
  }'
```

### Lấy danh sách đăng ký
```bash
curl -X GET "https://api.example.com/api/bots/registrations/rdmx6-jaaaa-aaaah-qcaiq-cai" \
  -H "X-API-Key: your_api_key_here"
```