# Frontend Environment Variables Setup

## Required Environment Variables

Create a `.env.local` file in the `frontend` directory with the following variables:

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Google OAuth 2.0
# Get your Client ID from: https://console.cloud.google.com/apis/credentials
# Follow setup guide: docs/GOOGLE_OAUTH_SETUP.md
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

## Setup Instructions

1. Copy the template above to `.env.local`
2. Replace `your-google-client-id.apps.googleusercontent.com` with your actual Google OAuth Client ID
3. For Google OAuth setup, follow: `../docs/GOOGLE_OAUTH_SETUP.md`

## Production Configuration

For production deployment, update the following in your environment:

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-production-client-id.apps.googleusercontent.com
```

**Important**: Never commit `.env.local` to version control!

