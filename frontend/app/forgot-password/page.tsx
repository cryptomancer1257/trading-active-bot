'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

/**
 * Redirect page for backward compatibility
 * Redirects /forgot-password to /auth/forgot-password
 */
export default function ForgotPasswordRedirect() {
  const router = useRouter()
  
  useEffect(() => {
    router.replace('/auth/forgot-password')
  }, [router])
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center">
      <div className="text-white text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p>Redirecting...</p>
      </div>
    </div>
  )
}

