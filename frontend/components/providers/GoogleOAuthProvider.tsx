'use client'

import { GoogleOAuthProvider as GoogleProvider } from '@react-oauth/google'
import { ReactNode } from 'react'

interface GoogleOAuthProviderProps {
  children: ReactNode
}

export default function GoogleOAuthProvider({ children }: GoogleOAuthProviderProps) {
  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID

  // Check if it's a placeholder or not set
  if (!clientId || clientId === 'YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com') {
    console.warn('⚠️ Google OAuth not configured:')
    console.warn('   1. Get Client ID from: https://console.cloud.google.com/apis/credentials')
    console.warn('   2. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID in frontend/.env.local')
    console.warn('   3. See docs/GOOGLE_OAUTH_SETUP.md for full setup guide')
    console.warn('   Google Sign-In button will not appear.')
    return <>{children}</>
  }

  return (
    <GoogleProvider clientId={clientId}>
      {children}
    </GoogleProvider>
  )
}

