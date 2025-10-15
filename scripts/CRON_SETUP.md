# Plan Expiry Cron Job Setup

This guide explains how to set up the automated plan expiry notification and downgrade system.

## What It Does

The cron job performs two tasks daily:

1. **Send Expiry Reminders**: Notifies users 7 days before their Pro plan expires
2. **Downgrade Expired Plans**: Automatically downgrades expired Pro plans to Free

## Installation

### 1. Manual Test Run

First, test the scripts manually to ensure they work:

```bash
# Test expiry reminders (7-day warning)
python3 services/plan_expiry_notifier.py

# Test plan downgrade
python3 services/plan_expiry_notifier.py downgrade
```

### 2. Add to Crontab

Edit your crontab:

```bash
crontab -e
```

Add this line to run daily at 9 AM:

```cron
0 9 * * * /path/to/trade-bot-marketplace/scripts/plan_expiry_cron.sh
```

**Example with actual path:**
```cron
0 9 * * * /Users/thanhde.nguyenshopee.com/workspace/ai-agent/trade-bot-marketplace/scripts/plan_expiry_cron.sh
```

### 3. Verify Cron Job

List your cron jobs to verify:

```bash
crontab -l
```

### 4. Check Logs

Logs are written to `logs/plan_expiry_YYYYMMDD.log`:

```bash
tail -f logs/plan_expiry_$(date +%Y%m%d).log
```

## Cron Schedule Options

```cron
# Run daily at 9 AM
0 9 * * * /path/to/script.sh

# Run daily at midnight
0 0 * * * /path/to/script.sh

# Run twice daily (9 AM and 9 PM)
0 9,21 * * * /path/to/script.sh

# Run every hour
0 * * * * /path/to/script.sh
```

## How It Works

### 1. Expiry Reminders (7 days before)

- Queries database for Pro plans expiring in 7 days
- Sends email notification to each user
- Email includes:
  - Expiry date
  - What happens when plan expires
  - Link to renew

### 2. Plan Downgrade (on expiry date)

- Queries database for expired Pro plans
- Updates plan to Free with these changes:
  ```python
  max_bots: unlimited → 5
  allowed_environment: mainnet → testnet
  publish_marketplace: true → false
  revenue_share: 90% → 0%
  ```
- Creates history record
- Sends downgrade notification email

## Database Impact

### Tables Modified

1. **user_plans**: Plan fields updated to Free defaults
2. **plan_history**: New record added for downgrade action

### Transaction Safety

- All updates wrapped in database transaction
- Rollback on error
- Logs all actions for audit trail

## Monitoring

### Check Execution

```bash
# View today's log
cat logs/plan_expiry_$(date +%Y%m%d).log

# View all recent logs
ls -lh logs/plan_expiry_*.log

# Count notifications sent
grep "Sent expiry reminder" logs/plan_expiry_*.log | wc -l

# Count downgrades
grep "Downgraded user" logs/plan_expiry_*.log | wc -l
```

### Database Queries

```sql
-- Check plans expiring soon
SELECT 
    up.id, 
    u.email, 
    up.expiry_date,
    DATEDIFF(up.expiry_date, NOW()) as days_until_expiry
FROM user_plans up
JOIN users u ON u.id = up.user_id
WHERE up.plan_name = 'pro'
  AND up.status = 'active'
  AND up.expiry_date <= DATE_ADD(NOW(), INTERVAL 7 DAY)
  AND up.expiry_date > NOW();

-- Check plan history
SELECT * FROM plan_history 
WHERE action = 'downgrade' 
ORDER BY action_date DESC 
LIMIT 10;
```

## Troubleshooting

### Cron Job Not Running

1. Check cron service is running:
   ```bash
   sudo service cron status
   ```

2. Check crontab syntax:
   ```bash
   crontab -l
   ```

3. Check script permissions:
   ```bash
   ls -l scripts/plan_expiry_cron.sh
   ```

### Email Not Sending

1. Check email service configuration in `.env`:
   ```
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

2. Check logs for email errors:
   ```bash
   grep "email" logs/plan_expiry_*.log
   ```

### Database Connection Issues

1. Check database is running:
   ```bash
   mysql -u root -p -e "SELECT 1"
   ```

2. Check database config in `.env`:
   ```
   DATABASE_URL=mysql+pymysql://user:pass@localhost/db_name
   ```

## Manual Operations

### Force Downgrade Single User

```python
from services.plan_expiry_notifier import plan_expiry_notifier
from core.database import SessionLocal
from core import models

db = SessionLocal()
plan = db.query(models.UserPlan).filter(
    models.UserPlan.user_id == 123  # User ID
).first()

plan_expiry_notifier._downgrade_to_free(plan)
db.commit()
```

### Send Test Email

```python
from services.plan_expiry_notifier import plan_expiry_notifier
from core.database import SessionLocal
from core import models

db = SessionLocal()
plan = db.query(models.UserPlan).filter(
    models.UserPlan.user_id == 123  # User ID
).first()

plan_expiry_notifier._send_expiry_reminder(plan, days_remaining=7)
```

## Security Considerations

- Logs contain user IDs but NOT sensitive data
- Email templates do NOT expose payment info
- Database queries use SQLAlchemy ORM (SQL injection safe)
- Cron script runs with file owner permissions

## Customization

### Change Reminder Days

Edit `plan_expiry_cron.sh` line:

```bash
# From 7 days to 3 days
python3 "$PROJECT_ROOT/services/plan_expiry_notifier.py" 3
```

### Multiple Reminders

Add multiple calls in cron script:

```bash
# 7 days before
python3 "$PROJECT_ROOT/services/plan_expiry_notifier.py" 7

# 3 days before
python3 "$PROJECT_ROOT/services/plan_expiry_notifier.py" 3

# 1 day before
python3 "$PROJECT_ROOT/services/plan_expiry_notifier.py" 1
```

## Production Recommendations

1. **Run at low-traffic times**: 9 AM or midnight
2. **Monitor logs daily**: Check for errors
3. **Set up log rotation**: Prevent disk fill-up
4. **Test in staging first**: Before production deploy
5. **Alert on failures**: Integrate with monitoring tools

## Support

For issues or questions:
- Check logs first: `logs/plan_expiry_*.log`
- Review database: `user_plans` and `plan_history` tables
- Contact: dev@quantumforget.ai

