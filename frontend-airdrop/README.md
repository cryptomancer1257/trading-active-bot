# BOT Token Airdrop Frontend

Standalone airdrop website for BOT token distribution.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment File

The `.env.local` file is already created with:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=114750114886-72d8dms069foichq9c1dft6i0r4no5u6.apps.googleusercontent.com
NEXT_PUBLIC_FRONTEND_URL=http://localhost:3002
```

### 3. Run Development Server

```bash
npm run dev
```

Open http://localhost:3002

### 4. Build for Production

```bash
npm run build
npm start
```

## 📁 Project Structure

```
frontend-airdrop/
├── app/
│   ├── page.tsx              # Landing page
│   ├── login/page.tsx        # Auth page
│   └── dashboard/page.tsx    # User dashboard
├── lib/
│   ├── auth.ts               # JWT authentication
│   └── api.ts                # API client
└── package.json
```

## 🔐 Authentication

Multiple authentication methods:

### 1. **Email/Password**
- Register: `POST /api/auth/register` (sends verification email)
- Verify: `GET /api/auth/verify-email?token=xxx`
- Login: `POST /api/auth/token` (requires verified email)

### 2. **Google OAuth**
- One-click sign in with Google
- Auto-verified (no email verification needed)
- Backend: `POST /api/auth/google`

### Token Management
- JWT tokens stored in localStorage
- Auto-attached to all API requests
- Refresh token for session management

## 🌐 Deployment

### Vercel

```bash
vercel --prod
```

Set environment variable:
- `NEXT_PUBLIC_API_URL` = your backend API URL

### Domain

Point `airdrop.cryptomancer.ai` to deployment.

## 📊 Pages

- `/` - Landing page ✅
- `/login` - Login/Register (Email + Google OAuth) ✅
- `/verify` - Email verification handler ✅
- `/dashboard` - User dashboard ✅
- `/tasks` - All tasks with categories ✅
- `/leaderboard` - Rankings and top performers ✅

## 🔗 Backend

Requires `trade-bot-marketplace` backend running on port 8000.

API endpoints:
- `/api/airdrop/*` - Airdrop tasks
- `/api/trader-contributions/*` - Strategy templates
