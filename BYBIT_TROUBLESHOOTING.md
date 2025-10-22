# 🔧 Bybit "Order Price Higher Than Maximum" - Deep Troubleshooting

## 📊 **Error Details**

**Time**: 2025-10-22 16:46:33  
**User**: Developer user 25 (telegram_chat_id=1592582978)  
**Symbol**: BTCUSDT  
**Quantity**: 0.001 BTC  
**Entry Price**: $332,685.60  
**Leverage**: 5x  
**Network**: TESTNET

```
ERROR: Bybit API error: Failed to submit order(s). 
The order price is higher than the maximum buying price.
```

---

## 🔍 **Investigation Timeline**

### **Attempt 1: Remove `timeInForce` + Add `marketUnit`** ❌
```python
params = {
    'category': 'linear',
    'symbol': 'BTCUSDT',
    'side': 'Buy',
    'orderType': 'Market',
    'qty': '0.001',
    'marketUnit': 'baseCoin'  # ❌ Still caused error
}
```
**Result**: FAILED - Same error persisted

### **Attempt 2: Minimal Parameters (Current)** ⏳
```python
params = {
    'category': 'linear',
    'symbol': 'BTCUSDT',
    'side': 'Buy',
    'orderType': 'Market',
    'qty': '0.001'
    # NO timeInForce, NO marketUnit
}
```
**Status**: Testing with enhanced logging

---

## 🤔 **Possible Root Causes**

### **1. API Key Permissions** 🔑
**Likelihood**: ⭐⭐⭐⭐⭐ (VERY HIGH)

**Symptoms**:
- Market orders fail with "price validation" error
- Even minimal params cause the same error
- Error message doesn't make sense for market orders (no price sent)

**Potential Issues**:
- ❌ API key lacks "Contract Trading" permission
- ❌ API key restricted to "Read-Only" mode
- ❌ API key IP whitelist doesn't include server IP
- ❌ API key created for SPOT trading, not FUTURES

**How to Check**:
```sql
-- Get user's Bybit credentials
SELECT 
    id,
    user_id,
    exchange,
    credential_type,
    is_testnet,
    is_active,
    created_at
FROM exchange_credentials
WHERE user_id = 25 AND exchange = 'BYBIT';
```

**Bybit Dashboard Check**:
1. Go to: https://testnet.bybit.com/app/user/api-management
2. Find the API key being used
3. Check permissions:
   - ✅ **Must have**: "Contract Trading" or "Derivatives Trading"
   - ✅ **Must have**: "Trade" permission (not just Read)
   - ✅ **IP Restriction**: Either disabled or includes server IP

### **2. Account Verification Level** 📋
**Likelihood**: ⭐⭐⭐ (MEDIUM-HIGH)

**Potential Issues**:
- Testnet account not properly set up
- Account KYC level too low
- Account has trading restrictions

**How to Check**:
- Login to Bybit Testnet
- Check account status
- Verify "Derivatives Trading" is enabled

### **3. Symbol Trading Restrictions** 🚫
**Likelihood**: ⭐⭐ (LOW-MEDIUM)

**Potential Issues**:
- BTCUSDT might have special restrictions on testnet
- Symbol might be temporarily disabled
- Order size too small/large

**How to Check**:
```python
# Test with Bybit API
GET /v5/market/instruments-info?category=linear&symbol=BTCUSDT
```

### **4. Testnet Quirks** 🧪
**Likelihood**: ⭐⭐⭐⭐ (HIGH)

**Known Issues**:
- Testnet has different rules than mainnet
- Some market orders may not work on testnet
- Testnet may require limit orders instead

**Test**: Try with a different exchange (Binance) to see if issue is Bybit-specific

### **5. Price Validation Bug** 🐛
**Likelihood**: ⭐⭐ (LOW)

**Theory**: Bybit API might be:
- Applying limit order logic to market orders
- Using stale price data
- Having internal calculation errors

---

## 🔬 **Enhanced Diagnostics Added**

### **New Logging**:
```python
logger.error(f"❌ Bybit API Error:")
logger.error(f"   Code: {error_code}")
logger.error(f"   Message: {error_msg}")
logger.error(f"   Full Response: {data}")
logger.error(f"   Request Params: {params}")
```

### **What to Look For in Next Error**:
1. **Error Code**: `retCode` value (e.g., 10001, 10004, etc.)
2. **Full Response**: May contain additional hints
3. **Rate Limit Info**: Check if hitting API limits

---

## 📋 **Immediate Action Items**

### ✅ **Step 1: Verify API Key Permissions** (CRITICAL)
```bash
# Get API key from database
SELECT api_key, api_secret, is_testnet 
FROM exchange_credentials 
WHERE user_id = 25 AND exchange = 'BYBIT';

# Check in Bybit Dashboard:
https://testnet.bybit.com/app/user/api-management
```

**Required Permissions**:
- ✅ Contract Trading (or Derivatives)
- ✅ Trade permission enabled
- ✅ IP whitelist: Either OFF or includes server IP

### ✅ **Step 2: Monitor Next Error with Enhanced Logging**
```bash
tail -f celery_worker.log | grep -A 10 "Bybit API Error"
```

Look for:
- **retCode**: Error code number
- **Full Response**: Complete API response
- **Additional fields**: May reveal restrictions

### ✅ **Step 3: Test with Limit Order (Workaround)**
If market orders continue failing, try limit order:
```python
params = {
    'category': 'linear',
    'symbol': 'BTCUSDT',
    'side': 'Buy',
    'orderType': 'Limit',
    'qty': '0.001',
    'price': str(current_price),  # Set to current market price
    'timeInForce': 'IOC'  # Immediate-Or-Cancel (like market order)
}
```

### ✅ **Step 4: Try Different Symbol**
Test with ETHUSDT instead of BTCUSDT:
```python
symbol = 'ETHUSDT'
```

### ✅ **Step 5: Compare with Binance**
If bot works fine with Binance but fails with Bybit → API key issue

---

## 🔄 **Alternative Solutions**

### **Option A: Use Limit Orders as Market Orders**
```python
# Get current price
current_price = client.get_current_price(symbol)

# Place limit order at market price with IOC
params = {
    'orderType': 'Limit',
    'price': current_price,
    'timeInForce': 'IOC'  # Executes immediately or cancels
}
```

### **Option B: Use Different Account Type**
- Switch from "Unified Trading Account" to "Classic Account"
- Some Bybit features work differently on different account types

### **Option C: Contact Bybit Support**
If all else fails:
- Email: support@bybit.com
- Telegram: @Bybit_HelpDesk
- Provide: API error code, request params, full error response

---

## 📊 **Expected Next Steps**

1. **Immediate**: Check API key permissions in Bybit dashboard
2. **Monitor**: Next bot execution will show enhanced error details
3. **Analyze**: Use error code to identify specific issue
4. **Fix**: Apply appropriate solution based on root cause

---

## 🎯 **Most Likely Diagnosis**

Based on symptoms, **API Key Permissions** is the most likely issue:

**Evidence**:
- ✅ Error persists with multiple parameter combinations
- ✅ Error message doesn't match the actual problem (no price sent)
- ✅ Bybit is known for strict API permission requirements
- ✅ Testnet API keys often have default restrictions

**Recommended Action**:
1. **Check API key permissions RIGHT NOW**
2. **Regenerate API key if needed**
3. **Ensure "Contract Trading" permission is enabled**

---

## 📝 **Update Log**

- **17:28**: Removed `marketUnit`, added enhanced logging
- **16:47**: Removed `timeInForce`, added `marketUnit='baseCoin'` - FAILED
- **15:49**: Initial fix attempt - FAILED
- **Next**: Waiting for enhanced error logs from next execution

---

**Status**: 🔬 **INVESTIGATING - Enhanced Logging Active**

**Next Update**: After next bot execution with full API response details

