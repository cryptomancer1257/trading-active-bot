# 🔑 Exchange API Configuration

Learn how to configure exchange API keys for backtesting and live trading in QuantumForge Studio.

## 📋 Table of Contents

1. [Why You Need Exchange API Keys](#why-you-need-exchange-api-keys)
2. [Supported Exchanges](#supported-exchanges)
3. [API Key Setup Guide](#api-key-setup-guide)
4. [Adding Keys to QuantumForge](#adding-keys-to-quantumforge)
5. [Security Best Practices](#security-best-practices)
6. [Troubleshooting](#troubleshooting)

---

## 1. Why You Need Exchange API Keys

### For Backtesting
- **Historical Data Access**: Download real market data for accurate backtests
- **Realistic Conditions**: Test with actual market conditions and spreads
- **Exchange-Specific Features**: Test features unique to each exchange
- **Data Quality**: Ensure backtest results reflect real trading conditions

### For Live Trading
- **Order Execution**: Place real buy/sell orders
- **Account Management**: Monitor balances and positions
- **Risk Management**: Implement stop-losses and position limits
- **Portfolio Tracking**: Track performance and P&L

### What API Keys Enable
```
✅ Read market data (prices, order book, trades)
✅ Read account information (balance, positions)
✅ Place orders (buy, sell, stop-loss)
✅ Cancel orders
✅ View trading history
❌ Withdraw funds (disabled for security)
```

---

## 2. Supported Exchanges

### Primary Exchanges

| Exchange | Spot Trading | Futures Trading | Testnet | Mainnet |
|----------|--------------|------------------|---------|---------|
| **Binance** | ✅ | ✅ | ✅ | ✅ |
| **Bybit** | ✅ | ✅ | ✅ | ✅ |
| **OKX** | ✅ | ✅ | ✅ | ✅ |
| **KuCoin** | ✅ | ❌ | ✅ | ✅ |

### Exchange Comparison

#### Binance
**Pros**:
- ✅ Largest liquidity
- ✅ Most trading pairs
- ✅ Advanced order types
- ✅ Excellent API documentation

**Cons**:
- ❌ Regulatory restrictions in some countries
- ❌ Complex fee structure

**Best For**: High-volume trading, diverse altcoins

#### Bybit
**Pros**:
- ✅ Excellent futures trading
- ✅ User-friendly interface
- ✅ Good API performance
- ✅ Competitive fees

**Cons**:
- ❌ Limited spot trading pairs
- ❌ Smaller liquidity than Binance

**Best For**: Futures trading, derivatives

#### OKX
**Pros**:
- ✅ Global availability
- ✅ Good API performance
- ✅ Competitive fees
- ✅ Advanced features

**Cons**:
- ❌ Smaller user base
- ❌ Limited documentation

**Best For**: International traders, advanced features

---

## 3. API Key Setup Guide

### Binance Setup

#### Step 1: Create Account
1. Go to [binance.com](https://www.binance.com)
2. Complete registration and KYC
3. Enable 2FA (Google Authenticator recommended)

#### Step 2: Create API Key
1. **Navigate to API Management**
   ```
   Profile → API Management → Create API
   ```

2. **Configure API Key**
   ```
   Label: QuantumForge Trading Bot
   API Key Type: System-generated
   ```

3. **Set Permissions**
   ```
   ✅ Enable Reading
   ✅ Enable Spot & Margin Trading
   ✅ Enable Futures Trading
   ❌ Disable Withdrawals (CRITICAL for security)
   ```

4. **IP Restrictions (Recommended)**
   ```
   Add QuantumForge server IPs:
   - 52.15.123.45
   - 52.15.123.46
   ```

5. **Save Your Keys**
   ```
   API Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Secret Key: yyyyyyyyyyyyyyyyyyyyyyyyy
   ```

#### Step 3: Testnet Setup (Optional but Recommended)
1. Go to [testnet.binance.vision](https://testnet.binance.vision)
2. Create testnet account
3. Get testnet API keys
4. Use testnet keys for initial testing

### Bybit Setup

#### Step 1: Create Account
1. Go to [bybit.com](https://www.bybit.com)
2. Complete registration and verification
3. Enable 2FA

#### Step 2: Create API Key
1. **Navigate to API Management**
   ```
   Account & Security → API → Create New Key
   ```

2. **Configure API Key**
   ```
   Key Name: QuantumForge Bot
   Key Type: System-generated API Keys
   ```

3. **Set Permissions**
   ```
   ✅ Read-Write
   ✅ Contract Trading
   ✅ Spot Trading
   ❌ Asset Transfer
   ❌ Withdrawal
   ```

4. **IP Restrictions**
   ```
   Add allowed IPs:
   - 52.15.123.45
   - 52.15.123.46
   ```

5. **Save Keys**
   ```
   API Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Secret Key: yyyyyyyyyyyyyyyyyyyyyyyyy
   ```

### OKX Setup

#### Step 1: Create Account
1. Go to [okx.com](https://www.okx.com)
2. Complete registration and KYC
3. Enable 2FA

#### Step 2: Create API Key
1. **Navigate to API Management**
   ```
   Account → API → Create API Key
   ```

2. **Configure API Key**
   ```
   API Key Name: QuantumForge
   Passphrase: [Create strong passphrase]
   ```

3. **Set Permissions**
   ```
   ✅ Read
   ✅ Trade
   ❌ Withdraw
   ```

4. **IP Restrictions**
   ```
   Add allowed IPs:
   - 52.15.123.45
   - 52.15.123.46
   ```

5. **Save Keys**
   ```
   API Key: xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   Secret Key: yyyyyyyyyyyyyyyyyyyyyyyyy
   Passphrase: your_passphrase_here
   ```

---

## 4. Adding Keys to QuantumForge

### Via Web Interface

#### Step 1: Navigate to Settings
```
Studio → Settings → Exchange API Credentials
```

#### Step 2: Add New Credential
1. Click **"Add New Credential"**
2. Fill in the form:

```
Exchange: [Select from dropdown]
├─ Binance
├─ Bybit
├─ OKX
└─ KuCoin

Trading Mode: [Select trading type]
├─ Spot Trading
├─ Futures Trading
└─ Both

Environment: [Select environment]
├─ Testnet (Recommended for beginners)
└─ Mainnet (Live trading)

API Key: [Paste your API key]
Secret Key: [Paste your secret key]
Passphrase: [Only for OKX]

Label: [Give it a name]
├─ "Binance Testnet"
├─ "Bybit Mainnet"
└─ "OKX Futures"
```

#### Step 3: Test Connection
1. Click **"Test Connection"**
2. Wait for verification
3. ✅ **Success**: "Connection successful!"
4. ❌ **Error**: Check keys and permissions

#### Step 4: Save Configuration
1. Click **"Save & Continue"**
2. Your API keys are now configured
3. You can use them for backtesting and live trading

### Via API (Advanced)

```python
import requests

# Add exchange credentials
response = requests.post(
    "https://quantumforge.cryptomancer.ai/api/settings/exchange-credentials",
    headers={"Authorization": f"Bearer {YOUR_API_TOKEN}"},
    json={
        "exchange": "BINANCE",
        "trading_mode": "FUTURES",
        "environment": "TESTNET",
        "api_key": "your_binance_api_key",
        "api_secret": "your_binance_secret_key",
        "label": "Binance Testnet"
    }
)

print(response.json())
# {"success": true, "message": "Credentials saved successfully"}
```

---

## 5. Security Best Practices

### 🔒 Key Security Rules

#### Never Share Your Secret Keys
```
❌ Don't share in chat, email, or forums
❌ Don't commit to version control
❌ Don't store in plain text files
✅ Use environment variables
✅ Use secure password managers
```

#### Enable IP Restrictions
```
✅ Whitelist only QuantumForge IPs
✅ Use VPN if needed
❌ Don't use 0.0.0.0/0 (allows all IPs)
```

#### Disable Withdrawals
```
✅ Always disable withdrawal permissions
✅ Use separate trading accounts
✅ Keep main funds in cold storage
```

#### Regular Key Rotation
```
✅ Rotate keys every 3-6 months
✅ Monitor for suspicious activity
✅ Use different keys for testnet/mainnet
```

### 🛡️ Advanced Security

#### Multi-Account Strategy
```
Account 1: Main trading (large funds)
├─ Limited API permissions
├─ IP restrictions
└─ Regular monitoring

Account 2: Bot trading (small funds)
├─ Full trading permissions
├─ QuantumForge IP whitelist
└─ Automated monitoring
```

#### Monitoring & Alerts
```
✅ Set up balance alerts
✅ Monitor API usage
✅ Check for unauthorized access
✅ Regular security audits
```

---

## 6. Troubleshooting

### Common Issues

#### "Invalid API Key"
```
Possible Causes:
- Key copied incorrectly (extra spaces)
- Key doesn't have required permissions
- IP not whitelisted
- Key expired or revoked

Solutions:
1. Re-copy key (no spaces)
2. Check permissions in exchange
3. Add QuantumForge IPs
4. Generate new key if needed
```

#### "Connection Timeout"
```
Possible Causes:
- Network issues
- Exchange maintenance
- Rate limiting
- Firewall blocking

Solutions:
1. Check internet connection
2. Wait for maintenance to end
3. Reduce API call frequency
4. Check firewall settings
```

#### "Insufficient Permissions"
```
Possible Causes:
- API key lacks trading permissions
- Account not verified
- Regional restrictions

Solutions:
1. Enable trading permissions
2. Complete KYC verification
3. Use VPN if needed
4. Contact exchange support
```

### Testing Your Setup

#### Step 1: Test Connection
```
Studio → Settings → Exchange API Credentials
Click "Test Connection" for each credential
```

#### Step 2: Test Data Access
```
Create a simple bot that:
1. Fetches current price
2. Gets account balance
3. Lists available trading pairs
```

#### Step 3: Test Trading (Testnet Only)
```
1. Use testnet keys
2. Place small test orders
3. Verify order execution
4. Check order history
```

---

## 🎯 Next Steps

Now that your exchange API keys are configured:

**Continue to**: [Backtesting Guide →](./09-backtesting.md)

**Or**: [Bot Configuration →](./03-bot-configuration.md)

---

## 🆘 Need Help?

### Getting Support

- 📧 **Email**: support@quantumforge.ai
- 💬 **Discord**: [Community Server](https://discord.gg/quantumforge)
- 📖 **Documentation**: [Full API Reference](https://docs.quantumforge.ai)

### Exchange Support

- **Binance**: [Support Center](https://www.binance.com/en/support)
- **Bybit**: [Help Center](https://www.bybit.com/en/help)
- **OKX**: [Support Center](https://www.okx.com/support)

---

**Ready to start backtesting?** → [Next: Backtesting Guide](./09-backtesting.md)
