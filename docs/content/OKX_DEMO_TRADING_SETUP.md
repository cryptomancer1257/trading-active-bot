# OKX Demo Trading Setup Guide

## 🎯 Overview
OKX uses **Demo Trading** mode instead of a separate testnet URL. The same API endpoint is used for both live and demo trading, differentiated by the `x-simulated-trading` header.

---

## 🔑 Creating OKX Demo Trading API Keys

### Step 1: Access Demo Trading
1. Go to [OKX Demo Trading](https://www.okx.com/trade-demo)
2. Log in to your OKX account
3. Click on **"Start Demo Trading"** (you'll get virtual funds)

### Step 2: Create API Key for Demo Trading
1. In Demo Trading mode, go to **API** section
2. Click **"Create API Key"**
3. **IMPORTANT:** Select **"Trading"** permission (NOT just "Read")
4. **CRITICAL:** Save these 3 values:
   - ✅ **API Key**
   - ✅ **Secret Key**
   - ✅ **Passphrase** (REQUIRED for OKX!)

⚠️ **OKX requires ALL 3 values to work!**

---

## 📝 Adding OKX Credentials to QuantumForge

### Via Web UI
1. Go to **"API Credentials"** page
2. Click **"Add Credentials"**
3. Fill in:
   ```
   Exchange: OKX
   Type: FUTURES
   Network: TESTNET (for Demo Trading)
   Name: OKX Demo Trading
   API Key: [Your API Key]
   API Secret: [Your Secret Key]
   Passphrase: [Your Passphrase] ← REQUIRED!
   ```

### Via Database (if needed)
```sql
INSERT INTO developer_exchange_credentials (
    user_id, 
    exchange_type, 
    credential_type, 
    network_type, 
    name, 
    api_key, 
    api_secret, 
    passphrase,  -- Required for OKX!
    is_active
) VALUES (
    7,
    'OKX',
    'FUTURES',
    'TESTNET',
    'OKX Demo Trading',
    '<encrypted_api_key>',
    '<encrypted_secret>',
    '<your_passphrase>',  -- Don't forget this!
    1
);
```

---

## 🔧 How OKX Demo Trading Works

### API Endpoints
```python
# Both testnet and mainnet use the same base URL
BASE_URL = "https://www.okx.com"

# Differentiation is via header
if testnet:
    headers["x-simulated-trading"] = "1"  # Demo Trading
else:
    # No special header for live trading
```

### Authentication Headers
```python
headers = {
    "OK-ACCESS-KEY": api_key,
    "OK-ACCESS-SIGN": signature,
    "OK-ACCESS-TIMESTAMP": timestamp,  # ISO8601 format
    "OK-ACCESS-PASSPHRASE": passphrase,  # REQUIRED!
    "x-simulated-trading": "1"  # For demo trading only
}
```

### Timestamp Format
OKX requires specific ISO8601 format:
```python
# ✅ CORRECT
timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
# Example: 2025-10-04T19:59:17.456Z

# ❌ WRONG
timestamp = datetime.utcnow().isoformat() + 'Z'
```

---

## 🐛 Troubleshooting

### Error: 401 Unauthorized

**Cause 1: Missing Passphrase**
```
❌ OKX HTTP 401: {"code":"50113","msg":"Invalid sign"}
```
**Fix:** Make sure passphrase is provided when creating credentials

**Cause 2: Wrong Timestamp Format**
```
❌ OKX HTTP 401: {"code":"50102","msg":"Timestamp request expired"}
```
**Fix:** Use correct ISO8601 format (see above)

**Cause 3: Wrong API Key Type**
```
❌ OKX HTTP 401: {"code":"50111","msg":"Invalid OK-ACCESS-KEY"}
```
**Fix:** Create API key in **Demo Trading** mode, not main account

**Cause 4: Insufficient Permissions**
```
❌ OKX API Error [50004]: Endpoint requires that APIKey has trading permission
```
**Fix:** Recreate API key with **Trading** permission enabled

---

### Error: Invalid Signature

**Symptoms:**
```
❌ OKX HTTP 401: {"code":"50113","msg":"Invalid sign"}
```

**Common Causes:**
1. Passphrase mismatch
2. Wrong secret key
3. Timestamp format issue
4. Request path mismatch in signature

**Debug Steps:**
```python
# Check signature generation
message = timestamp + method + request_path + body
print(f"Signature message: {message}")
print(f"Timestamp: {timestamp}")
print(f"Method: {method}")
print(f"Path: {request_path}")
print(f"Body: {body}")
```

---

## ✅ Verification Checklist

Before running OKX bot:
- [ ] Created API key in **Demo Trading** mode
- [ ] API key has **Trading** permission
- [ ] Saved all **3 values** (API Key + Secret + Passphrase)
- [ ] Added credentials with **Network = TESTNET**
- [ ] Passphrase field is **NOT empty**
- [ ] Demo Trading account has sufficient virtual balance

---

## 📊 Testing OKX Integration

### Test 1: Check Account Balance
```python
from services.exchange_integrations.okx_futures import OKXFuturesIntegration

client = OKXFuturesIntegration(
    api_key="your_api_key",
    api_secret="your_secret",
    passphrase="your_passphrase",  # Don't forget!
    testnet=True
)

account_info = client.get_account_info()
print(f"Balance: {account_info}")
```

**Expected Output:**
```
🔧 Initializing OKX Futures Integration - 🧪 DEMO TRADING
   API Key: abc12345***
   Passphrase: ✅ Provided
🔑 OKX DEMO TRADING API Request: GET /api/v5/account/balance
📥 OKX Response Status: 200
✅ OKX API Success: GET /api/v5/account/balance
Balance: {'totalEq': '10000', 'availBal': '10000', ...}
```

### Test 2: Get Ticker
```python
ticker = client.get_ticker("BTC-USDT-SWAP")
print(f"BTC Price: ${ticker['price']}")
```

---

## 🔗 Official Documentation

- [OKX Demo Trading](https://www.okx.com/trade-demo)
- [OKX API Documentation](https://www.okx.com/docs-v5/en/)
- [OKX Authentication](https://www.okx.com/docs-v5/en/#overview-authentication)
- [OKX Demo Trading Guide](https://www.okx.com/support/hc/en-us/articles/360045263011-Demo-trading)

---

## 🆚 OKX vs Other Exchanges

| Feature | OKX | Binance | Bybit |
|---------|-----|---------|-------|
| **Testnet URL** | Same as mainnet | Different URL | Different URL |
| **Testnet Flag** | `x-simulated-trading: 1` | URL-based | URL-based |
| **Passphrase** | ✅ Required | ❌ Not needed | ❌ Not needed |
| **API Key Location** | Demo Trading section | Testnet site | Testnet site |

---

## 🎯 Summary

**Key Differences for OKX:**
1. ✅ Use **same URL** for testnet and mainnet
2. ✅ Add `x-simulated-trading: 1` header for demo trading
3. ✅ **MUST provide passphrase** (3rd credential)
4. ✅ Create API keys in **Demo Trading** mode
5. ✅ Use specific ISO8601 timestamp format

**Most Common Mistake:**
❌ Forgetting to provide passphrase → 401 Unauthorized

---

*Last Updated: October 4, 2025*

