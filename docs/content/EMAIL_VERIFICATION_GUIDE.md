# Email Verification System Guide

## Overview

The email verification system ensures that users confirm their email address before they can access the platform. This helps prevent fake accounts and ensures users can receive important notifications.

## Features

### ✅ Core Features

1. **Email Verification on Registration**
   - New users receive a verification email after registration
   - Users must click the verification link before they can log in
   - Verification tokens expire after 24 hours

2. **Google OAuth Bypass**
   - Users who sign up via Google OAuth automatically have their email verified
   - Existing users who later log in via Google OAuth get their email verified automatically

3. **Resend Verification Email**
   - Users can request a new verification email if the original expires
   - Available through the verification page

4. **Friendly User Experience**
   - Clear instructions after registration
   - Professional verification email templates
   - Helpful error messages
   - Easy resend functionality

## Architecture

### Backend Components

#### 1. Database Schema
```sql
-- Added to users table
ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN verification_token VARCHAR(255) NULL;
ALTER TABLE users ADD COLUMN verification_token_expires DATETIME NULL;
CREATE INDEX idx_users_verification_token ON users(verification_token);
```

#### 2. Email Service (`services/email_service.py`)
- Handles sending verification emails
- Professional HTML email templates
- Configurable SMTP settings
- Support for Gmail, SendGrid, and other SMTP providers

#### 3. API Endpoints (`api/endpoints/auth.py`)

**POST /auth/register**
- Creates new user with `email_verified = FALSE`
- Generates verification token
- Sends verification email
- Returns user object

**POST /auth/verify-email?token={token}**
- Verifies email address
- Marks user as verified
- Clears verification token
- Returns success message

**POST /auth/resend-verification**
- Generates new verification token
- Sends new verification email
- Returns success message

**POST /auth/token** (login)
- Checks if email is verified
- Returns 403 Forbidden if not verified
- Returns access token if verified

**POST /auth/google**
- Automatically sets `email_verified = TRUE` for Google OAuth users
- No verification email needed

### Frontend Components

#### 1. Registration Flow (`frontend/components/auth/RegisterForm.tsx`)
- After successful registration, shows success message
- Instructions to check email
- Link to resend verification email
- Link to login page

#### 2. Verification Page (`frontend/app/verify-email/page.tsx`)
- Processes verification token from email link
- Shows success/error message
- Allows resending verification email if expired
- Auto-redirects to login after success

#### 3. Login Flow (`frontend/components/auth/LoginForm.tsx`)
- Displays error message if email not verified
- Directs users to check inbox or resend email

## Setup Guide

### 1. Configure Email Service (Backend)

Add the following to your `.env` file:

```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@tradebotmarketplace.com
FROM_NAME=Trade Bot Marketplace
FRONTEND_URL=http://localhost:3001
```

#### For Gmail:
1. Enable 2-Factor Authentication on your Google Account
2. Generate an App Password:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Select "Mail" and "Other (Custom name)"
   - Copy the generated 16-character password
   - Use this as `SMTP_PASSWORD`

#### For SendGrid:
```bash
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### For AWS SES:
```bash
SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
```

### 2. Run Database Migration

```bash
python migrations/migration_runner.py
```

This will add the email verification columns to the `users` table.

### 3. Test Email Sending

```python
from services.email_service import email_service

# Test sending a verification email
email_service.send_verification_email(
    to_email="test@example.com",
    username="testuser",
    verification_token="test-token-123"
)
```

### 4. Frontend Configuration

No additional frontend configuration needed. The email verification feature is automatically enabled.

## User Flows

### Flow 1: Normal Registration

1. User fills out registration form
2. User submits form
3. Backend creates user with `email_verified = FALSE`
4. Backend sends verification email
5. User sees success message: "Check Your Email"
6. User clicks verification link in email
7. Backend marks email as verified
8. User is redirected to login page
9. User logs in successfully

### Flow 2: Google OAuth Registration

1. User clicks "Sign in with Google"
2. Google OAuth flow completes
3. Backend creates user with `email_verified = TRUE`
4. User is logged in immediately (no email verification needed)

### Flow 3: Expired Token

1. User clicks expired verification link
2. Verification page shows "Token expired" error
3. User enters email address
4. User clicks "Resend Verification Email"
5. Backend generates new token
6. Backend sends new verification email
7. User clicks new verification link
8. Email is verified successfully

### Flow 4: Login Before Verification

1. User tries to log in without verifying email
2. Backend returns 403 Forbidden error
3. Login form shows error: "Email not verified. Please check your inbox..."
4. User checks inbox and verifies email
5. User logs in successfully

## Email Templates

### Verification Email

- Subject: "Verify Your Email - Trade Bot Marketplace"
- Professional HTML template with branding
- Clear call-to-action button
- Plain text fallback
- Security warnings about expiration

### Key Elements:
- Welcome message with username
- Prominent "Verify Email Address" button
- Copy-pasteable verification URL
- Expiration notice (24 hours)
- Warning for users who didn't register

## API Error Codes

| Status Code | Error Message | Description |
|-------------|---------------|-------------|
| 400 | "Email already registered" | Email is already in use |
| 400 | "Invalid verification token" | Token doesn't exist or is malformed |
| 400 | "Verification token has expired" | Token is older than 24 hours |
| 400 | "Email is already verified" | User already verified their email |
| 403 | "Email not verified. Please check your inbox..." | User tried to login without verifying |
| 404 | "User not found" | No user with that email (resend endpoint) |
| 500 | "Failed to send verification email" | SMTP configuration issue |

## Monitoring & Troubleshooting

### Check Verification Status

```sql
-- Check users who haven't verified
SELECT id, email, created_at, email_verified 
FROM users 
WHERE email_verified = FALSE;

-- Check expired tokens
SELECT id, email, verification_token_expires 
FROM users 
WHERE email_verified = FALSE 
  AND verification_token_expires < NOW();
```

### Common Issues

#### 1. Emails Not Sending

**Symptoms:**
- Users not receiving verification emails
- No errors in backend logs

**Solutions:**
- Check SMTP credentials in `.env`
- Verify SMTP server and port
- Check firewall/network settings
- For Gmail: Ensure App Password is used (not regular password)
- Check email spam folder

#### 2. Verification Link Not Working

**Symptoms:**
- Users click link but get "Invalid token" error
- Link appears correct

**Solutions:**
- Check `FRONTEND_URL` environment variable
- Ensure frontend is accessible at that URL
- Check if token expired (24 hours)
- Verify database has the token

#### 3. Google OAuth Users Can't Login

**Symptoms:**
- Google OAuth login succeeds but user can't access dashboard

**Solutions:**
- Check that `email_verified` is set to TRUE in database
- Verify Google OAuth endpoint sets `email_verified = TRUE`
- Check backend logs for errors

### Backend Logs

Enable debug logging for email service:

```python
import logging
logging.getLogger('services.email_service').setLevel(logging.DEBUG)
```

## Security Considerations

### ✅ Implemented Security Features

1. **Token Expiration**
   - Verification tokens expire after 24 hours
   - Expired tokens cannot be reused

2. **One-Time Use**
   - Tokens are cleared after successful verification
   - Cannot be reused even if not expired

3. **Secure Token Generation**
   - Uses `secrets.token_urlsafe(32)` for cryptographically secure tokens
   - 32 bytes = 256 bits of entropy

4. **Rate Limiting**
   - Consider adding rate limiting to resend endpoint
   - Prevents email spam abuse

5. **HTTPS Required**
   - Verification links should only work over HTTPS in production
   - Update `FRONTEND_URL` to use HTTPS

### 🔐 Recommended Additional Security

1. **Rate Limiting**
```python
from fastapi_limiter.depends import RateLimiter

@router.post("/resend-verification", dependencies=[Depends(RateLimiter(times=3, hours=1))])
async def resend_verification_email(...):
    ...
```

2. **CAPTCHA for Resend**
- Add reCAPTCHA to resend verification page
- Prevents automated abuse

3. **Email Audit Log**
```python
# Log all verification emails sent
verification_log = VerificationLog(
    user_id=user.id,
    email=user.email,
    sent_at=datetime.utcnow(),
    token=verification_token
)
db.add(verification_log)
```

## Testing

### Manual Testing

1. **Register a new user**
   ```bash
   curl -X POST http://localhost:8000/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "password123",
       "role": "USER"
     }'
   ```

2. **Check email inbox** for verification link

3. **Click verification link** or test endpoint:
   ```bash
   curl -X POST "http://localhost:8000/auth/verify-email?token=YOUR_TOKEN_HERE"
   ```

4. **Try to login before verification** (should fail):
   ```bash
   curl -X POST http://localhost:8000/auth/token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=password123"
   ```

5. **Login after verification** (should succeed)

### Automated Testing

```python
# tests/test_email_verification.py

def test_registration_sends_verification_email(client, db):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "role": "USER"
    })
    assert response.status_code == 200
    
    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user.email_verified == False
    assert user.verification_token is not None

def test_email_verification_success(client, db):
    # Create user with verification token
    user = create_test_user(db, email_verified=False)
    token = "test-token-123"
    user.verification_token = token
    db.commit()
    
    # Verify email
    response = client.post(f"/auth/verify-email?token={token}")
    assert response.status_code == 200
    assert response.json()["success"] == True
    
    # Check user is verified
    db.refresh(user)
    assert user.email_verified == True
    assert user.verification_token is None

def test_login_without_verification_fails(client, db):
    user = create_test_user(db, email_verified=False)
    
    response = client.post("/auth/token", data={
        "username": user.email,
        "password": "password123"
    })
    assert response.status_code == 403
    assert "not verified" in response.json()["detail"].lower()

def test_google_oauth_skips_verification(client, db, mock_google_token):
    response = client.post("/auth/google", json={
        "credential": mock_google_token
    })
    assert response.status_code == 200
    
    user = db.query(User).filter(User.email == "google@example.com").first()
    assert user.email_verified == True
```

## Production Checklist

- [ ] SMTP credentials configured in production `.env`
- [ ] `FRONTEND_URL` set to production URL (HTTPS)
- [ ] Database migration applied
- [ ] Email sending tested (send test email)
- [ ] Verification link tested (click test verification link)
- [ ] Login flow tested (verify error message before verification)
- [ ] Google OAuth tested (verify auto-verification)
- [ ] Email templates reviewed (check branding, links)
- [ ] Error handling tested (expired token, invalid token)
- [ ] Rate limiting configured (optional but recommended)
- [ ] Monitoring set up (email sending failures, verification rates)

## FAQ

**Q: Can I disable email verification for development?**

A: Yes, you can skip email verification by setting all existing users to verified:
```sql
UPDATE users SET email_verified = TRUE;
```

Or modify the login endpoint to skip the verification check in development mode.

**Q: How do I manually verify a user?**

A: Run this SQL:
```sql
UPDATE users 
SET email_verified = TRUE, 
    verification_token = NULL, 
    verification_token_expires = NULL 
WHERE email = 'user@example.com';
```

**Q: What if SMTP is not configured?**

A: The system will log a warning and skip sending emails. Users will need to be manually verified via SQL.

**Q: Can I change the token expiration time?**

A: Yes, edit `api/endpoints/auth.py`:
```python
# Change from 24 hours to 48 hours
user.verification_token_expires = datetime.utcnow() + timedelta(hours=48)
```

**Q: How do I customize the email templates?**

A: Edit `services/email_service.py`, specifically the `send_verification_email` method. You can modify the HTML and text content.

## Support

For issues or questions:
- Check backend logs for SMTP errors
- Verify environment variables are set correctly
- Test email sending with a simple script
- Check database for user verification status
- Review this guide for common troubleshooting steps


