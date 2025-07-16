# 🤖 Bot Marketplace - Customer Flow Example

## Ví dụ: Alice thuê "RSI Mean Reversion Bot" để trade BTC/USDT

### 📱 **Bước 1: Đăng ký & Đăng nhập**

#### 1.1. Đăng ký tài khoản mới
```http
POST /auth/register
Content-Type: application/json

{
  "email": "alice.trader@gmail.com",
  "password": "SecurePass123!",
  "role": "USER"
}
```

**Response:**
```json
{
  "id": 10,
  "email": "alice.trader@gmail.com",
  "role": "USER",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z"
}
```

#### 1.2. Đăng nhập
```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=alice.trader@gmail.com&password=SecurePass123!
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 🔍 **Bước 2: Tìm kiếm & Chọn Bot**

#### 2.1. Xem danh sách bots có sẵn
```http
GET /bots?category_id=5&search=RSI&sort_by=average_rating&order=desc
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "bots": [
    {
      "id": 2,
      "name": "RSI Mean Reversion",
      "description": "Contrarian strategy using RSI indicator to identify oversold/overbought conditions. Perfect for range-bound markets.",
      "developer_id": 1,
      "category_id": 5,
      "status": "APPROVED",
      "bot_type": "TECHNICAL",
      "price_per_month": 19.99,
      "is_free": false,
      "version": "1.1.0",
      "total_subscribers": 78,
      "average_rating": 4.5,
      "total_reviews": 23,
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

#### 2.2. Xem chi tiết bot
```http
GET /bots/2
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "id": 2,
  "name": "RSI Mean Reversion",
  "description": "Contrarian strategy using RSI indicator...",
  "developer": {
    "id": 1,
    "developer_name": "John Doe",
    "developer_bio": "Experienced algorithmic trader...",
    "total_bots": 5,
    "average_rating": 4.3
  },
  "category": {
    "id": 5,
    "name": "Mean Reversion"
  },
  "config_schema": {
    "type": "object",
    "properties": {
      "rsi_period": {"type": "integer", "minimum": 7, "maximum": 21, "default": 14},
      "oversold_level": {"type": "number", "minimum": 20, "maximum": 35, "default": 30},
      "overbought_level": {"type": "number", "minimum": 65, "maximum": 80, "default": 70}
    }
  },
  "default_config": {
    "rsi_period": 14,
    "oversold_level": 30,
    "overbought_level": 70
  },
  "performance_stats": {
    "total_profit_percentage": 15.8,
    "win_rate": 68.5,
    "max_drawdown": 8.2,
    "sharpe_ratio": 1.45
  }
}
```

#### 2.3. Đọc reviews từ users khác
```http
GET /bots/2/reviews
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
[
  {
    "id": 5,
    "rating": 5,
    "comment": "Excellent bot! Made 12% profit in 2 months with BTC/USDT. Works great in sideways markets.",
    "user": {
      "id": 8,
      "email": "tr***@gmail.com"
    },
    "created_at": "2025-01-10T00:00:00Z"
  },
  {
    "id": 6,
    "rating": 4,
    "comment": "Good strategy but be careful in trending markets. Best for range-bound conditions.",
    "user": {
      "id": 9,
      "email": "in***@yahoo.com"
    },
    "created_at": "2025-01-08T00:00:00Z"
  }
]
```

---

### 🔧 **Bước 3: Cấu hình Exchange & API Keys**

#### 3.1. Kiểm tra exchanges hỗ trợ
```http
GET /exchanges/supported
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
["BINANCE", "COINBASE", "KRAKEN", "BYBIT", "HUOBI"]
```

#### 3.2. Validate API credentials
```http
POST /exchanges/validate-credentials
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "exchange_name": "BINANCE",
  "api_key": "alice_binance_api_key_here",
  "api_secret": "alice_binance_secret_here",
  "testnet": true
}
```

**Response:**
```json
{
  "valid": true,
  "permissions": ["SPOT_TRADING", "READ_ACCOUNT"],
  "account_info": {
    "can_trade": true,
    "can_withdraw": false,
    "balances": [
      {"asset": "USDT", "free": "1000.00", "locked": "0.00"},
      {"asset": "BTC", "free": "0.05", "locked": "0.00"}
    ]
  }
}
```

---

### 📋 **Bước 4: Tạo Subscription (Thuê Bot)**

#### 4.1. Tạo subscription với cấu hình tùy chỉnh
```http
POST /subscriptions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "instance_name": "Alice's RSI Bot for BTC",
  "bot_id": 2,
  "exchange_type": "BINANCE",
  "trading_pair": "BTCUSDT",
  "timeframe": "1h",
  "strategy_config": {
    "rsi_period": 14,
    "oversold_level": 25,
    "overbought_level": 75
  },
  "execution_config": {
    "buy_order_type": "PERCENTAGE",
    "buy_order_value": 10.0,
    "sell_order_type": "ALL",
    "sell_order_value": 100.0
  },
  "risk_config": {
    "stop_loss_percent": 5.0,
    "take_profit_percent": 15.0,
    "max_position_size": 500.0
  }
}
```

**Response:**
```json
{
  "id": 15,
  "instance_name": "Alice's RSI Bot for BTC",
  "bot_id": 2,
  "bot_name": "RSI Mean Reversion",
  "status": "ACTIVE",
  "exchange_type": "BINANCE",
  "trading_pair": "BTCUSDT",
  "timeframe": "1h",
  "created_at": "2025-01-15T10:30:00Z",
  "next_execution": "2025-01-15T11:00:00Z",
  "message": "Subscription created successfully. Bot will start trading on next hourly candle."
}
```

---

### 🚀 **Bước 5: Bot Bắt Đầu Trading**

#### 5.1. Kiểm tra trạng thái subscription
```http
GET /subscriptions/15
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "id": 15,
  "instance_name": "Alice's RSI Bot for BTC",
  "status": "ACTIVE",
  "bot": {
    "id": 2,
    "name": "RSI Mean Reversion",
    "version": "1.1.0"
  },
  "trading_pair": "BTCUSDT",
  "last_execution": "2025-01-15T11:00:00Z",
  "next_execution": "2025-01-15T12:00:00Z",
  "total_trades": 0,
  "current_position": 0,
  "total_profit_usd": 0.00,
  "profit_percentage": 0.00
}
```

#### 5.2. Bot thực hiện trade đầu tiên (sau 1 giờ)
```http
GET /subscriptions/15
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (sau khi bot đã trade):**
```json
{
  "id": 15,
  "instance_name": "Alice's RSI Bot for BTC",
  "status": "ACTIVE",
  "last_execution": "2025-01-15T12:00:00Z",
  "next_execution": "2025-01-15T13:00:00Z",
  "total_trades": 1,
  "current_position": 0.002,
  "total_profit_usd": 0.00,
  "profit_percentage": 0.00,
  "last_action": "BUY",
  "last_trade": {
    "action": "BUY",
    "price": 42500.00,
    "quantity": 0.002,
    "total_usd": 85.00,
    "signal_data": {
      "rsi": 28.5,
      "reason": "RSI oversold condition detected"
    }
  }
}
```

---

### 📊 **Bước 6: Theo Dõi Performance**

#### 6.1. Xem lịch sử trades
```http
GET /subscriptions/15/trades?limit=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "trades": [
    {
      "id": 1,
      "side": "BUY",
      "entry_price": 42500.00,
      "quantity": 0.002,
      "total_usd": 85.00,
      "timestamp": "2025-01-15T12:00:00Z",
      "status": "FILLED"
    },
    {
      "id": 2,
      "side": "SELL",
      "entry_price": 43200.00,
      "quantity": 0.002,
      "total_usd": 86.40,
      "profit_usd": 1.40,
      "profit_percentage": 1.65,
      "timestamp": "2025-01-15T15:00:00Z",
      "status": "FILLED"
    }
  ],
  "total": 2,
  "total_profit_usd": 1.40,
  "win_rate": 100.0
}
```

#### 6.2. Xem performance chi tiết
```http
GET /subscriptions/15/performance
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
{
  "subscription_id": 15,
  "period_days": 7,
  "total_trades": 5,
  "winning_trades": 3,
  "losing_trades": 2,
  "win_rate": 60.0,
  "total_profit_usd": 15.80,
  "profit_percentage": 3.16,
  "max_profit_usd": 8.50,
  "max_loss_usd": -3.20,
  "average_profit_per_trade": 3.16,
  "sharpe_ratio": 1.25,
  "max_drawdown": 2.8,
  "daily_performance": [
    {"date": "2025-01-15", "profit_usd": 1.40, "trades": 1},
    {"date": "2025-01-16", "profit_usd": 8.50, "trades": 2},
    {"date": "2025-01-17", "profit_usd": -3.20, "trades": 1},
    {"date": "2025-01-18", "profit_usd": 5.30, "trades": 1},
    {"date": "2025-01-19", "profit_usd": 3.80, "trades": 0}
  ]
}
```

#### 6.3. Xem logs hoạt động
```http
GET /subscriptions/15/logs?limit=5
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
```json
[
  {
    "id": 25,
    "action": "SELL",
    "price": 43200.00,
    "quantity": 0.002,
    "balance": 1001.40,
    "signal_data": {
      "rsi": 76.2,
      "reason": "RSI overbought condition - taking profit"
    },
    "timestamp": "2025-01-15T15:00:00Z"
  },
  {
    "id": 24,
    "action": "HOLD",
    "price": 42800.00,
    "quantity": 0.002,
    "balance": 1000.00,
    "signal_data": {
      "rsi": 45.5,
      "reason": "RSI in neutral zone - holding position"
    },
    "timestamp": "2025-01-15T14:00:00Z"
  }
]
```

---

### ⚙️ **Bước 7: Quản Lý Subscription**

#### 7.1. Cập nhật cấu hình bot
```http
PUT /subscriptions/15
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "strategy_config": {
    "rsi_period": 14,
    "oversold_level": 20,
    "overbought_level": 80
  },
  "risk_config": {
    "stop_loss_percent": 3.0,
    "take_profit_percent": 20.0
  }
}
```

#### 7.2. Tạm dừng bot (nếu thị trường không phù hợp)
```http
POST /subscriptions/15/pause
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "reason": "Market trending strongly - pausing mean reversion strategy"
}
```

#### 7.3. Tiếp tục bot
```http
POST /subscriptions/15/resume
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 7.4. Hủy subscription (nếu không hài lòng)
```http
POST /subscriptions/15/cancel
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "reason": "Switching to trend-following strategy",
  "immediate": false
}
```

---

### 📝 **Bước 8: Đánh Giá Bot**

#### 8.1. Viết review cho bot (sau 1 tháng sử dụng)
```http
POST /bots/2/reviews
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "rating": 4,
  "comment": "Great bot for sideways markets! Made 8% profit in BTC/USDT over 1 month. Only downside is it struggles in strong trends. Would recommend for range-bound conditions."
}
```

---

## 💡 **Key Insights từ Flow này:**

### ✅ **Ưu điểm của RSI Bot:**
- Hoạt động tốt trong thị trường sideway
- Win rate 60% khá ổn định
- Risk management tốt với stop-loss
- Giao diện quản lý dễ sử dụng

### ⚠️ **Lưu ý:**
- Cần pause trong thị trường trending mạnh
- Nên test với số tiền nhỏ trước
- Theo dõi performance thường xuyên
- Điều chỉnh parameters theo market conditions

### 🎯 **Kết quả sau 1 tháng:**
- Total trades: 45
- Win rate: 62%
- Profit: +8.5%
- Max drawdown: -4.2%
- Alice quyết định tiếp tục thuê bot và recommend cho bạn bè!

---

## 🔄 **Next Steps cho Alice:**

1. **Thuê thêm bot khác** cho trending markets (MACD Trend Follower)
2. **Tăng vốn** từ $1000 lên $5000 cho RSI Bot
3. **Test bot mới** với timeframe 4h thay vì 1h
4. **Join community** để học thêm strategies từ traders khác

---

*Đây là một flow hoàn chỉnh từ việc tìm hiểu đến việc sử dụng thành công một trading bot trên marketplace!* 