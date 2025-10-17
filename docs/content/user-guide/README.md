# 📚 QuantumForge Developer Guide

Welcome to **QuantumForge** - The AI-Powered Trading Bot Platform!

This guide will help you onboard as a developer and create your first trading bot in minutes.

## 🚀 Quick Start

1. **[Getting Started](./01-getting-started.md)** - Set up your account and access QuantumForge Studio
2. **[Creating Your First Bot](./02-creating-your-first-bot.md)** - Build and deploy a simple trading bot
3. **[Bot Templates](./02a-bot-templates.md)** - Understand available bot templates and their roles
4. **[Bot Configuration](./03-bot-configuration.md)** - Configure trading parameters, leverage, and risk management
5. **[LLM Integration](./04-llm-integration.md)** - Add AI intelligence to your bot
6. **[Exchange API Configuration](./04b-exchange-api-configuration.md)** - Set up exchange API keys for backtesting
7. **[Strategy Management](./05-prompt-engineering.md)** - Create and manage trading strategies
8. **[Backtesting](./09-backtesting.md)** - Test your strategies on historical data
9. **[Trading History & Statistics](./10-trading-history-statistics.md)** - View performance and analyze results
10. **[Risk Management](./08-risk-management.md)** - Implement risk controls and position sizing

## 📖 Table of Contents

### Getting Started
- [Account Setup](./01-getting-started.md#account-setup)
- [Development Environment](./01-getting-started.md#development-environment)
- [API Keys](./01-getting-started.md#api-keys)

### Bot Development
- [Creating Bots](./02-creating-your-first-bot.md)
  - Technical Analysis Bots
  - ML/DL Bots
  - LLM-Powered Bots
  - RPA Bots (Browser Automation)
- [Bot Types](./03-bot-configuration.md#bot-types)
  - SPOT Trading
  - FUTURES Trading
  - Signal-Only Bots

### Advanced Features
- [LLM Providers](./04-llm-integration.md)
  - OpenAI Integration
  - Anthropic (Claude)
  - Google Gemini
  - Groq
  - Custom Providers
- [Prompt Templates](./05-prompt-engineering.md)
  - Creating Prompts
  - Attaching Prompts to Bots
  - Prompt Categories
  - Best Practices
- [Risk Management](./08-risk-management.md)
  - Stop Loss / Take Profit
  - Position Sizing
  - AI-Driven Risk Controls
- [Backtesting](./09-backtesting.md)
  - Historical Data Testing
  - Performance Metrics

### Marketplace
- [Publishing Your Bot](./07-publishing-to-marketplace.md)
- [Pricing & Monetization](./10-monetization.md)
- [User Management](./11-user-management.md)

### Reference
- [API Reference](./api-reference.md)
- [Configuration Schema](./configuration-schema.md)
- [Troubleshooting](./troubleshooting.md)
- [FAQ](./faq.md)

## 🎯 Key Concepts

### What is QuantumForge?

QuantumForge is an AI-powered trading bot platform that enables developers to:

- 🤖 **Create intelligent trading bots** with AI/LLM integration
- 📊 **Backtest strategies** on historical data
- 🏪 **Publish to marketplace** and earn passive income
- 🔧 **Configure complex strategies** with no-code interface
- 🌐 **Trade on multiple exchanges** (Binance, Bybit, OKX, etc.)

### Platform Architecture

```
┌─────────────────────────────────────────────────┐
│           QuantumForge Platform                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────┐        ┌──────────────┐      │
│  │  AI Studio  │◄──────►│ Marketplace  │      │
│  │  (Create)   │        │   (Trade)    │      │
│  └─────────────┘        └──────────────┘      │
│         │                       │              │
│         ├───────────────────────┤              │
│         ▼                       ▼              │
│  ┌──────────────────────────────────┐         │
│  │      Trading Engine              │         │
│  │  - SPOT / FUTURES                │         │
│  │  - Multi-Pair Trading            │         │
│  │  - Risk Management               │         │
│  └──────────────────────────────────┘         │
│         │                                      │
│         ▼                                      │
│  ┌──────────────────────────────────┐         │
│  │   Exchange Connectors            │         │
│  │   Binance │ Bybit │ OKX │ ...   │         │
│  └──────────────────────────────────┘         │
│                                                 │
└─────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

- **Backend**: Python (FastAPI)
- **Frontend**: React + TypeScript
- **Blockchain**: Internet Computer (ICP)
- **Database**: MySQL
- **Task Queue**: Celery + Redis
- **AI/LLM**: OpenAI, Anthropic, Gemini, Groq
- **Exchanges**: Binance, Bybit, OKX, Bitget

## 📝 Prerequisites

Before you start, make sure you have:

- ✅ Basic knowledge of trading concepts (SPOT, FUTURES, leverage)
- ✅ Python programming skills (for custom bots)
- ✅ Understanding of REST APIs
- ✅ Exchange account with API keys (Binance, Bybit, etc.)
- ✅ (Optional) AI/LLM API keys for intelligent bots

## 🎓 Learning Path

### For Beginners
1. Start with [Getting Started Guide](./01-getting-started.md)
2. Create a simple [Technical Analysis Bot](./02-creating-your-first-bot.md)
3. Learn [Basic Configuration](./03-bot-configuration.md)
4. Test with [Paper Trading](./01-getting-started.md#testnet-trading)

### For Intermediate Developers
1. Explore [LLM Integration](./04-llm-integration.md)
2. Master [Prompt Engineering](./05-prompt-engineering.md)
3. Implement [Multi-Pair Trading](./06-multi-pair-trading.md)
4. Set up [Advanced Risk Management](./08-risk-management.md)

### For Advanced Developers
1. Build custom ML/DL models
2. Create RPA bots with browser automation
3. Implement custom indicators
4. Optimize for high-frequency trading

## 🆘 Getting Help

- 📧 **Email**: support@quantumforge.ai
- 💬 **Discord**: [Join our community](https://discord.gg/quantumforge)
- 🐛 **Issues**: [GitHub Issues](https://github.com/quantumforge/issues)
- 📖 **Docs**: You're here! 

## 📜 License

QuantumForge is proprietary software. See [LICENSE](../../LICENSE) for details.

---

**Ready to start?** Begin with [Getting Started Guide](./01-getting-started.md) →

