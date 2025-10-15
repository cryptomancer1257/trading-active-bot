# ❓ Frequently Asked Questions (FAQ)

Common questions and answers about QuantumForge platform.

## 📋 Table of Contents

### General
- [What is QuantumForge?](#what-is-quantumforge)
- [Who can use QuantumForge?](#who-can-use-quantumforge)
- [Is QuantumForge safe?](#is-quantumforge-safe)
- [What exchanges are supported?](#what-exchanges-are-supported)

### Getting Started
- [How do I create an account?](#how-do-i-create-an-account)
- [Do I need coding skills?](#do-i-need-coding-skills)
- [How much capital do I need?](#how-much-capital-do-i-need)
- [Can I test before using real money?](#can-i-test-before-using-real-money)

### Bot Creation
- [How long does it take to create a bot?](#how-long-to-create-bot)
- [Can I use AI in my bot?](#can-i-use-ai-in-my-bot)
- [What's the difference between bot types?](#bot-types-difference)
- [Can I trade multiple pairs?](#can-i-trade-multiple-pairs)

### Risk & Trading
- [How much can I lose?](#how-much-can-i-lose)
- [What is leverage?](#what-is-leverage)
- [Do I need to monitor my bot 24/7?](#need-to-monitor-247)
- [Can the bot guarantee profits?](#guarantee-profits)

### Marketplace
- [How do I earn money as a developer?](#how-to-earn-money)
- [What commission does QuantumForge take?](#platform-commission)
- [How do I rent a bot?](#how-to-rent-bot)
- [Can I cancel my subscription?](#can-cancel-subscription)

### Technical
- [API rate limits?](#api-rate-limits)
- [How is my API key stored?](#api-key-security)
- [Can I use webhooks?](#can-use-webhooks)
- [What about data privacy?](#data-privacy)

---

## General

### What is QuantumForge?

**QuantumForge** is an AI-powered trading bot platform with two main components:

1. **AI Studio** - Where developers create trading bots
2. **Marketplace** - Where traders rent and use bots

Think of it as an "App Store for Trading Bots" where you can:
- Create intelligent trading bots (no coding required)
- Backtest on historical data
- Publish and monetize your bots
- Rent proven bots created by experts

---

### Who can use QuantumForge?

**Developers/Creators:**
- Algo traders who want to monetize strategies
- Python developers
- AI/ML engineers
- Anyone with a profitable trading strategy

**Traders/Renters:**
- Busy professionals who want passive income
- Beginners who want to learn from experts
- Experienced traders looking for new strategies
- Anyone who wants to automate trading

**No coding required** for basic bot creation!

---

### Is QuantumForge safe?

Yes, QuantumForge implements multiple security layers:

**API Key Security:**
- ✅ Encrypted storage (AES-256)
- ✅ Never stored in plain text
- ✅ Withdrawal permissions disabled
- ✅ IP whitelisting supported

**Platform Security:**
- ✅ Built on Internet Computer (ICP) blockchain
- ✅ Non-custodial (we never hold your funds)
- ✅ Regular security audits
- ✅ 2FA authentication

**Your funds stay on your exchange** - QuantumForge only executes trades via API.

---

### What exchanges are supported?

**Fully Supported:**
- ✅ Binance (SPOT + FUTURES)
- ✅ Bybit (SPOT + FUTURES)
- ✅ OKX (SPOT + FUTURES)
- ✅ Bitget (FUTURES)
- ✅ Huobi (SPOT)

**Coming Soon:**
- 🔄 KuCoin
- 🔄 Gate.io
- 🔄 Kraken

Each bot can trade on multiple exchanges simultaneously.

---

## Getting Started

### How do I create an account?

**3 Easy Steps:**

1. Go to [studio.quantumforge.ai](https://studio.quantumforge.ai)
2. Click **"Sign Up"**
3. Choose signup method:
   - 📧 Email + Password
   - 🔐 Google OAuth
   - 🌐 Internet Computer (ICP) Principal

**Verification:**
- Email verification required (check spam folder)
- No KYC needed
- Free to create account

---

### Do I need coding skills?

**No!** QuantumForge offers multiple approaches:

**For Non-Coders:**
- ✅ Visual bot builder (drag & drop)
- ✅ Pre-built templates
- ✅ No-code configuration
- ✅ AI-powered bots (GPT, Claude)

**For Developers:**
- ✅ Python bot development
- ✅ Custom indicators
- ✅ ML/DL model integration
- ✅ Full API access

Start with templates, scale to custom code when ready!

---

### How much capital do I need?

**Minimum Requirements:**

| Trading Type | Min Capital | Recommended |
|--------------|-------------|-------------|
| **SPOT (Testnet)** | $0 (fake money) | Test freely |
| **SPOT (Live)** | $100 | $500+ |
| **FUTURES (3x)** | $300 | $1,000+ |
| **FUTURES (10x)** | $500 | $2,000+ |

**Reality Check:**
- Smaller capital = smaller profits
- Need enough to absorb losses
- Recommended: Start with $500-1,000

---

### Can I test before using real money?

**Absolutely! We strongly recommend testing first:**

**Option 1: Backtesting**
- Test on historical data
- See how strategy performed in past
- FREE, instant results

**Option 2: Paper Trading (Testnet)**
- Real-time market data
- Fake money
- Exactly like live trading
- FREE, no risk

**Option 3: Small Capital Live**
- Start with $100-500
- Real money, real learning
- Low risk way to test

**Recommendation:** Backtest → Testnet (1 week) → Small live (1 month) → Full capital

---

## Bot Creation

### How long does it take to create a bot? {#how-long-to-create-bot}

**Depends on complexity:**

| Bot Type | Time Required | Skill Level |
|----------|---------------|-------------|
| **Template Bot** | 5-10 minutes | Beginner |
| **Custom Technical** | 30-60 minutes | Intermediate |
| **LLM-Powered** | 1-2 hours | Intermediate |
| **ML/DL Bot** | 1-2 days | Advanced |
| **Full Custom** | 1-2 weeks | Expert |

**Fastest Path:**
1. Choose template (2 min)
2. Configure parameters (5 min)
3. Backtest (3 min)
4. Deploy (1 min)

**Total: ~11 minutes!**

---

### Can I use AI in my bot?

**Yes! Multiple ways:**

**1. LLM Integration (GPT, Claude, Gemini)**
```python
{
  "bot_type": "LLM",
  "llm_provider": "OpenAI GPT-4",
  "use_cases": [
    "Market sentiment analysis",
    "News interpretation",
    "Dynamic strategy adjustment"
  ]
}
```

**2. Machine Learning Models**
```python
{
  "bot_type": "ML",
  "model": "your_trained_model.pkl",
  "framework": "scikit-learn | TensorFlow | PyTorch"
}
```

**3. Hybrid (AI + Technical)**
```python
{
  "bot_type": "TECHNICAL",
  "llm_filter": true,  # AI confirms signals
  "llm_risk_management": true
}
```

---

### What's the difference between bot types? {#bot-types-difference}

| Type | How It Works | Best For |
|------|-------------|----------|
| **TECHNICAL** | Uses indicators (RSI, MACD, etc.) | Beginners, clear rules |
| **ML/DL** | Uses trained AI models | Pattern recognition |
| **LLM** | Uses GPT/Claude for decisions | Market intelligence |
| **RPA** | Browser automation | Complex workflows |

**SPOT vs FUTURES:**
- **SPOT**: Buy and sell actual crypto (safer)
- **FUTURES**: Contracts with leverage (riskier, higher returns)

---

### Can I trade multiple pairs?

**Yes! Multi-pair trading supported:**

```python
{
  "trading_pair": "BTC/USDT",      # Primary
  "secondary_trading_pairs": [      # Secondary
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT"
  ]
}
```

**Benefits:**
- More trading opportunities
- Better diversification
- Higher capital efficiency

**Recommendation:** Start with 1-2 pairs, scale to 3-5 max

---

## Risk & Trading

### How much can I lose?

**Honest answer: You can lose everything if you're reckless.**

**But with proper risk management:**

```python
# Example with 1% risk per trade
Capital: $10,000
Risk per trade: 1% = $100

Even if you lose 10 trades in a row:
Loss = $1,000 (10% of capital)
Remaining = $9,000
Still in the game ✅
```

**Key Rules:**
- ✅ Never risk more than 1-2% per trade
- ✅ Always use stop losses
- ✅ Start small
- ✅ Don't use excessive leverage

**Reality:** Most losses come from poor risk management, not bad strategies.

---

### What is leverage?

**Simple explanation:**

```
No Leverage (1x):
You have $1,000 → Can trade $1,000
Price moves +10% → You make $100

With 10x Leverage:
You have $1,000 → Can trade $10,000
Price moves +10% → You make $1,000 🚀

BUT:
Price moves -10% → You lose $1,000 (entire capital!) 💥
```

**Leverage = Magnified gains AND losses**

**Recommendations:**
- Beginners: No leverage (1x)
- Intermediate: 3-5x max
- Advanced: 5-10x
- **Avoid: >20x** (extreme risk)

---

### Do I need to monitor my bot 24/7? {#need-to-monitor-247}

**No, but recommended daily check-ins:**

**What Bots Do Automatically:**
- ✅ Monitor markets 24/7
- ✅ Execute trades
- ✅ Manage risk (stop loss/take profit)
- ✅ Send notifications

**What YOU Should Do:**
- ✅ Check daily performance (5 min)
- ✅ Review weekly stats (15 min)
- ✅ Adjust if market conditions change
- ✅ Respond to alerts

**Set up notifications:**
```python
{
  "notify_on_trade": true,
  "notify_on_profit": true,
  "notify_on_loss": true,
  "channels": ["EMAIL", "TELEGRAM"]
}
```

---

### Can the bot guarantee profits? {#guarantee-profits}

**NO. Anyone who guarantees profits in trading is lying.**

**Reality:**
- ❌ No bot wins 100% of the time
- ❌ Past performance ≠ future results
- ❌ Markets are unpredictable

**What Good Bots CAN Do:**
- ✅ Improve win rate (55-70% is good)
- ✅ Enforce discipline (no emotional trading)
- ✅ Execute faster than humans
- ✅ Trade 24/7 without fatigue

**Our Best Bots:**
- Win rate: 60-70%
- Monthly return: 5-15%
- Max drawdown: 10-20%

**Still involves risk!**

---

## Marketplace

### How do I earn money as a developer? {#how-to-earn-money}

**Simple: Create bots → Publish → Earn passive income**

**Revenue Model:**
```
User pays $100/month to rent your bot
├─ Platform fee: $5 (5%)
└─ You receive: $95 (95%)
```

**Example Earnings:**

| Users | Monthly Revenue | Annual Revenue |
|-------|-----------------|----------------|
| 10 | $950 | $11,400 |
| 50 | $4,750 | $57,000 |
| 100 | $9,500 | $114,000 |
| 500 | $47,500 | $570,000 |

**Top developers earn $50k-100k/year!**

**Requirements:**
- Bot must pass review (quality check)
- Must have backtest results
- Clear risk disclosure

---

### What commission does QuantumForge take? {#platform-commission}

**Only 5% of subscription revenue**

```
Example:
User pays: $100/month
Platform: $5 (5%)
You get: $95 (95%)
```

**No hidden fees:**
- ❌ No listing fees
- ❌ No setup fees
- ❌ No withdrawal fees (ICP)
- ✅ Just 5% per transaction

**Industry comparison:**
- App Store: 30%
- Google Play: 30%
- Patreon: 5-12%
- **QuantumForge: 5%** 🎉

---

### How do I rent a bot? {#how-to-rent-bot}

**4 Easy Steps:**

1. **Browse Marketplace**
   - Filter by category, performance, price
   - Read bot description
   - Check backtest results

2. **Select Bot**
   - Click "Rent Bot"
   - Choose duration (daily/quarterly/yearly)

3. **Configure**
   - Add exchange API keys
   - Set risk parameters
   - Choose network (testnet/mainnet)

4. **Pay & Start**
   - Payment: ICP, PayPal, or Credit Card
   - Bot starts trading immediately!

**Total time: ~10 minutes**

---

### Can I cancel my subscription? {#can-cancel-subscription}

**Yes, anytime!**

**Cancellation Policy:**
```
- Cancel anytime (no lock-in)
- Access until end of paid period
- No refunds for unused time
- Can re-subscribe later
```

**How to Cancel:**
1. Go to **Active Subscriptions**
2. Click bot → **"Cancel Subscription"**
3. Confirm cancellation
4. Bot stops at period end

**Pro tip:** Pause instead of cancel if taking a break!

---

## Technical

### API rate limits? {#api-rate-limits}

**QuantumForge API:**
```
Free Tier:
- 100 requests/minute
- 10,000 requests/day

Pro Tier:
- 1,000 requests/minute
- 100,000 requests/day

Enterprise:
- Custom limits
```

**Exchange APIs:**
- Binance: 1,200 requests/minute
- Bybit: 120 requests/minute
- OKX: 100 requests/2 seconds

**Bots automatically handle rate limiting**

---

### How is my API key stored? {#api-key-security}

**Security Measures:**

1. **Encryption:**
   - AES-256 encryption at rest
   - TLS 1.3 in transit
   - Keys encrypted before database storage

2. **Access Control:**
   - Only your bots can access your keys
   - Never logged or displayed
   - Auto-rotate every 90 days (optional)

3. **Permissions:**
   - ✅ Trading only
   - ❌ Withdrawal disabled
   - ❌ Account management disabled

4. **Additional Security:**
   - IP whitelisting
   - 2FA required
   - Audit logs

**We cannot decrypt your keys without your password**

---

### Can I use webhooks? {#can-use-webhooks}

**Yes! Webhook support for:**

**Incoming Webhooks (Trigger bot):**
```python
POST https://api.quantumforge.ai/webhooks/{bot_id}
{
  "action": "BUY" | "SELL",
  "pair": "BTC/USDT",
  "size": 1000
}
```

**Outgoing Webhooks (Bot events):**
```python
# Configure webhook URL
{
  "webhook_url": "https://your-server.com/webhook",
  "events": [
    "trade_executed",
    "stop_loss_hit",
    "daily_report"
  ]
}

# Receive events
POST https://your-server.com/webhook
{
  "event": "trade_executed",
  "bot_id": "123",
  "data": {...}
}
```

---

### What about data privacy? {#data-privacy}

**We take privacy seriously:**

**What We Collect:**
- ✅ Account info (email, username)
- ✅ Trading stats (for performance)
- ✅ Usage analytics

**What We DON'T Collect:**
- ❌ Personal financial info
- ❌ Exchange passwords
- ❌ Withdrawal addresses
- ❌ Personal documents

**Data Protection:**
- GDPR compliant
- Data encryption
- Regular security audits
- Right to deletion

**Your trading data is private and never sold to third parties.**

---

## 🆘 Still Have Questions?

### Contact Support

- 📧 **Email**: support@quantumforge.ai
- 💬 **Discord**: [Join Community](https://discord.gg/quantumforge)
- 📖 **Docs**: [Full Documentation](../README.md)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/quantumforge/issues)

### Response Times

- Critical issues: <2 hours
- General inquiries: <24 hours
- Feature requests: <48 hours

---

**Next**: [Troubleshooting Guide →](./troubleshooting.md)

