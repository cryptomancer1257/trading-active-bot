# 🎯 Bot Templates & Their Roles

Understanding QuantumForge's pre-built bot templates and when to use each one.

## 📋 Table of Contents

1. [Available Bot Templates](#available-bot-templates)
2. [Template Categories](#template-categories)
3. [Template Selection Guide](#template-selection-guide)
4. [Customizing Templates](#customizing-templates)

---

## 1. Available Bot Templates

QuantumForge Studio provides several pre-built bot templates, each designed for specific trading scenarios:

### 🚀 Universal Futures Bot

**Purpose**: Advanced futures trading with multi-timeframe analysis

**Key Features**:
- ✅ Futures trading support (Binance, Bybit)
- ✅ Multi-timeframe analysis (1m, 5m, 15m, 1h, 4h, 1d)
- ✅ Advanced risk management
- ✅ LLM integration for market analysis
- ✅ Custom leverage settings
- ✅ Stop-loss and take-profit automation

**Best For**:
- Experienced traders
- High-frequency trading
- Leveraged positions
- Advanced strategies

**Trading Pairs**: BTC/USDT, ETH/USDT, SOL/USDT, and 50+ others

### 📈 Universal Spot Bot

**Purpose**: Spot trading with comprehensive market analysis

**Key Features**:
- ✅ Spot trading only (no leverage)
- ✅ Technical indicators (RSI, MACD, Bollinger Bands)
- ✅ Trend following strategies
- ✅ Risk management
- ✅ Portfolio diversification

**Best For**:
- Conservative traders
- Long-term investments
- Beginners
- Portfolio building

**Trading Pairs**: All major spot pairs

### 🎯 Universal Futures Signals Bot

**Purpose**: Generate trading signals without executing trades

**Key Features**:
- ✅ Signal generation only
- ✅ Telegram/Discord notifications
- ✅ No capital management
- ✅ No trade execution
- ✅ Market analysis and alerts

**Best For**:
- Signal providers
- Educational purposes
- Strategy testing
- Market analysis

**Output**: Trading signals via Telegram/Discord

### 🧠 Advanced ML Bot

**Purpose**: Machine learning-powered trading decisions

**Key Features**:
- ✅ AI/ML model integration
- ✅ Pattern recognition
- ✅ Adaptive learning
- ✅ Custom model training
- ✅ Backtesting with ML

**Best For**:
- Data scientists
- Advanced traders
- Custom strategies
- Research purposes

### 📊 Simple SMA Bot

**Purpose**: Basic moving average crossover strategy

**Key Features**:
- ✅ Simple moving averages
- ✅ Golden cross / Death cross
- ✅ Easy to understand
- ✅ Low computational cost
- ✅ Beginner-friendly

**Best For**:
- Beginners
- Learning purposes
- Simple strategies
- Educational use

---

## 2. Template Categories

### By Trading Type

| Template | Spot | Futures | Signals | ML |
|----------|------|---------|---------|----|
| Universal Futures Bot | ❌ | ✅ | ❌ | ❌ |
| Universal Spot Bot | ✅ | ❌ | ❌ | ❌ |
| Universal Futures Signals Bot | ❌ | ✅ | ✅ | ❌ |
| Advanced ML Bot | ✅ | ✅ | ❌ | ✅ |
| Simple SMA Bot | ✅ | ❌ | ❌ | ❌ |

### By Complexity

| Template | Beginner | Intermediate | Advanced |
|----------|----------|--------------|----------|
| Simple SMA Bot | ✅ | ✅ | ❌ |
| Universal Spot Bot | ✅ | ✅ | ✅ |
| Universal Futures Bot | ❌ | ✅ | ✅ |
| Universal Futures Signals Bot | ✅ | ✅ | ✅ |
| Advanced ML Bot | ❌ | ❌ | ✅ |

### By Risk Level

| Template | Low Risk | Medium Risk | High Risk |
|----------|----------|--------------|-----------|
| Simple SMA Bot | ✅ | ❌ | ❌ |
| Universal Spot Bot | ✅ | ✅ | ❌ |
| Universal Futures Bot | ❌ | ✅ | ✅ |
| Universal Futures Signals Bot | ✅ | ✅ | ✅ |
| Advanced ML Bot | ❌ | ✅ | ✅ |

---

## 3. Template Selection Guide

### 🎯 Choose Based on Your Experience

#### For Beginners
```
Recommended: Simple SMA Bot or Universal Spot Bot
Why: Easy to understand, low risk, good for learning
```

#### For Intermediate Traders
```
Recommended: Universal Spot Bot or Universal Futures Signals Bot
Why: More features, better risk management, real market exposure
```

#### For Advanced Traders
```
Recommended: Universal Futures Bot or Advanced ML Bot
Why: Full control, leverage, custom strategies, AI integration
```

### 🎯 Choose Based on Your Goals

#### Learning & Education
- **Simple SMA Bot**: Learn basic concepts
- **Universal Futures Signals Bot**: Study market patterns

#### Conservative Trading
- **Universal Spot Bot**: Safe, proven strategies
- **Universal Futures Signals Bot**: No capital risk

#### Aggressive Trading
- **Universal Futures Bot**: Leverage, advanced features
- **Advanced ML Bot**: AI-powered decisions

#### Signal Provision
- **Universal Futures Signals Bot**: Generate and share signals

### 🎯 Choose Based on Available Capital

#### < $100
- **Universal Futures Signals Bot**: No capital required
- **Simple SMA Bot**: Low capital requirements

#### $100 - $1,000
- **Universal Spot Bot**: Safe spot trading
- **Universal Futures Bot**: Small futures positions

#### > $1,000
- **Universal Futures Bot**: Full features
- **Advanced ML Bot**: Sophisticated strategies

---

## 4. Customizing Templates

### Basic Customization

All templates support these customizations:

#### Trading Parameters
```
- Trading pairs selection
- Timeframe settings
- Risk management rules
- Position sizing
- Stop-loss/take-profit levels
```

#### Strategy Settings
```
- Technical indicator parameters
- Entry/exit conditions
- Market filters
- Time-based rules
- Volatility adjustments
```

#### Risk Management
```
- Maximum position size
- Daily loss limits
- Drawdown protection
- Correlation limits
- Volatility filters
```

### Advanced Customization

#### Universal Futures Bot
```
- Leverage settings (1x - 125x)
- Multi-timeframe analysis
- Advanced order types
- Custom indicators
- Market regime detection
```

#### Advanced ML Bot
```
- Model selection
- Feature engineering
- Training parameters
- Validation methods
- Prediction confidence
```

### Template Modification Workflow

1. **Select Template**
   ```
   Studio → Create Bot → Choose Template
   ```

2. **Basic Configuration**
   ```
   - Bot name and description
   - Trading pairs
   - Timeframes
   - Risk parameters
   ```

3. **Advanced Settings**
   ```
   - Strategy parameters
   - Risk management
   - Notification settings
   - Performance targets
   ```

4. **Testing & Validation**
   ```
   - Backtest on historical data
   - Paper trading
   - Performance analysis
   - Risk assessment
   ```

5. **Deployment**
   ```
   - Live trading
   - Monitoring
   - Optimization
   - Scaling
   ```

---

## 🎯 Next Steps

Now that you understand the available templates:

**Continue to**: [Bot Configuration →](./03-bot-configuration.md)

**Or**: [LLM Integration →](./04-llm-integration.md)

---

## 🆘 Template Selection Help

### Still Not Sure?

**Take the Quiz**: [Which Bot Template is Right for Me?](https://quantumforge.ai/bot-quiz)

### Need More Information?

- 📧 **Support**: support@quantumforge.ai
- 💬 **Community**: [Discord Server](https://discord.gg/quantumforge)
- 📖 **Documentation**: [Full API Reference](https://docs.quantumforge.ai)

---

**Ready to configure your bot?** → [Next: Bot Configuration](./03-bot-configuration.md)
