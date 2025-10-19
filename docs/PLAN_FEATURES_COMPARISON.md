
# 🎯 Complete Plan Features Comparison

## Overview
QuantumForge offers 3 pricing tiers designed for different trading needs:
- **FREE**: For testing and learning ($0/month)
- **PRO**: For serious traders ($60/month)
- **ULTRA**: For professional traders ($500/month)

---

## 📊 Feature Comparison Table

| **Feature Group**               | **Feature**                           | **FREE**        | **PRO ($60)**     | **ULTRA ($500)**  |
| ------------------------------- | ------------------------------------- | --------------- | ----------------- | ----------------- |
| **1️⃣ Core Limits**             | Maximum Entities (bots)               | 5 bots          | 20 bots           | ∞ Unlimited       |
|                                 | Subscriptions per Bot                 | 5 max           | 20                | ∞ Unlimited       |
|                                 | Trading Environment                   | Testnet Only    | Testnet + Mainnet | Testnet + Mainnet |
|                                 | Compute Quota (API calls per bot/day) | 24              | 240               | 2400              |
|                                 | Bot Subscription Duration             | 3-day trial     | 30 days           | 30 days           |
|                                 | LLM Provider                          | Low Quality     | High Quality      | High Quality      |
| **2️⃣ Trading & Performance**   | Trading Type                          | ✅ SPOT, FUTURES | ✅ SPOT, FUTURES   | ✅ SPOT, FUTURES   |
|                                 | Exchange Support                      | Multiple        | Multiple          | Multiple          |
|                                 | Risk Management                       | ✅               | ✅                 | ✅                 |
|                                 | Capital Management                    | ✅               | ✅                 | ✅                 |
|                                 | Strategies Library                    | ✅               | ✅                 | ✅                 |
|                                 | Bot Template                          | ✅               | ✅                 | ✅                 |
|                                 | Execution Log Monitoring              | ✅               | ✅                 | ✅                 |
| **3️⃣ Communication & Support** | Telegram/Discord Notification         | ✅               | ✅                 | ✅                 |
|                                 | Analytic Dashboard                    | ✅               | ✅                 | ✅                 |
|                                 | Subscription Management               | ✅               | ✅                 | ✅                 |
|                                 | Priority Support                      | Community Only  | 24/7 Support      | 24/7 Support      |
| **4️⃣ Marketplace Access**      | Publish to Marketplace                | ❌ Not Allowed   | ✅ Full Access     | ✅ Full Access     |

---

## 🔧 Backend Configuration

### Plan Constants (`api/endpoints/plans.py`)

```python
FREE_PLAN_CONFIG = {
    "plan_name": "free",
    "price_usd": 0.00,
    "max_bots": 5,
    "max_subscriptions_per_bot": 5,
    "allowed_environment": "testnet",
    "publish_marketplace": False,
    "subscription_expiry_days": 3,
    "compute_quota_per_day": 24,
    "revenue_share_percentage": 0.00
}

PRO_PLAN_CONFIG = {
    "plan_name": "pro",
    "price_usd": 60.00,
    "max_bots": 20,
    "max_subscriptions_per_bot": 20,
    "allowed_environment": "mainnet",
    "publish_marketplace": True,
    "subscription_expiry_days": 30,
    "compute_quota_per_day": 240,
    "revenue_share_percentage": 90.00
}

ULTRA_PLAN_CONFIG = {
    "plan_name": "ultra",
    "price_usd": 500.00,
    "max_bots": 999999,  # Unlimited
    "max_subscriptions_per_bot": 999999,  # Unlimited
    "allowed_environment": "mainnet",
    "publish_marketplace": True,
    "subscription_expiry_days": 30,
    "compute_quota_per_day": 2400,
    "revenue_share_percentage": 90.00
}
```

---

## 📝 Feature Details

### 1️⃣ Core Limits (Differentiated by Plan)

#### Maximum Entities (Bots)
- **FREE**: 5 bots maximum
- **PRO**: 20 bots maximum
- **ULTRA**: Unlimited bots

#### Subscriptions per Bot
- **FREE**: 5 active subscriptions per bot
- **PRO**: 20 active subscriptions per bot
- **ULTRA**: Unlimited subscriptions

#### Trading Environment
- **FREE**: Testnet only (safe testing with fake money)
- **PRO**: Both Testnet and Mainnet (real trading)
- **ULTRA**: Both Testnet and Mainnet

#### Compute Quota (API calls per bot/day)
- **FREE**: 24 API calls per bot per day
- **PRO**: 240 API calls per bot per day (10x)
- **ULTRA**: 2400 API calls per bot per day (100x)

#### Bot Subscription Duration
- **FREE**: 3-day trial period
- **PRO**: 30 days
- **ULTRA**: 30 days

#### LLM Provider Quality
- **FREE**: Auto-selected free provider (Gemini 2.0 Flash)
- **PRO**: High-quality providers (GPT-4, Claude 3.5, Gemini Pro)
- **ULTRA**: High-quality providers with priority access

---

### 2️⃣ Trading & Performance (Available for All Plans)

#### Trading Type
All plans support:
- ✅ SPOT Trading
- ✅ FUTURES Trading
- ✅ Multiple trading pairs
- ✅ Multi-timeframe analysis

#### Exchange Support
All plans have access to:
- Binance
- Bybit
- OKX
- (More exchanges coming soon)

#### Risk Management
All plans include:
- Stop Loss / Take Profit automation
- Position sizing based on risk percentage
- Maximum drawdown limits
- Risk/Reward ratio validation

#### Capital Management
All plans include:
- Dynamic position sizing
- Capital allocation strategies
- Leverage management
- Portfolio diversification

#### Strategies Library
All plans have access to:
- Pre-built trading strategies
- Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Custom strategy builder
- Backtesting capabilities

#### Bot Template
All plans include:
- Universal Futures Bot
- Universal Spot Bot
- Signals Bot (notifications only)
- Custom bot creation

#### Execution Log Monitoring
All plans include:
- Real-time execution logs
- Trade history
- Performance metrics
- Error tracking and alerts

---

### 3️⃣ Communication & Support

#### Telegram/Discord Notification
All plans include:
- Trade execution alerts
- Bot status updates
- Price alerts
- Performance summaries

#### Analytic Dashboard
All plans have access to:
- Real-time portfolio overview
- Profit/Loss tracking
- Win rate statistics
- Trade history visualization

#### Subscription Management
All plans include:
- Start/Stop/Pause bot subscriptions
- Modify trading parameters
- View subscription status
- Renew subscriptions

#### Priority Support
- **FREE**: Community support (Discord, documentation)
- **PRO**: 24/7 email support + priority Discord
- **ULTRA**: 24/7 dedicated support + Telegram/WhatsApp

---

### 4️⃣ Marketplace Access (Differentiated by Plan)

#### Publish to Marketplace
- **FREE**: ❌ Cannot publish bots to marketplace
- **PRO**: ✅ Publish up to 20 bots, 90% revenue share
- **ULTRA**: ✅ Publish unlimited bots, 90% revenue share

**Marketplace Benefits:**
- Earn passive income from bot rentals
- Gain reputation as a strategy creator
- Access to marketplace analytics
- Automatic payment processing

---

## 💡 Plan Recommendations

### Choose FREE if:
- 🎓 You're learning algorithmic trading
- 🧪 You want to test strategies on Testnet
- 📚 You need basic features to get started
- 💰 You're not ready to invest yet

### Choose PRO if:
- 💼 You're a serious trader ready for Mainnet
- 📈 You want to run multiple bots simultaneously
- 🤖 You need high-quality AI analysis
- 💸 You want to publish bots and earn passive income

### Choose ULTRA if:
- 🚀 You're a professional trader or institution
- ⚡ You need unlimited bots and subscriptions
- 🔥 You require maximum API quota for high-frequency trading
- 👑 You want dedicated support and priority features

---

## 🎯 Upgrade Benefits

### FREE → PRO ($60/mo)
- ✅ 5 → 20 bots (4x increase)
- ✅ Testnet → Mainnet access
- ✅ 24 → 240 API calls (10x increase)
- ✅ 3 days → 30 days duration
- ✅ Can publish to marketplace
- ✅ 24/7 priority support

### PRO → ULTRA ($500/mo)
- ✅ 20 → Unlimited bots
- ✅ 240 → 2400 API calls (10x increase)
- ✅ 20 → Unlimited subscriptions/bot
- ✅ Dedicated support (Telegram/WhatsApp)
- ✅ Priority LLM access
- ✅ Early access to new features

---

## 🔐 Technical Implementation

### Feature Flags (All Plans)
```python
# These features are available for ALL plans
AVAILABLE_FOR_ALL = [
    "spot_trading",
    "futures_trading",
    "risk_management",
    "capital_management",
    "strategies_library",
    "bot_templates",
    "execution_monitoring",
    "telegram_notifications",
    "discord_notifications",
    "analytic_dashboard",
    "subscription_management"
]

# These features are gated by plan
PLAN_GATED_FEATURES = {
    "max_bots": {
        "free": 5,
        "pro": 20,
        "ultra": 999999
    },
    "mainnet_access": {
        "free": False,
        "pro": True,
        "ultra": True
    },
    "publish_marketplace": {
        "free": False,
        "pro": True,
        "ultra": True
    },
    "compute_quota": {
        "free": 24,
        "pro": 240,
        "ultra": 2400
    },
    "priority_support": {
        "free": "community",
        "pro": "24/7",
        "ultra": "dedicated"
    }
}
```

---

## 📞 Support Channels

### Community Support (FREE)
- Discord: #free-plan-support
- Documentation: docs.quantumforge.ai
- Community Forum: forum.quantumforge.ai

### 24/7 Email Support (PRO)
- Email: pro-support@quantumforge.ai
- Response time: < 4 hours
- Priority Discord: #pro-support

### Dedicated Support (ULTRA)
- Email: ultra-support@quantumforge.ai
- Telegram: @quantumforge_ultra
- WhatsApp: +1-XXX-XXX-XXXX
- Response time: < 1 hour
- Dedicated account manager

---

## 🚀 Getting Started

1. **Sign up** at [quantumforge.ai](https://quantumforge.ai)
2. **Start with FREE** plan to explore features
3. **Upgrade to PRO** when ready for Mainnet trading
4. **Scale to ULTRA** for professional/institutional needs

**Need help choosing?** Contact sales@quantumforge.ai

