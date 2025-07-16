# Email Notification Configuration

## 📧 Email Settings

To enable email notifications for bot activities, configure the following environment variables:

### Required Environment Variables:

```bash
# Gmail Configuration (recommended)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password, not regular password
FROM_EMAIL=noreply@botmarketplace.com
FROM_NAME=Bot Marketplace

# Alternative: Outlook/Hotmail
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password

# Alternative: Yahoo
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USERNAME=your-email@yahoo.com
SMTP_PASSWORD=your-password
```

## 🔐 Gmail App Password Setup

1. Go to your Google Account settings
2. Navigate to Security → 2-Step Verification
3. Select App passwords
4. Generate a new app password for "Bot Marketplace"
5. Use this app password (not your regular Gmail password)

## 📝 Email Templates

Email templates are stored in `email_templates/` directory:
- `trade_notification.html` - HTML template for trade alerts
- `trade_notification.txt` - Text template for trade alerts  
- `signal_notification.html` - HTML template for signal alerts
- `signal_notification.txt` - Text template for signal alerts

## 🚀 Usage Examples

### In Bot Code:
```python
from email_tasks import notify_trade_async, notify_signal_async, notify_error_async

# Send trade notification
notify_trade_async(
    user_email="user@example.com",
    subscription_id=123,
    bot_name="Golden Cross Bot",
    trade_data={
        "side": "BUY",
        "symbol": "BTC/USDT",
        "quantity": "0.001",
        "price": "45000.00",
        "type": "MARKET"
    },
    is_testnet=True
)

# Send signal notification  
notify_signal_async(
    user_email="user@example.com",
    subscription_id=123,
    bot_name="RSI Bot",
    signal_data={
        "signal_type": "BUY",
        "symbol": "BTC/USDT",
        "current_price": "45000.00",
        "confidence": "85",
        "message": "RSI indicates oversold condition"
    },
    is_testnet=True
)

# Send error notification
notify_error_async(
    user_email="user@example.com",
    subscription_id=123,
    bot_name="MACD Bot",
    error_data={
        "error_type": "API_ERROR",
        "message": "Failed to connect to exchange",
        "details": "Connection timeout after 30 seconds"
    },
    is_testnet=True
)
```

## 🔧 Testing Email Setup

Test email configuration:
```python
from email_service import email_service

# Test basic email sending
success = email_service.send_email(
    to_email="test@example.com",
    subject="Test Email",
    html_body="<h1>Test Email</h1><p>This is a test email.</p>",
    text_body="Test Email\n\nThis is a test email."
)

print(f"Email sent successfully: {success}")
```

## 🚨 Production Considerations

- Use dedicated email service (SendGrid, AWS SES, etc.) for production
- Implement email rate limiting to avoid spam
- Add unsubscribe functionality
- Use email queues for high-volume notifications
- Monitor email delivery rates and bounces

## 🎯 Notification Types

1. **Trade Notifications**: Sent when bot executes trades
2. **Signal Notifications**: Sent when bot generates trading signals
3. **Error Notifications**: Sent when bot encounters errors
4. **Performance Summaries**: Daily/weekly performance reports
5. **Trial Expiry Notifications**: When trial subscriptions are about to expire

## 📊 Email Analytics

Monitor email performance:
- Delivery rates
- Open rates (if using tracking)
- Click-through rates
- Bounce rates
- Unsubscribe rates 