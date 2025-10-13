# Google OAuth 2.0 Setup Guide

This guide will help you set up Google OAuth 2.0 authentication for the QuantumForge Trading Bot Marketplace.

## Overview

Google OAuth allows users to sign in to the platform using their Google account, providing a seamless and secure authentication experience.

## Prerequisites

- A Google Account
- Access to [Google Cloud Console](https://console.cloud.google.com/)
- Backend and Frontend environments configured

---

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click **"New Project"**
4. Enter your project name (e.g., "QuantumForge Trading Bot")
5. Click **"Create"**

---

## Step 2: Enable Google+ API

1. In your Google Cloud project, go to **"APIs & Services"** > **"Library"**
2. Search for **"Google+ API"** or **"Google Identity"**
3. Click on **"Google+ API"**
4. Click **"Enable"**

---

## Step 3: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** > **"OAuth consent screen"**
2. Select **"External"** user type (or "Internal" if using Google Workspace)
3. Click **"Create"**
4. Fill in the required information:
   - **App name**: QuantumForge Trading Bot Marketplace
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
5. Click **"Save and Continue"**
6. On the **Scopes** page, click **"Add or Remove Scopes"**
7. Add these scopes:
   - `email`
   - `profile`
   - `openid`
8. Click **"Update"** and then **"Save and Continue"**
9. On the **Test users** page (for development), add your email addresses
10. Click **"Save and Continue"**
11. Review and click **"Back to Dashboard"**

---

## Step 4: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"Create Credentials"** > **"OAuth client ID"**
3. Select **"Web application"**
4. Configure the settings:
   - **Name**: QuantumForge Web Client
   - **Authorized JavaScript origins**:
     ```
     http://localhost:3001
     http://localhost:3000
     https://yourdomain.com (for production)
     ```
   - **Authorized redirect URIs**:
     ```
     http://localhost:3001/auth/callback
     http://localhost:3000/auth/callback
     https://yourdomain.com/auth/callback (for production)
     ```
5. Click **"Create"**
6. **IMPORTANT**: Copy the **Client ID** - you'll need this for environment variables

---

## Step 5: Configure Environment Variables

### Frontend Configuration

Create or update `.env.local` file in the `frontend` directory:

```bash
# Google OAuth Client ID (Frontend)
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com

# API URL (if not already set)
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Configuration

Update `.env` file or set environment variables in the root directory:

```bash
# Google OAuth Client ID (Backend - same as frontend)
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
```

**Note**: The backend uses the same Client ID to verify tokens from Google.

---

## Step 6: Verify Installation

### 1. Install Dependencies (Already Done)

Frontend:
```bash
cd frontend
npm install @react-oauth/google jwt-decode
```

Backend:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### 2. Restart Services

Restart both frontend and backend:

```bash
# Backend
# Stop current backend (Ctrl+C)
python main.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

### 3. Test Google Sign-In

1. Navigate to: `http://localhost:3001/auth/login`
2. You should see the **"Sign in with Google"** button below the regular login form
3. Click the Google button
4. Sign in with your Google account
5. You should be redirected to `/dashboard` after successful authentication

---

## Troubleshooting

### Error: "Google OAuth not configured"

**Problem**: Backend returns "Google OAuth not configured. Please set GOOGLE_CLIENT_ID environment variable."

**Solution**: 
- Ensure `GOOGLE_CLIENT_ID` is set in your backend environment
- Restart the backend server after setting the variable

### Error: "Invalid Google token"

**Problem**: Token verification fails

**Solutions**:
1. Ensure the Client ID in frontend matches the backend
2. Check if the token hasn't expired
3. Verify that your domain is in **Authorized JavaScript origins**

### Google Button Not Showing

**Problem**: The Google Sign-In button doesn't appear

**Solutions**:
1. Check browser console for errors
2. Verify `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set in frontend `.env.local`
3. Ensure you're using `http://localhost:3001` (or your configured domain)
4. Try clearing browser cache and cookies

### "Access blocked: This app's request is invalid"

**Problem**: Google shows an error page when trying to sign in

**Solutions**:
1. Go back to OAuth consent screen configuration
2. Verify all required fields are filled
3. Add your test email to Test Users (if app is not published)
4. Check Authorized JavaScript origins and redirect URIs

### "redirect_uri_mismatch"

**Problem**: Google returns redirect URI mismatch error

**Solutions**:
1. Go to Google Cloud Console > Credentials
2. Edit your OAuth 2.0 Client ID
3. Add the exact URI shown in the error message to **Authorized redirect URIs**
4. Save and try again

---

## Security Best Practices

1. **Never commit credentials to version control**
   - Add `.env` and `.env.local` to `.gitignore`
   - Use environment variables for all sensitive data

2. **Use different credentials for development and production**
   - Create separate OAuth clients for dev and prod
   - Restrict authorized origins appropriately

3. **Regularly rotate credentials**
   - Update Client IDs periodically
   - Revoke unused credentials

4. **Monitor OAuth usage**
   - Check Google Cloud Console for suspicious activity
   - Set up alerts for unusual patterns

---

## Production Deployment

### Update Authorized Origins

Before deploying to production:

1. Go to Google Cloud Console > Credentials
2. Edit your OAuth 2.0 Client ID
3. Add production domains to:
   - **Authorized JavaScript origins**:
     ```
     https://yourdomain.com
     https://www.yourdomain.com
     ```
   - **Authorized redirect URIs**:
     ```
     https://yourdomain.com/auth/callback
     https://www.yourdomain.com/auth/callback
     ```

### Publish OAuth Consent Screen

1. Go to **"OAuth consent screen"**
2. Click **"Publish App"**
3. Follow the verification process if required by Google

---

## API Endpoints

### Backend Endpoint

**POST** `/api/v1/auth/google`

**Request Body**:
```json
{
  "credential": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjdhYmM..."
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Frontend Usage

The frontend automatically handles Google authentication using the `@react-oauth/google` library and sends the credential to the backend for verification.

---

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Sign-In for Web](https://developers.google.com/identity/gsi/web)
- [Google Cloud Console](https://console.cloud.google.com/)
- [@react-oauth/google Documentation](https://www.npmjs.com/package/@react-oauth/google)

---

## Support

If you encounter issues not covered in this guide:

1. Check the browser console for errors
2. Check backend logs for detailed error messages
3. Verify all environment variables are correctly set
4. Ensure all services are running and accessible

---

**Last Updated**: January 2025
**Version**: 1.0.0

