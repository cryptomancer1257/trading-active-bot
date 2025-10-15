# 💳 PayPal Integration Guide

## 🎯 Overview

This guide covers the complete PayPal integration for the AI Trading Bot Marketplace, enabling users to rent bots using PayPal accounts or credit/debit cards without requiring crypto knowledge.

## 🚀 Quick Start

### 1. Run the Setup Script
```bash
cd trade-bot-marketplace
./scripts/setup_paypal_integration.sh
```

### 2. Configure PayPal Credentials
Edit your `.env` file with PayPal sandbox credentials:
```bash
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_sandbox_client_secret
PAYPAL_WEBHOOK_SECRET=your_webhook_secret
```

### 3. Start the Server
```bash
uvicorn core.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test Integration
```bash
python scripts/test_paypal_integration.py
```

## 🏗️ Architecture

### Payment Flow
```
User → Select Bot → Choose PayPal → PayPal Login/Card → Approval → 
Backend → Create Rental → Activate Bot
```

### Components
- **Currency Service**: ICP/USD conversion with Redis caching
- **PayPal Service**: Payment creation, execution, webhooks
- **Database Models**: Payment tracking and audit
- **API Endpoints**: RESTful PayPal payment API
- **Background Tasks**: Asynchronous rental creation

## 📊 Database Schema

### PayPal Payments Table
```sql
CREATE TABLE paypal_payments (
    id VARCHAR(255) PRIMARY KEY,
    user_principal_id VARCHAR(255) NOT NULL,
    bot_id INT NOT NULL,
    amount_usd DECIMAL(10,2) NOT NULL,
    amount_icp_equivalent DECIMAL(18,8) NOT NULL,
    status ENUM('PENDING', 'COMPLETED', 'FAILED', ...) DEFAULT 'PENDING',
    paypal_order_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rental_id VARCHAR(255),
    -- ... additional fields
);
```

### Payment Status Flow
```
PENDING → APPROVED → COMPLETED → [Rental Created]
        ↓
      FAILED/CANCELLED
```

## 🔌 API Endpoints

### Create PayPal Order
```http
POST /payments/paypal/create-order
Content-Type: application/json

{
  "user_principal_id": "principal_id",
  "bot_id": 123,
  "duration_days": 30,
  "pricing_tier": "monthly"
}
```

**Response:**
```json
{
  "success": true,
  "payment_id": "paypal_abc123",
  "approval_url": "https://sandbox.paypal.com/cgi-bin/webscr?cmd=...",
  "amount_usd": 25.99,
  "expires_in_minutes": 60
}
```

### Execute Payment
```http
POST /payments/paypal/execute-payment
Content-Type: application/json

{
  "payment_id": "paypal_abc123",
  "payer_id": "PAYER123"
}
```

### Get Payment Status
```http
GET /payments/paypal/payment/{payment_id}
```

### Admin Endpoints
```http
GET /payments/paypal/payments/summary
GET /payments/paypal/payments/user/{user_principal_id}
POST /payments/paypal/retry-rental/{payment_id}
```

## 💰 Currency Conversion

### ICP/USD Rate Service
- **Source**: CoinGecko API
- **Caching**: Redis (5-minute TTL)
- **Fallback**: $10.00 default rate

### Pricing Calculation
```python
# Example: Bot costs 2.5 ICP/day for 30 days
icp_amount = 2.5 * 30  # 75 ICP
usd_rate = 10.50      # $10.50 per ICP
usd_amount = 75 * 10.50  # $787.50
```

### Tier Discounts
- **Daily**: No discount (1.0x)
- **Quarterly**: 15% discount (0.85x)
- **Yearly**: 30% discount (0.70x)

## 🔧 Configuration

### Environment Variables
```bash
# PayPal Configuration
PAYPAL_MODE=sandbox                 # sandbox or live
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_secret
PAYPAL_WEBHOOK_SECRET=webhook_secret

# Redis Configuration (for currency caching)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Application URLs
FRONTEND_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=bot_marketplace
```

### PayPal Sandbox Setup
1. Go to [PayPal Developer Console](https://developer.paypal.com/)
2. Create a new sandbox application
3. Get Client ID and Client Secret
4. Create webhook endpoint: `your_domain/payments/paypal/webhook`
5. Subscribe to events: `PAYMENT.SALE.COMPLETED`, `PAYMENT.SALE.DENIED`

## 🎨 Frontend Integration

### Payment Method Selector
```typescript
const paymentMethods = [
  { id: 'ICP', name: 'ICP Token', icon: '🌐' },
  { id: 'BOT', name: 'BOT Token', icon: '🤖' },
  { id: 'PAYPAL', name: 'PayPal & Cards', icon: '💳' }
];
```

### PayPal Payment Flow
```typescript
// 1. Create PayPal order
const response = await fetch('/payments/paypal/create-order', {
  method: 'POST',
  body: JSON.stringify(orderData)
});

const { approval_url, payment_id } = await response.json();

// 2. Redirect to PayPal
window.location.href = approval_url;

// 3. Handle return (success page)
const executeResponse = await fetch('/payments/paypal/execute-payment', {
  method: 'POST',
  body: JSON.stringify({ payment_id, payer_id })
});
```

### User Experience
- **PayPal Users**: Login with PayPal account
- **Guest Users**: Pay with credit/debit card directly
- **No Account Required**: Full guest checkout support

## 🔍 Testing

### Test Payment Creation
```bash
curl -X POST http://localhost:8000/payments/paypal/create-order \
  -H "Content-Type: application/json" \
  -d '{
    "user_principal_id": "test_principal",
    "bot_id": 1,
    "duration_days": 1,
    "pricing_tier": "daily"
  }'
```

### Test Currency Service
```bash
curl http://localhost:8000/payments/paypal/currency-rate
```

### Integration Test Script
```bash
python scripts/test_paypal_integration.py
```

## 🛠️ Troubleshooting

### Common Issues

#### 1. PayPal Order Creation Failed
**Error**: `PayPal order creation failed`
**Solution**: 
- Check PayPal credentials in `.env`
- Verify sandbox vs live mode
- Check network connectivity

#### 2. Currency Rate Fetch Failed
**Error**: `Currency rate fetch failed`
**Solution**:
- Check internet connectivity
- Verify Redis is running
- Check CoinGecko API status

#### 3. Database Migration Failed
**Error**: `Migration failed`
**Solution**:
- Verify database credentials
- Check MySQL is running
- Review migration script output

#### 4. Redis Connection Failed
**Error**: `Redis connection failed`
**Solution**:
- Start Redis: `redis-server`
- Check Redis configuration
- Use fallback without caching

### Debug Mode
Enable detailed logging:
```bash
export LOG_LEVEL=DEBUG
uvicorn core.main:app --reload --log-level debug
```

### Check Database Tables
```sql
-- Verify PayPal tables exist
SHOW TABLES LIKE 'paypal_%';

-- Check payment records
SELECT * FROM paypal_payments ORDER BY created_at DESC LIMIT 5;

-- View payment summary
SELECT * FROM paypal_payment_summary;
```

## 📊 Monitoring & Analytics

### Payment Metrics
- **Conversion Rate**: PayPal vs Crypto payments
- **Success Rate**: Completed vs Failed payments
- **Average Amount**: USD payment amounts
- **Geographic Distribution**: Payment locations

### Database Queries
```sql
-- Payment status distribution
SELECT status, COUNT(*) as count 
FROM paypal_payments 
GROUP BY status;

-- Daily payment volume
SELECT DATE(created_at) as date, 
       COUNT(*) as payments,
       SUM(amount_usd) as volume_usd
FROM paypal_payments 
WHERE status = 'COMPLETED'
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- Top bots by PayPal payments
SELECT b.name, COUNT(*) as paypal_payments
FROM paypal_payments pp
JOIN bots b ON pp.bot_id = b.id
WHERE pp.status = 'COMPLETED'
GROUP BY b.id, b.name
ORDER BY paypal_payments DESC;
```

## 🔒 Security Considerations

### Webhook Security
- ✅ Signature verification implemented
- ✅ HTTPS required for production
- ✅ Event deduplication
- ✅ Error handling and logging

### Data Protection
- ✅ PCI DSS compliance (PayPal handles card data)
- ✅ Encrypted database connections
- ✅ No card data stored locally
- ✅ GDPR compliance for EU users

### Access Control
- ✅ Admin endpoints protected
- ✅ User principal validation
- ✅ Payment ownership verification
- ✅ Rate limiting on payment creation

## 🚀 Production Deployment

### Environment Setup
1. **PayPal Live Credentials**
   ```bash
   PAYPAL_MODE=live
   PAYPAL_CLIENT_ID=live_client_id
   PAYPAL_CLIENT_SECRET=live_client_secret
   ```

2. **Redis Production**
   ```bash
   REDIS_HOST=your_redis_host
   REDIS_PASSWORD=your_redis_password
   ```

3. **Database Production**
   ```bash
   DB_HOST=your_db_host
   DB_SSL_MODE=required
   ```

### Monitoring Setup
- **Health Checks**: `/health` endpoint
- **Metrics**: Prometheus/Grafana
- **Logging**: Structured JSON logs
- **Alerts**: Payment failure notifications

### Backup Strategy
- **Database**: Daily automated backups
- **Configuration**: Version controlled
- **Monitoring**: Backup verification

## 📈 Performance Optimization

### Caching Strategy
- **Currency Rates**: Redis (5-minute TTL)
- **Bot Data**: Application cache
- **Payment Status**: Real-time updates

### Database Optimization
- **Indexes**: Payment status, user principal, dates
- **Partitioning**: By creation date
- **Archiving**: Old completed payments

### API Performance
- **Async Processing**: Background rental creation
- **Connection Pooling**: Database connections
- **Rate Limiting**: Payment endpoint protection

## 🔄 Migration & Rollback

### Migration Process
1. **Backup**: Automated database backup
2. **Apply**: Run migration script
3. **Verify**: Check table creation
4. **Test**: Run integration tests

### Rollback Procedure
```bash
# Restore from backup if needed
mysql -u root -p bot_marketplace < backup_file.sql

# Check rollback success
python scripts/test_paypal_integration.py
```

## 📚 Additional Resources

### PayPal Documentation
- [PayPal REST API](https://developer.paypal.com/docs/api/overview/)
- [Webhook Events](https://developer.paypal.com/docs/api/webhooks/)
- [Testing Guide](https://developer.paypal.com/docs/api/sandbox/)

### Internal Documentation
- `api/endpoints/paypal_payments.py` - API implementation
- `services/paypal_service.py` - Core PayPal logic
- `services/currency_service.py` - Currency conversion
- `migrations/versions/011_paypal_integration.sql` - Database schema

---

## 🎉 Success!

Your PayPal integration is now complete and ready for production use! Users can now rent bots using:

- ✅ **PayPal Account** - Familiar login flow
- ✅ **Credit Cards** - Guest checkout (Visa, MasterCard, etc.)
- ✅ **Debit Cards** - Direct payment
- ✅ **No Crypto Required** - Traditional payment methods

**Questions?** Check the troubleshooting section or review the test scripts for examples.
