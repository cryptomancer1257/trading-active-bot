# 🚀 Airdrop Frontend Setup Guide

**Created:** October 30, 2025  
**Status:** ✅ Initial Setup Complete

---

## ✅ **What's Done**

1. ✅ Next.js 14 app created with TypeScript & Tailwind
2. ✅ Dependencies installed: next-auth, @heroicons/react, axios
3. ⏳ Need to configure: Google OAuth, pages, components

---

## 📋 **Next Steps**

### **1. Setup Google OAuth (5 minutes)**

**A. Get Google OAuth Credentials:**

1. Go to https://console.cloud.google.com/
2. Create new project: "BOT Token Airdrop"
3. Enable "Google+ API"
4. Create OAuth 2.0 Client ID:
   - Application type: Web application
   - Authorized redirect URIs: 
     - `http://localhost:3000/api/auth/callback/google` (dev)
     - `https://airdrop.cryptomancer.ai/api/auth/callback/google` (prod)
5. Copy `Client ID` and `Client Secret`

**B. Create `.env.local`:**

```bash
# frontend-airdrop/.env.local
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_random_secret_key

# Backend API
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Generate `NEXTAUTH_SECRET`:
```bash
openssl rand -base64 32
```

---

### **2. File Structure**

Need to create these files:

```
frontend-airdrop/
├── app/
│   ├── layout.tsx                    # ✅ Exists
│   ├── page.tsx                      # ⚠️ Need to update
│   ├── api/
│   │   └── auth/
│   │       └── [...nextauth]/
│   │           └── route.ts          # ⏳ CREATE
│   ├── dashboard/
│   │   └── page.tsx                  # ⏳ CREATE
│   ├── tasks/
│   │   └── page.tsx                  # ⏳ CREATE
│   └── leaderboard/
│       └── page.tsx                  # ⏳ CREATE
├── components/
│   ├── Header.tsx                    # ⏳ CREATE
│   ├── TaskCard.tsx                  # ⏳ CREATE
│   ├── ProgressBar.tsx               # ⏳ CREATE
│   ├── ClaimButton.tsx               # ⏳ CREATE
│   └── providers/
│       └── SessionProvider.tsx       # ⏳ CREATE
├── lib/
│   ├── auth.ts                       # ⏳ CREATE
│   └── api.ts                        # ⏳ CREATE
└── types/
    └── airdrop.ts                    # ⏳ CREATE
```

---

### **3. Key Files to Create**

#### **A. `lib/auth.ts` - NextAuth Configuration**

```typescript
import { NextAuthOptions } from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    async signIn({ user, account, profile }) {
      // Register user in backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/airdrop/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: user.email,
          name: user.name,
          google_id: account?.providerAccountId,
          avatar: user.image,
        }),
      });
      
      const data = await response.json();
      user.apiKey = data.api_key; // Store API key for backend calls
      
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        token.apiKey = user.apiKey;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.apiKey = token.apiKey;
      return session;
    },
  },
  pages: {
    signIn: '/auth/signin',
  },
};
```

#### **B. `app/api/auth/[...nextauth]/route.ts`**

```typescript
import NextAuth from 'next-auth';
import { authOptions } from '@/lib/auth';

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
```

#### **C. `lib/api.ts` - API Client**

```typescript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

// Add auth token to requests
export const setAuthToken = (token: string) => {
  apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

// Airdrop API calls
export const airdropAPI = {
  // Get all tasks
  getTasks: () => apiClient.get('/api/airdrop/tasks'),
  
  // Get user status
  getUserStatus: () => apiClient.get('/api/airdrop/status'),
  
  // Verify bot creation
  verifyBotCreation: () => apiClient.post('/api/airdrop/verify-bot-creation'),
  
  // Verify first trade
  verifyFirstTrade: () => apiClient.post('/api/airdrop/verify-first-trade'),
  
  // Verify trading volume
  verifyTradingVolume: () => apiClient.post('/api/airdrop/verify-trading-volume'),
  
  // Discord verification
  verifyDiscord: (discordId: string) => 
    apiClient.post('/api/airdrop/verify-discord', { discord_id: discordId }),
  
  // Telegram verification
  verifyTelegram: (code: string) => 
    apiClient.post('/api/airdrop/verify-telegram', { code }),
  
  // Get referral code
  getReferralCode: () => apiClient.get('/api/airdrop/referral-code'),
  
  // Use referral code
  useReferralCode: (code: string) => 
    apiClient.post('/api/airdrop/use-referral', { referral_code: code }),
  
  // Claim tokens
  claimTokens: () => apiClient.post('/api/airdrop/claim'),
  
  // Leaderboard
  getLeaderboard: () => apiClient.get('/api/trader-contributions/leaderboard/monthly-performance'),
  
  // Submit strategy template
  submitStrategy: (data: any) => 
    apiClient.post('/api/trader-contributions/submit-strategy-template', data),
};

export default apiClient;
```

---

### **4. Backend Updates Needed**

Add user registration endpoint in `api/endpoints/airdrop.py`:

```python
@router.post("/register")
async def register_user(
    user_data: dict,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Register user from Google OAuth"""
    
    # Check if user exists
    user = db.query(User).filter(User.email == user_data['email']).first()
    
    if not user:
        # Create new user
        user = User(
            email=user_data['email'],
            name=user_data['name'],
            google_id=user_data['google_id'],
            avatar_url=user_data.get('avatar'),
            created_at=datetime.now()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate API key for airdrop access
    api_key = secrets.token_urlsafe(32)
    
    # Store API key
    user_api_key = UserAPIKey(
        user_id=user.id,
        api_key=api_key,
        created_at=datetime.now()
    )
    db.add(user_api_key)
    db.commit()
    
    return {
        'success': True,
        'user_id': user.id,
        'api_key': api_key
    }
```

---

### **5. Run Development Server**

```bash
cd frontend-airdrop
npm run dev
```

Open http://localhost:3000

---

### **6. Deploy to Production**

**Frontend (Vercel):**

```bash
cd frontend-airdrop
vercel --prod
```

**Set environment variables in Vercel:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `NEXTAUTH_URL=https://airdrop.cryptomancer.ai`
- `NEXTAUTH_SECRET`
- `NEXT_PUBLIC_API_URL=https://api.cryptomancer.ai`

**DNS:**
```
airdrop.cryptomancer.ai → Vercel
```

---

### **7. Architecture Diagram**

```
┌──────────────────────────────────────────┐
│  User Browser                            │
│  airdrop.cryptomancer.ai                 │
└────────────┬─────────────────────────────┘
             │
             │ 1. Click "Login with Google"
             ↓
┌──────────────────────────────────────────┐
│  Google OAuth                            │
│  accounts.google.com                     │
└────────────┬─────────────────────────────┘
             │
             │ 2. User approves
             ↓
┌──────────────────────────────────────────┐
│  NextAuth Callback                       │
│  /api/auth/callback/google               │
│  - Receives Google user info             │
│  - Calls backend /register               │
│  - Gets API key                          │
└────────────┬─────────────────────────────┘
             │
             │ 3. Register user & get API key
             ↓
┌──────────────────────────────────────────┐
│  Python Backend                          │
│  api.cryptomancer.ai/api/airdrop/*       │
│  - Store user in DB                      │
│  - Generate API key                      │
│  - Return to frontend                    │
└────────────┬─────────────────────────────┘
             │
             │ 4. Store API key in session
             ↓
┌──────────────────────────────────────────┐
│  User Dashboard                          │
│  - View tasks                            │
│  - Verify tasks                          │
│  - Claim tokens                          │
│  - All API calls use API key             │
└──────────────────────────────────────────┘
```

---

### **8. Testing Checklist**

- [ ] Google OAuth login works
- [ ] User registered in backend
- [ ] API key generated and stored
- [ ] Can view tasks
- [ ] Can verify tasks
- [ ] Can view dashboard
- [ ] Can see leaderboard
- [ ] Can claim tokens
- [ ] Referral system works

---

## 🎯 **Quick Commands**

```bash
# Install dependencies
cd frontend-airdrop
npm install

# Setup environment
cp .env.example .env.local
# Edit .env.local with your values

# Run dev server
npm run dev

# Build for production
npm run build

# Deploy to Vercel
vercel --prod
```

---

## 📞 **Support**

- Backend API Docs: http://localhost:8000/docs
- Next.js Docs: https://nextjs.org/docs
- NextAuth Docs: https://next-auth.js.org
- Tailwind Docs: https://tailwindcss.com

---

**Status:** ✅ **Ready to implement pages and components!**

**Next:** Create page components and connect to backend API.

