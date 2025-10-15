# Google OAuth Quick Start

## 🚀 Quick Setup (5 minutes)

### 1. Get Google Client ID

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Google+ API"
4. Go to **Credentials** > **Create Credentials** > **OAuth client ID**
5. Select "Web application"
6. Add authorized origins: `http://localhost:3001`
7. Copy your **Client ID**

### 2. Configure (Choose ONE method)

#### Option A: 🤖 Automated Setup (Recommended)

```bash
# Run the setup script
./scripts/setup_google_oauth.sh
```

The script will:
- ✅ Configure both frontend and backend
- ✅ Create/update `.env` files automatically
- ✅ Validate your Client ID format

#### Option B: ✋ Manual Setup

**Frontend** (`frontend/.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

**Backend** (root `.env`):
```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
```

💡 **Note**: You only need **Client ID**, NOT Client Secret!

### 3. Restart Services

```bash
# Backend
python main.py

# Frontend (in another terminal)
cd frontend && npm run dev
```

### 4. Test

Visit: `http://localhost:3001/auth/login`

You should see the "Sign in with Google" button!

---

## 📚 Full Documentation

For detailed setup instructions, troubleshooting, and production deployment:

👉 **See: [docs/GOOGLE_OAUTH_SETUP.md](docs/GOOGLE_OAUTH_SETUP.md)**

---

## 🔑 Client ID vs Client Secret

| What | Need It? | Why? |
|------|----------|------|
| **Client ID** | ✅ YES | Verify Google JWT tokens |
| **Client Secret** | ❌ NO | Only for server-to-server OAuth |

**How it works:**
```
1. User clicks "Sign in with Google"
2. Google returns JWT token (already signed)
3. Frontend sends token to backend
4. Backend verifies token with Client ID ✅
5. No Client Secret needed! 🎉
```

## ⚠️ Common Issues

**Google button not showing?**
- Check if `NEXT_PUBLIC_GOOGLE_CLIENT_ID` is set in `frontend/.env.local`
- Make sure it's not the placeholder value
- Restart frontend dev server
- Clear browser cache

**"Invalid token" error?**
- Ensure backend `GOOGLE_CLIENT_ID` matches frontend
- Check if domain is in authorized origins
- Restart backend server after changing `.env`

**"Google OAuth not configured" in backend?**
- Check if `.env` file exists in root directory
- Verify `GOOGLE_CLIENT_ID` is set
- Restart backend: `python main.py`

---

## 🔗 Resources

- [Google Cloud Console](https://console.cloud.google.com/)
- [Backend ENV Setup](BACKEND_ENV_SETUP.md) ⭐ NEW
- [Full Setup Guide](docs/GOOGLE_OAUTH_SETUP.md)
- [Frontend ENV Setup](frontend/ENV_SETUP.md)

