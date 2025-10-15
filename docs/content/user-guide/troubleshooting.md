# 🔧 Troubleshooting Guide

Quick solutions to common problems on QuantumForge platform.

## 📋 Quick Links

- [Account & Login Issues](#account-and-login)
- [Bot Creation Problems](#bot-creation)
- [Trading Errors](#trading-errors)
- [Exchange Connection Issues](#exchange-connection)
- [LLM Integration Problems](#llm-integration)
- [Performance Issues](#performance-issues)
- [Payment & Subscription](#payment-and-subscription)

---

## Account & Login

### Cannot Log In

**Symptoms:**
- "Invalid credentials" error
- "Account not found"
- Login button not responding

**Solutions:**

1. **Check credentials:**
   ```
   - Email correct? (check for typos)
   - Password correct? (case-sensitive)
   - Caps Lock on?
   ```

2. **Reset password:**
   ```
   1. Click "Forgot Password"
   2. Check email (including spam folder)
   3. Click reset link
   4. Create new password
   ```

3. **Clear browser cache:**
   ```
   Chrome: Ctrl+Shift+Delete
   Firefox: Ctrl+Shift+Delete
   Safari: Cmd+Option+E
   ```

4. **Try different browser:**
   - Chrome
   - Firefox
   - Safari
   - Edge

5. **Check if account is verified:**
   ```
   - Check email for verification link
   - Resend verification email
   - Contact support if no email received
   ```

---

### Email Verification Link Expired

**Solution:**

1. Go to login page
2. Click **"Resend Verification"**
3. Check email (spam folder too)
4. Click new link within 24 hours

**Still not working?**
```bash
Email: support@quantumforge.ai
Subject: "Cannot verify email: your@email.com"
```

---

### Two-Factor Authentication (2FA) Issues

**Lost 2FA device:**

1. Click **"Lost 2FA device"** on login
2. Enter recovery codes (saved during setup)
3. Disable 2FA
4. Re-enable with new device

**No recovery codes:**
```
Contact support with:
- Account email
- Photo ID
- Last successful login date
```

---

## Bot Creation

### "Bot creation failed" Error

**Common causes & solutions:**

1. **Invalid configuration:**
   ```python
   # Check:
   - All required fields filled?
   - Valid trading pair? (e.g., BTC/USDT)
   - Timeframe supported? (1m, 5m, 15m, 1h, 4h, 1d)
   - Exchange selected?
   ```

2. **Missing exchange credentials:**
   ```
   Solution:
   1. Go to Settings → Exchange API Credentials
   2. Add credentials for selected exchange
   3. Test connection
   4. Try creating bot again
   ```

3. **Invalid strategy config:**
   ```python
   # Example error:
   "rsi_period": "fourteen"  ❌ (should be number)
   "rsi_period": 14  ✅
   
   # Fix:
   - Use numbers, not strings
   - Check JSON syntax
   - Validate all parameters
   ```

---

### Cannot Upload ML Model

**File size too large:**
```
Max file size: 100MB

Solution:
1. Compress model:
   import joblib
   joblib.dump(model, 'model.pkl', compress=3)

2. Or use model quantization
3. Or host model externally
```

**Unsupported format:**
```
Supported:
- .pkl (scikit-learn, pickled models)
- .h5 (Keras/TensorFlow)
- .pt (PyTorch)
- .onnx (ONNX format)

Solution: Convert model to supported format
```

---

### Backtest Returns No Results

**Causes:**

1. **Date range issues:**
   ```python
   ❌ start_date > end_date
   ❌ start_date in future
   ❌ Date range too short (<7 days)
   
   ✅ start_date: "2024-01-01"
   ✅ end_date: "2024-10-01"
   ```

2. **No trades generated:**
   ```
   Reasons:
   - Entry conditions too strict
   - Insufficient data for pair/timeframe
   - Strategy filters all signals
   
   Solution:
   - Relax entry conditions
   - Try different pair/timeframe
   - Check strategy logic
   ```

3. **Exchange data unavailable:**
   ```
   Some pairs don't have full history
   
   Solution:
   - Try major pairs (BTC/USDT, ETH/USDT)
   - Reduce backtest period
   - Check exchange data availability
   ```

---

## Trading Errors

### "Insufficient Balance" Error

**Check:**
```
1. Actual exchange balance:
   - Log into exchange
   - Check available balance
   - Account for open orders

2. Bot configuration:
   - Position size too large?
   - Using all capital (100%)?
   - Reserve some for fees

3. Spot vs Margin:
   - Spot bot needs spot balance
   - Futures bot needs futures balance
```

**Solution:**
```python
# Reduce position size
{
  "position_percent": 80  # Use 80%, not 100%
}

# Or deposit more funds
```

---

### Orders Not Filling

**Symptoms:**
- Order placed but never executed
- Order cancelled after timeout
- "Order timeout" in logs

**Causes & Solutions:**

1. **Limit order too aggressive:**
   ```python
   # If using LIMIT orders:
   {
     "order_type": "LIMIT",
     "limit_offset_percent": 0.5  # Too far from market
   }
   
   # Solution: Reduce offset or use MARKET
   {
     "limit_offset_percent": 0.1  # Closer to market
     # or
     "order_type": "MARKET"  # Guaranteed fill
   }
   ```

2. **Low liquidity pair:**
   ```
   Problem: Trading pair has low volume
   
   Solution:
   - Trade major pairs (BTC, ETH, BNB)
   - Use MARKET orders
   - Increase order timeout
   ```

3. **Exchange issues:**
   ```
   Check:
   - Exchange under maintenance?
   - API limits reached?
   - Trading suspended for pair?
   ```

---

### Bot Stopped Trading

**Check Bot Status:**
```
My Bots → [Your Bot] → Status

If status is PAUSED or STOPPED:
- Click "Resume" or "Start"
- Check why it stopped (logs)
```

**Common Reasons:**

1. **Daily loss limit hit:**
   ```
   Solution:
   - Wait until next day (auto-reset)
   - Or increase daily loss limit
   - Or manually reset (if confident)
   ```

2. **Exchange credentials invalid:**
   ```
   Solution:
   1. Settings → Exchange Credentials
   2. Test connection
   3. Re-enter API keys if failed
   4. Check API key permissions
   ```

3. **Risk limits exceeded:**
   ```
   Check:
   - Max positions reached?
   - Total exposure exceeded?
   - Drawdown limit hit?
   
   Solution: Adjust limits or close positions
   ```

---

## Exchange Connection

### "Invalid API Keys" Error

**Step-by-step fix:**

1. **Verify keys are correct:**
   ```
   - Copy-paste carefully (no extra spaces)
   - Check both API Key and Secret Key
   - Ensure not using wrong exchange keys
   ```

2. **Check API permissions:**
   ```
   Required permissions:
   ✅ Read
   ✅ Spot/Margin Trading (for SPOT bots)
   ✅ Futures Trading (for FUTURES bots)
   ❌ Withdrawal (NOT needed, don't enable!)
   ```

3. **Test on exchange directly:**
   ```
   Use Postman or curl to test:
   
   curl -X GET "https://api.binance.com/api/v3/account" \
     -H "X-MBX-APIKEY: your_api_key"
   
   If this fails, issue is with exchange, not QuantumForge
   ```

4. **Check IP whitelist:**
   ```
   If you enabled IP whitelist on exchange:
   - Add QuantumForge IPs (provided in Settings)
   - Or disable IP whitelist
   ```

5. **Regenerate keys:**
   ```
   Last resort:
   1. Go to exchange
   2. Delete old API key
   3. Create new API key
   4. Update in QuantumForge
   ```

---

### "Insufficient Permissions" Error

**Fix API Permissions:**

**Binance:**
```
1. Log into Binance
2. Profile → API Management
3. Click Edit on your API key
4. Enable:
   ✅ Enable Reading
   ✅ Enable Spot & Margin Trading
   ✅ Enable Futures (if using futures bot)
5. Save
```

**Bybit:**
```
1. Log into Bybit
2. API Management
3. Edit permissions:
   ✅ Read-Write
   ✅ Contract Trading
   ✅ Spot Trading
4. Save
```

---

### Exchange Rate Limit Errors

**Symptoms:**
- "429 Too Many Requests"
- "Rate limit exceeded"
- Orders failing intermittently

**Solutions:**

1. **Reduce check frequency:**
   ```python
   {
     "check_interval": 60  # Check every 60 seconds, not 10
   }
   ```

2. **Optimize API calls:**
   ```python
   {
     "batch_requests": true,  # Batch multiple calls
     "cache_duration": 30     # Cache data for 30 seconds
   }
   ```

3. **Wait and retry:**
   ```
   Rate limits reset after:
   - Binance: 1 minute
   - Bybit: 1-5 minutes
   - OKX: 2 seconds
   ```

---

## LLM Integration

### "LLM Provider Authentication Failed"

**Causes:**

1. **Invalid API key:**
   ```
   OpenAI: Starts with "sk-"
   Anthropic: Starts with "sk-ant-"
   Google: Starts with "AI..."
   
   Solution: Copy full key, no spaces
   ```

2. **Expired or revoked key:**
   ```
   Check on provider dashboard:
   - OpenAI: platform.openai.com/api-keys
   - Anthropic: console.anthropic.com
   - Google: makersuite.google.com
   ```

3. **Insufficient credits:**
   ```
   Check billing:
   - OpenAI: Add payment method
   - Anthropic: Top up account
   - Groq: Free tier has limits
   ```

---

### LLM Responses Are Inconsistent

**Problem:** AI giving different answers for same input

**Solutions:**

1. **Lower temperature:**
   ```python
   {
     "temperature": 0.1  # More consistent (was 0.7)
   }
   ```

2. **More specific prompt:**
   ```markdown
   ❌ Vague:
   "Analyze the market"
   
   ✅ Specific:
   "Analyze BTC/USDT. If RSI < 30 AND price > EMA200, 
   output {\"signal\": \"BUY\"}. Otherwise, {\"signal\": \"HOLD\"}"
   ```

3. **Add examples (few-shot):**
   ```markdown
   Example 1:
   Input: RSI 28, Price above EMA
   Output: {"signal": "BUY"}
   
   Example 2:
   Input: RSI 75, Price below EMA
   Output: {"signal": "SELL"}
   
   Now analyze current data...
   ```

---

### "LLM Token Limit Exceeded"

**Error:** Request exceeds model's token limit

**Solutions:**

1. **Reduce prompt size:**
   ```python
   ❌ Too long:
   Send entire 1000-line news article
   
   ✅ Optimized:
   Send top 5 headlines (200 words)
   ```

2. **Use model with larger context:**
   ```python
   GPT-3.5: 16k tokens
   GPT-4: 8k → 128k tokens
   Claude 3: Up to 200k tokens
   Gemini 1.5: Up to 1M tokens
   ```

3. **Chunk data:**
   ```python
   Instead of one large request:
   - Split into smaller chunks
   - Process separately
   - Combine results
   ```

---

## Performance Issues

### Bot is Slow / Unresponsive

**Diagnostics:**

1. **Check server status:**
   ```
   https://status.quantumforge.ai
   ```

2. **Test internet connection:**
   ```bash
   ping api.quantumforge.ai
   ```

3. **Clear browser cache:**
   ```
   Ctrl+Shift+Delete (Chrome/Firefox)
   ```

4. **Check bot complexity:**
   ```
   Complex bots (many indicators, LLM calls) are slower
   
   Solution:
   - Simplify strategy
   - Reduce indicator count
   - Lower LLM call frequency
   ```

---

### High LLM Costs

**Symptoms:**
- Unexpectedly high billing
- Running out of credits quickly

**Cost Reduction:**

1. **Use cheaper models:**
   ```python
   ❌ Expensive:
   GPT-4: $0.03 per 1k tokens
   
   ✅ Affordable:
   GPT-3.5: $0.001 per 1k tokens
   Groq: FREE
   ```

2. **Reduce call frequency:**
   ```python
   ❌ Every 5 minutes = 288 calls/day
   ✅ Every 1 hour = 24 calls/day
   
   Savings: 91% fewer calls!
   ```

3. **Limit max tokens:**
   ```python
   {
     "max_tokens": 200  # Instead of 2000
   }
   ```

4. **Cache results:**
   ```python
   {
     "cache_llm_results": true,
     "cache_duration": 900  # 15 minutes
   }
   ```

---

## Payment & Subscription

### Payment Failed

**Credit Card Issues:**

1. **Check card details:**
   ```
   - Card number correct?
   - CVV correct?
   - Expiry date valid?
   - Billing address matches?
   ```

2. **Insufficient funds:**
   ```
   - Check card balance
   - Contact bank
   - Try different card
   ```

3. **Bank declining:**
   ```
   Common reasons:
   - International transaction blocked
   - Suspicious activity flag
   - Daily limit reached
   
   Solution: Call bank to authorize
   ```

**PayPal Issues:**

1. **PayPal account not verified:**
   ```
   Solution: Verify your PayPal account
   ```

2. **Payment authorization failed:**
   ```
   Solution:
   - Check PayPal balance
   - Link bank account
   - Try again
   ```

**ICP (Crypto) Issues:**

1. **Insufficient ICP balance:**
   ```
   Solution:
   - Buy more ICP
   - Transfer ICP to wallet
   ```

2. **Wallet not connected:**
   ```
   Solution:
   - Connect Plug/Stoic wallet
   - Authorize connection
   ```

---

### Subscription Not Activating

**After successful payment:**

1. **Wait 5 minutes** (blockchain confirmation)

2. **Refresh page:**
   ```
   F5 or Ctrl+R
   ```

3. **Check "Active Subscriptions":**
   ```
   Dashboard → Active Subscriptions
   ```

4. **Still not showing?**
   ```
   Contact support with:
   - Payment receipt/transaction ID
   - Bot name
   - Payment method
   - Account email
   ```

---

## 🆘 Still Having Issues?

### Contact Support

**Before contacting:**
- ✅ Check this guide
- ✅ Check [FAQ](./faq.md)
- ✅ Try basic troubleshooting
- ✅ Gather error messages/screenshots

**Contact Methods:**

📧 **Email:** support@quantumforge.ai
```
Include:
1. Account email
2. Bot name (if applicable)
3. Error message (screenshot)
4. Steps to reproduce
5. When it started happening
```

💬 **Discord:** [Community Support](https://discord.gg/quantumforge)
```
Fastest for:
- Quick questions
- Community help
- Real-time assistance
```

🐛 **Bug Report:** [GitHub Issues](https://github.com/quantumforge/issues)
```
For:
- Technical bugs
- Feature requests
- Documentation errors
```

### Response Times

- 🔴 Critical (bot stopped, money at risk): <2 hours
- 🟠 High (cannot trade): <12 hours
- 🟡 Medium (performance issue): <24 hours
- 🟢 Low (general question): <48 hours

---

## 📝 Error Code Reference

| Code | Meaning | Solution |
|------|---------|----------|
| **AUTH_001** | Invalid credentials | Check email/password |
| **AUTH_002** | Account not verified | Check verification email |
| **BOT_001** | Invalid configuration | Review bot settings |
| **BOT_002** | Insufficient balance | Deposit funds |
| **EXCH_001** | API key invalid | Re-enter API keys |
| **EXCH_002** | Rate limit exceeded | Wait 1-5 minutes |
| **LLM_001** | Provider auth failed | Check LLM API key |
| **LLM_002** | Token limit exceeded | Reduce prompt size |
| **PAY_001** | Payment failed | Check payment method |
| **PAY_002** | Insufficient funds | Add funds |

---

**Back to**: [User Guide Home](./README.md)

