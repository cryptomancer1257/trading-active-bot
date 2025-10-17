# 🚀 Getting Started with QuantumForge Studio

Welcome to QuantumForge Studio! This comprehensive guide will walk you through creating, configuring, and managing AI trading bots on the **quantumforge.cryptomancer.ai** platform.

## 🎯 What You'll Learn

- ✅ How to create your first trading bot
- ✅ Understanding bot templates and their roles
- ✅ Setting up LLM providers for AI analysis
- ✅ Configuring exchange API keys for backtesting
- ✅ Running backtests and analyzing results
- ✅ Managing risk and strategies
- ✅ Viewing trading history and profit statistics

## 📋 Table of Contents

1. [Account Setup](#account-setup)
2. [Development Environment](#development-environment)
3. [Exchange API Keys](#exchange-api-keys)
4. [Your First Login](#your-first-login)
5. [Platform Overview](#platform-overview)

---

## 1. Account Setup

### Creating Your Account

1. **Navigate to QuantumForge Studio**
   ```
   https://quantumforge.cryptomancer.ai
   ```

2. **Sign Up Options**
   - 📧 Email & Password
   - 🔐 Google OAuth
   - 🌐 Internet Computer (ICP) Principal

3. **Email Verification**
   - Check your inbox for verification email
   - Click the verification link
   - Your account is now active!

### Account Types

| Type | Description | Access |
|------|-------------|--------|
| **Developer** | Create and manage bots | Studio + API |
| **Trader** | Rent and use bots | Marketplace only |
| **Enterprise** | Custom solutions | Full platform |

---

## 2. Development Environment

### Option A: Web Interface (Recommended for Beginners)

The easiest way to get started - no installation required!

1. Log in to [QuantumForge Studio](https://studio.quantumforge.ai)
2. Navigate to **"My Bots"**
3. Click **"Create New Bot"**
4. Use the visual bot builder

### Option B: Local Development (Advanced)

For developers who want full control:

#### Prerequisites

```bash
# Check Python version (3.9+ required)
python --version

# Check Git
git --version
```

#### Clone the Repository

```bash
# Clone the project
git clone https://github.com/quantumforge/trading-bot-sdk.git
cd trading-bot-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### Configuration

Create a `.env` file:

```bash
# Studio API Configuration
STUDIO_API_URL=https://api.quantumforge.ai
STUDIO_API_KEY=your_api_key_here

# Exchange API Keys (we'll add these later)
BINANCE_API_KEY=
BINANCE_API_SECRET=

# Database (for local testing)
DATABASE_URL=sqlite:///./test.db

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```

#### Verify Installation

```bash
# Run the test suite
pytest tests/

# Start local development server
python main.py
```

You should see:
```
✅ QuantumForge SDK initialized successfully
🚀 Server running on http://localhost:8000
```

---

## 3. Exchange API Keys

To trade, you need API keys from your exchange.

### Binance Setup

1. **Log in to Binance**
   - Go to [www.binance.com](https://www.binance.com)
   - Navigate to **Profile → API Management**

2. **Create API Key**
   - Click **"Create API"**
   - Label: `QuantumForge Trading`
   - Complete 2FA verification

3. **Configure Permissions**
   ```
   ✅ Enable Reading
   ✅ Enable Spot & Margin Trading
   ✅ Enable Futures Trading (if needed)
   ❌ Disable Withdrawals (for security)
   ```

4. **Whitelist IPs (Optional but Recommended)**
   ```
   Add QuantumForge server IPs:
   - 123.456.789.0
   - 123.456.789.1
   ```

5. **Save Your Keys**
   ```
   API Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Secret Key: yyyyyyyyyyyyyyyyyyyyyyyyy
   ```
   
   ⚠️ **Important**: Never share your Secret Key!

### Bybit Setup

1. **Log in to Bybit**
   - Go to [www.bybit.com](https://www.bybit.com)
   - Navigate to **Account & Security → API**

2. **Create API Key**
   - Click **"Create New Key"**
   - Key Type: **"System-generated API Keys"**
   - API key name: `QuantumForge`

3. **Set Permissions**
   ```
   ✅ Read-Write
   ✅ Contract Trading
   ✅ Spot Trading
   ❌ Asset Transfer
   ❌ Withdrawal
   ```

4. **Save Keys**
   - Copy both API Key and Secret Key
   - Store them securely

### Adding Keys to QuantumForge

#### Via Web Interface

1. Go to **Settings → Exchange API Credentials**
2. Click **"Add New Credential"**
3. Fill in the form:
   ```
   Exchange: Binance / Bybit
   Trading Mode: Spot / Futures
   Environment: Testnet / Mainnet
   API Key: your_api_key
   Secret Key: your_secret_key
   ```
4. Click **"Save & Test Connection"**
5. ✅ You should see: "Connection successful!"

#### Via API

```python
import requests

# Add exchange credentials
response = requests.post(
    "https://api.quantumforge.ai/settings/exchange-credentials",
    headers={"Authorization": f"Bearer {YOUR_API_TOKEN}"},
    json={
        "exchange": "BINANCE",
        "trading_mode": "SPOT",
        "environment": "MAINNET",
        "api_key": "your_binance_api_key",
        "api_secret": "your_binance_secret_key"
    }
)

print(response.json())
# {"success": true, "message": "Credentials saved successfully"}
```

---

## 4. Your First Login

### Dashboard Overview

After logging in, you'll see:

```
┌─────────────────────────────────────────────┐
│  🏠 QuantumForge Studio                     │
├─────────────────────────────────────────────┤
│                                             │
│  📊 My Bots (0)                            │
│  ├─ Create New Bot                         │
│  ├─ Import Bot                             │
│  └─ Bot Templates                          │
│                                             │
│  🤖 LLM Providers (0)                      │
│  └─ Add Provider                           │
│                                             │
│  ✍️  Prompt Templates (0)                   │
│  └─ Create Prompt                          │
│                                             │
│  📈 Active Subscriptions (0)               │
│                                             │
│  ⚙️  Settings                               │
│  └─ Exchange API Keys                      │
│                                             │
└─────────────────────────────────────────────┘
```

### Key Sections

1. **My Bots**
   - View all your bots
   - Create new bots
   - Edit/Delete bots
   - Monitor performance

2. **LLM Providers**
   - Add AI providers (OpenAI, Claude, etc.)
   - Manage API keys
   - Monitor usage & billing

3. **Prompt Templates**
   - Create reusable prompts
   - Organize by category
   - Attach to bots

4. **Subscriptions**
   - Active bot rentals
   - Performance tracking
   - Trading history

5. **Settings**
   - Exchange API keys
   - Risk preferences
   - Notifications

---

## 5. Platform Overview

### Two Main Components

#### 🎨 AI Studio (Developer Side)

**Purpose**: Create and manage trading bots

**Key Features**:
- Visual bot builder
- Code editor for advanced bots
- Backtesting tools
- LLM integration
- Prompt engineering
- Performance analytics

**URL**: `https://studio.quantumforge.ai`

#### 🏪 Marketplace (Trader Side)

**Purpose**: Discover and rent trading bots

**Key Features**:
- Browse verified bots
- Compare performance
- Rent bots (ICP, PayPal, Credit Card)
- Real-time monitoring
- Auto-renewal

**URL**: `https://marketplace.quantumforge.ai`

### Testnet vs Mainnet

| Feature | Testnet | Mainnet |
|---------|---------|---------|
| **Real Money** | ❌ No | ✅ Yes |
| **Purpose** | Testing | Live Trading |
| **API Keys** | Testnet keys | Production keys |
| **Risk** | Zero | Real money at risk |
| **Recommended For** | Beginners, Testing | Experienced traders |

⚠️ **Always test on Testnet first!**

---

## 🎯 Next Steps

Now that you're set up, let's create your first bot!

**Continue to**: [Creating Your First Bot →](./02-creating-your-first-bot.md)

---

## 🆘 Troubleshooting

### Common Issues

#### "Email verification link expired"
```
Solution: Request a new verification email
Settings → Account → Resend Verification
```

#### "Invalid API keys"
```
Solution: 
1. Check keys are copied correctly (no spaces)
2. Verify permissions are enabled
3. Try testnet keys first
```

#### "Cannot connect to exchange"
```
Solution:
1. Check exchange is not under maintenance
2. Verify IP whitelist (if enabled)
3. Test with Postman/curl first
```

### Getting Help

- 📧 Email: support@quantumforge.ai
- 💬 Discord: [Community Server](https://discord.gg/quantumforge)
- 📖 FAQ: [Frequently Asked Questions](./faq.md)

---

**Ready to create your first bot?** → [Next: Creating Your First Bot](./02-creating-your-first-bot.md)

