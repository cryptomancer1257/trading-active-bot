# 🛡️ Enhanced Risk Management System

## Tổng Quan

Hệ thống Risk Management mới hỗ trợ **2 chế độ** quản lý rủi ro:

1. **DEFAULT Mode** (Cấu hình thủ công) - Người dùng thiết lập các quy tắc cố định
2. **AI_PROMPT Mode** (AI động) - Sử dụng LLM để phân tích và quyết định động

## 📋 Cấu Trúc Hệ Thống

### 1. Schema & Models

#### `RiskManagementMode` Enum
```python
class RiskManagementMode(str, Enum):
    DEFAULT = "DEFAULT"      # Quy tắc cố định
    AI_PROMPT = "AI_PROMPT"  # AI động
```

#### `RiskConfig` Schema
Hỗ trợ đầy đủ các tham số cho cả 2 modes:

**DEFAULT Mode Parameters:**
- `stop_loss_percent` - % stop loss
- `take_profit_percent` - % take profit  
- `max_position_size` - Kích thước vị thế tối đa
- `min_risk_reward_ratio` - RR tối thiểu (VD: 2.0 = 2:1)
- `risk_per_trade_percent` - % rủi ro mỗi lệnh
- `max_leverage` - Đòn bẩy tối đa
- `max_portfolio_exposure` - % exposure tối đa
- `daily_loss_limit_percent` - Giới hạn loss hàng ngày
- `trailing_stop` - Cấu hình trailing stop
- `trading_window` - Khung giờ giao dịch
- `cooldown` - Thời gian chờ sau loss

**AI Mode Parameters:**
- `ai_prompt_id` - ID của prompt template
- `ai_prompt_custom` - Custom prompt
- `ai_update_frequency_minutes` - Tần suất cập nhật từ AI
- `ai_allow_override` - Cho phép AI ghi đè defaults
- `ai_min_stop_loss` / `ai_max_stop_loss` - Giới hạn SL cho AI
- `ai_min_take_profit` / `ai_max_take_profit` - Giới hạn TP cho AI

### 2. Database Schema

```sql
-- Thêm vào bảng subscriptions:
risk_management_mode VARCHAR(20) DEFAULT 'DEFAULT'
daily_loss_amount DECIMAL(20, 8) DEFAULT 0
last_loss_reset_date DATE
cooldown_until TIMESTAMP
consecutive_losses INTEGER DEFAULT 0
```

### 3. Risk Management Service

**Class: `RiskManagementService`**

Xử lý logic đánh giá rủi ro cho cả 2 modes.

**Main Methods:**

#### `evaluate_trade()`
```python
def evaluate_trade(
    risk_config: RiskConfig,
    subscription_id: int,
    signal_data: Dict,
    market_data: Dict,
    account_info: Dict
) -> RiskDecision
```

Đánh giá xem có nên thực hiện lệnh không, trả về `RiskDecision` với:
- `approved`: True/False
- `reason`: Lý do quyết định
- `stop_loss_price`: Giá SL đề xuất
- `take_profit_price`: Giá TP đề xuất
- `position_size_pct`: % kích thước vị thế
- `warnings`: Các cảnh báo

#### `record_trade_result()`
```python
def record_trade_result(
    subscription_id: int,
    profit_loss: float,
    was_win: bool
)
```

Ghi nhận kết quả giao dịch để:
- Tracking daily loss
- Đếm consecutive losses
- Kích hoạt cooldown nếu cần

## 🔧 DEFAULT Mode - Quy Tắc Cố Định

### Các Kiểm Tra Tự Động

1. **Trading Window Check**
   - Kiểm tra giờ giao dịch (VD: chỉ trade 9:00-17:00 UTC)
   - Kiểm tra ngày trong tuần (VD: không trade cuối tuần)

2. **Cooldown Check**
   - Sau N lệnh thua liên tiếp → dừng trading X phút
   - VD: 3 lệnh thua → cooldown 30 phút

3. **Daily Loss Limit**
   - Tracking tổng loss trong ngày
   - Dừng trading khi đạt % loss limit
   - Reset vào 00:00 UTC hàng ngày

4. **Position Size Calculation**
   - Dựa trên `risk_per_trade_percent`
   - Tính toán khoảng cách stop loss
   - Áp dụng max position size

5. **Risk/Reward Ratio Check**
   - Đảm bảo RR >= `min_risk_reward_ratio`
   - VD: Nếu min RR = 2.0, TP phải gấp đôi SL

6. **Portfolio Exposure Check**
   - Tính tổng exposure hiện tại
   - Không vượt quá `max_portfolio_exposure`
   - Cảnh báo khi đạt 80% limit

7. **Leverage Limit**
   - Áp dụng `max_leverage`
   - VD: max 10x cho tài khoản nhỏ

8. **Trailing Stop**
   - Kích hoạt khi profit đạt `activation_percent`
   - Theo dõi với khoảng cách `trailing_percent`

### Ví Dụ Cấu Hình DEFAULT

```json
{
  "mode": "DEFAULT",
  "risk_per_trade_percent": 2.0,
  "min_risk_reward_ratio": 2.0,
  "max_leverage": 10,
  "max_portfolio_exposure": 30,
  "daily_loss_limit_percent": 5.0,
  
  "trailing_stop": {
    "enabled": true,
    "activation_percent": 2.0,
    "trailing_percent": 1.0
  },
  
  "trading_window": {
    "enabled": true,
    "start_hour": 9,
    "end_hour": 17,
    "days_of_week": [0, 1, 2, 3, 4]  // Mon-Fri
  },
  
  "cooldown": {
    "enabled": true,
    "cooldown_minutes": 30,
    "trigger_loss_count": 3
  }
}
```

## 🤖 AI_PROMPT Mode - Dynamic Risk Management

### Cách Hoạt Động

1. **Context Building**
   - Thu thập signal data, market data, account info
   - Format thành context cho LLM

2. **AI Analysis**
   - Gửi prompt + context tới LLM
   - LLM phân tích và đề xuất quyết định
   - Format: JSON response

3. **Safety Bounds**
   - Áp dụng giới hạn `ai_min_*` / `ai_max_*`
   - Ngăn AI đưa ra quyết định quá rủi ro

4. **Fallback**
   - Nếu AI fail → fallback về DEFAULT mode
   - Đảm bảo system luôn hoạt động

### Ví Dụ AI Prompt

```
You are an expert risk management advisor for cryptocurrency futures trading.

Analyze the provided trading signal and market conditions to determine if the trade should be executed.

Consider:
1. Risk/Reward ratio
2. Current market volatility
3. Account exposure
4. Stop loss and take profit levels
5. Position sizing
6. Market trends and conditions

Provide decision in JSON format:
{
  "approved": true/false,
  "reason": "explanation",
  "stop_loss_price": number,
  "take_profit_price": number,
  "position_size_pct": number,
  "warnings": ["warning1", "warning2"]
}
```

### Ví Dụ Cấu Hình AI Mode

```json
{
  "mode": "AI_PROMPT",
  "ai_prompt_id": 123,
  "ai_update_frequency_minutes": 15,
  "ai_allow_override": true,
  
  "ai_min_stop_loss": 1.0,
  "ai_max_stop_loss": 5.0,
  "ai_min_take_profit": 2.0,
  "ai_max_take_profit": 10.0,
  
  // Fallback defaults nếu AI không phản hồi
  "risk_per_trade_percent": 2.0,
  "max_leverage": 10
}
```

## 📡 API Endpoints

### 1. Get Risk Config
```http
GET /api/v1/risk-management/subscriptions/{subscription_id}/risk-config
```

### 2. Update Risk Config
```http
PUT /api/v1/risk-management/subscriptions/{subscription_id}/risk-config
Content-Type: application/json

{
  "mode": "DEFAULT",
  "risk_per_trade_percent": 2.0,
  ...
}
```

### 3. Test Risk Config
```http
POST /api/v1/risk-management/subscriptions/{subscription_id}/risk-config/test
Content-Type: application/json

{
  "signal": {
    "action": "BUY",
    "entry_price": 50000,
    "stop_loss": 49000,
    "take_profit": 52000
  },
  "market": { "current_price": 50000 },
  "account": { "totalWalletBalance": 10000 }
}
```

### 4. Get Risk Status
```http
GET /api/v1/risk-management/subscriptions/{subscription_id}/risk-status
```

Response:
```json
{
  "risk_mode": "DEFAULT",
  "daily_loss_amount": 150.50,
  "consecutive_losses": 2,
  "cooldown_active": false,
  "trading_allowed": true,
  "restrictions": []
}
```

### 5. Reset Cooldown
```http
POST /api/v1/risk-management/subscriptions/{subscription_id}/risk-config/reset-cooldown
```

### 6. Reset Daily Loss
```http
POST /api/v1/risk-management/subscriptions/{subscription_id}/risk-config/reset-daily-loss
```

### 7. Get Risk Management Prompts
```http
GET /api/v1/risk-management/prompts
```

## 🔄 Integration với Bot Execution

### Trong `run_bot_logic()` task:

```python
from services.risk_management_service import RiskManagementService

# ... get signal from bot ...

# Evaluate với Risk Management
risk_service = RiskManagementService(db)
decision = risk_service.evaluate_trade(
    risk_config=subscription.risk_config,
    subscription_id=subscription.id,
    signal_data={
        'action': signal.action,
        'entry_price': entry_price,
        'stop_loss': stop_loss,
        'take_profit': take_profit
    },
    market_data=market_data,
    account_info=account_info
)

if not decision.approved:
    logger.warning(f"Trade rejected by risk management: {decision.reason}")
    return

# Use risk management parameters
stop_loss = decision.stop_loss_price or stop_loss
take_profit = decision.take_profit_price or take_profit
position_size = decision.position_size_pct or default_size
leverage = decision.max_leverage or default_leverage

# Execute trade with risk-managed parameters
# ...

# After trade closes, record result
risk_service.record_trade_result(
    subscription_id=subscription.id,
    profit_loss=pnl,
    was_win=(pnl > 0)
)
```

## 🎨 Frontend Integration

### Risk Management Tab Component

**Tabs:**
1. **Mode Selection** - Chọn DEFAULT hoặc AI_PROMPT
2. **Basic Risk Rules** - SL, TP, Position Size
3. **Advanced Rules** - RR, Leverage, Exposure
4. **Trailing Stop** - Cấu hình trailing
5. **Trading Window** - Giờ giao dịch
6. **Cooldown** - Thời gian chờ
7. **AI Configuration** (nếu AI mode) - Prompt selection
8. **Risk Status** - Real-time status
9. **Test Configuration** - Test với scenario

## 🚀 Deployment

### 1. Run Migration
```bash
mysql -u root -p trade_bot_marketplace < migrations/versions/016_enhanced_risk_management.sql
```

### 2. Register Router
```python
# In main.py
from api.endpoints import risk_management

app.include_router(
    risk_management.router,
    prefix="/api/v1/risk-management",
    tags=["risk-management"]
)
```

### 3. Test
```bash
# Test API
curl -X GET http://localhost:8000/api/v1/risk-management/subscriptions/1/risk-config \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📊 Benefits

### DEFAULT Mode
✅ Predictable và consistent
✅ Dễ hiểu và debug
✅ Không phụ thuộc LLM
✅ Phù hợp với strategy đơn giản

### AI Mode
✅ Adaptive với market conditions
✅ Có thể học từ historical data
✅ Tối ưu RR ratio động
✅ Phù hợp với advanced traders

## 🔒 Safety Features

1. **Fallback Mechanism** - AI fail → DEFAULT mode
2. **Safety Bounds** - AI không thể vượt giới hạn
3. **Cooldown System** - Tự động dừng sau nhiều loss
4. **Daily Limit** - Bảo vệ tài khoản
5. **Trading Window** - Kiểm soát thời gian
6. **Exposure Limit** - Không over-leverage

## 📈 Monitoring & Analytics

Track các metrics:
- RR achievement rate
- Cooldown trigger frequency
- Daily loss patterns
- AI vs Rule-based performance
- Parameter effectiveness

## 🎯 Best Practices

1. **Start with DEFAULT mode** để hiểu system
2. **Test thoroughly** với test endpoint trước khi live
3. **Set conservative limits** ban đầu
4. **Monitor daily loss** carefully
5. **Use AI mode** khi đã quen với DEFAULT
6. **Review và adjust** parameters định kỳ
7. **Enable cooldown** để tránh revenge trading

## 🐛 Troubleshooting

**Q: Trade bị reject liên tục?**
- Check risk status endpoint
- Verify không trong cooldown
- Check daily loss limit
- Verify trading window

**Q: AI mode không hoạt động?**
- Check ai_prompt_id hoặc ai_prompt_custom
- Verify LLM service availability
- Check logs cho AI response
- Fallback về DEFAULT mode tạm thời

**Q: Cooldown không tự reset?**
- Check consecutive_losses counter
- Verify cooldown config
- Manual reset nếu cần

## 📚 Related Documentation

- [API Reference](./API_REFERENCE.md)
- [LLM Integration](./llm_integration_guide.md)
- [Capital Management](./CAPITAL_MANAGEMENT.md)
- [Position Monitoring](./POSITION_MONITORING_SYSTEM.md)

