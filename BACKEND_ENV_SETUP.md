# Backend Environment Configuration

## Required Environment Variables

Create a `.env` file in the **root directory** with the following configuration:

```bash
# Database Configuration
DATABASE_URL=mysql+pymysql://botuser:botpassword123@localhost:3307/bot_marketplace

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT Secret
SECRET_KEY=your-secret-key-here-change-in-production

# Google OAuth 2.0
# ⚠️ IMPORTANT: You only need Client ID, NOT Client Secret!
# Get your Client ID from: https://console.cloud.google.com/apis/credentials
# Follow setup guide: docs/GOOGLE_OAUTH_SETUP.md
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Environment
ENVIRONMENT=development

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Quick Setup

### 1. Create .env file

```bash
# In project root directory
cat > .env << 'EOF'
DATABASE_URL=mysql+pymysql://botuser:botpassword123@localhost:3307/bot_marketplace
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
EOF
```

### 2. Or Export Environment Variables

```bash
export GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
```

### 3. Restart Backend

```bash
python main.py
```

## ❓ FAQ

### Do I need Client Secret?

**NO!** You only need **Client ID**.

- ✅ **Client ID**: Used to verify Google JWT tokens (REQUIRED)
- ❌ **Client Secret**: Only for server-to-server OAuth flow (NOT NEEDED)

### Why don't we need Client Secret?

Because we use Google Sign-In button which:
1. User signs in on Google's page
2. Google returns a **signed JWT token**
3. Backend verifies the token signature using **Client ID**
4. No need for Client Secret in this flow

### Where to get Client ID?

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to **APIs & Services** > **Credentials**
4. Find your **OAuth 2.0 Client ID**
5. Copy the **Client ID** (looks like: `xxx.apps.googleusercontent.com`)

### Same Client ID for frontend and backend?

**YES!** Use the **SAME** Client ID for both:
- Frontend: `NEXT_PUBLIC_GOOGLE_CLIENT_ID`
- Backend: `GOOGLE_CLIENT_ID`

## Verification

Check if backend reads the environment variable:

```bash
python -c "import os; print('GOOGLE_CLIENT_ID:', os.getenv('GOOGLE_CLIENT_ID'))"
```

Should output:
```
GOOGLE_CLIENT_ID: your-client-id.apps.googleusercontent.com
```

## Production Notes

For production:
1. Use different Client IDs for dev and prod
2. Update authorized origins in Google Cloud Console
3. Use environment variables from your hosting provider
4. Never commit `.env` to version control

## See Also

- [Google OAuth Quick Start](GOOGLE_OAUTH_QUICKSTART.md)
- [Full Google OAuth Setup Guide](docs/GOOGLE_OAUTH_SETUP.md)
- [Frontend ENV Setup](frontend/ENV_SETUP.md)

