# Email Verification Quick Start

## ⚡ 5-Minute Setup

### Step 1: Configure Email Service (2 minutes)

Add these to your `.env` file:

```bash
# Email Configuration - REQUIRED for email verification
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@tradebotmarketplace.com
FROM_NAME=Trade Bot Marketplace
FRONTEND_URL=http://localhost:3001
```

### Step 2: Get Gmail App Password (2 minutes)

If using Gmail:

1. Go to [Google Account](https://myaccount.google.com/)
2. Security → 2-Step Verification → App passwords
3. Select "Mail" and "Other (Custom name)"
4. Copy the 16-character password
5. Use it as `SMTP_PASSWORD` in `.env`

### Step 3: Run Migration (30 seconds)

```bash
python migrations/migration_runner.py
```

### Step 4: Test It! (30 seconds)

1. Start your backend:
   ```bash
   python core/main.py
   ```

2. Register a new user at `http://localhost:3001/register`

3. Check your email inbox for the verification email

4. Click the verification link

5. Log in with your verified account

## 🎯 What's Included

- ✅ Email verification on registration
- ✅ Professional verification email templates
- ✅ Google OAuth auto-verification
- ✅ Resend verification email
- ✅ Token expiration (24 hours)
- ✅ Friendly error messages
- ✅ User-friendly UI

## 🔧 Using Other Email Providers

### SendGrid
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

### AWS SES
```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

### Microsoft Outlook
```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-outlook-email@outlook.com
SMTP_PASSWORD=your-outlook-password
```

## 📋 Verification Checklist

- [ ] SMTP credentials added to `.env`
- [ ] Gmail App Password generated (if using Gmail)
- [ ] Database migration completed
- [ ] Backend server restarted
- [ ] Test registration completed
- [ ] Verification email received
- [ ] Verification link clicked successfully
- [ ] Login after verification works

## 🚫 Troubleshooting

### "Failed to send verification email"
- Check SMTP credentials in `.env`
- For Gmail: Use App Password, not regular password
- Check firewall/network settings

### "Email not verified. Please check your inbox"
- Check your email spam folder
- Click the verification link in the email
- If expired, use "Resend verification email" option

### "No emails being sent"
- Verify `SMTP_USERNAME` and `SMTP_PASSWORD` are correct
- Check backend logs for SMTP errors
- Test with a simple Python script:
  ```python
  from services.email_service import email_service
  email_service.send_verification_email(
      to_email="test@example.com",
      username="testuser",
      verification_token="test123"
  )
  ```

## 🔒 Security Notes

- Verification tokens expire after 24 hours
- Tokens are cleared after use (one-time use)
- Google OAuth users bypass email verification
- Use HTTPS in production for verification links

## 📚 Full Documentation

For complete details, see [EMAIL_VERIFICATION_GUIDE.md](./docs/EMAIL_VERIFICATION_GUIDE.md)

## 🆘 Need Help?

1. Check `EMAIL_VERIFICATION_GUIDE.md` for detailed troubleshooting
2. Review backend logs for errors
3. Verify environment variables are set
4. Test email sending with a simple script

---

**Ready?** Let's get started! Add the SMTP credentials to your `.env` file and run the migration. 🚀

