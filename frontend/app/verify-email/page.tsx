'use client'

import { useEffect, useState, useRef } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { toast } from 'react-hot-toast'
import Link from 'next/link'

export default function VerifyEmailPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')
  const [email, setEmail] = useState('')
  const [isResending, setIsResending] = useState(false)
  const hasVerifiedRef = useRef(false)

  useEffect(() => {
    const token = searchParams.get('token')
    
    if (!token) {
      setStatus('error')
      setMessage('Invalid verification link. Please check your email and try again.')
      return
    }

    // Prevent running verification multiple times (React Strict Mode runs effects twice)
    if (hasVerifiedRef.current) {
      console.log('⚠️ Verification already attempted, skipping')
      return
    }

    hasVerifiedRef.current = true
    verifyEmail(token)
  }, [searchParams])

  const verifyEmail = async (token: string) => {
    try {
      console.log('🔵 Verifying email with token:', token.substring(0, 20) + '...')
      console.log('🔵 API URL:', process.env.NEXT_PUBLIC_API_URL)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/verify-email?token=${token}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      console.log('🔵 Response status:', response.status)
      console.log('🔵 Response ok:', response.ok)

      // Clone response to read it multiple times if needed
      const responseClone = response.clone()
      let data

      try {
        data = await response.json()
        console.log('🔵 Response data:', data)
      } catch (e) {
        console.error('❌ Failed to parse JSON response:', e)
        try {
          const text = await responseClone.text()
          console.error('❌ Response text:', text)
        } catch (textError) {
          console.error('❌ Failed to read response text:', textError)
        }
        throw new Error('Invalid response format')
      }

      if (response.ok) {
        console.log('✅ Email verified successfully!')
        setStatus('success')
        setMessage(data.message || 'Email verified successfully!')
        toast.success('Email verified! You can now log in.')
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          console.log('🔵 Redirecting to /auth/login')
          window.location.href = '/auth/login'
        }, 3000)
      } else {
        console.error('❌ Verification failed:', data)
        setStatus('error')
        setMessage(data.detail || 'Verification failed. Please try again.')
        toast.error(data.detail || 'Verification failed')
      }
    } catch (error) {
      console.error('❌ Verification error:', error)
      setStatus('error')
      setMessage('An error occurred during verification. Please try again.')
      toast.error('Verification failed')
    }
  }

  const handleResendVerification = async () => {
    if (!email) {
      toast.error('Please enter your email address')
      return
    }

    setIsResending(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/resend-verification`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (response.ok) {
        toast.success('Verification email sent! Please check your inbox.')
        setEmail('')
      } else {
        toast.error(data.detail || 'Failed to send verification email')
      }
    } catch (error) {
      console.error('Resend error:', error)
      toast.error('Failed to send verification email')
    } finally {
      setIsResending(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-2xl p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mb-4">
              {status === 'loading' && (
                <svg className="animate-spin h-8 w-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
              {status === 'success' && (
                <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
              {status === 'error' && (
                <svg className="h-8 w-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </div>
            
            <h1 className="text-3xl font-bold text-white mb-2">
              {status === 'loading' && 'Verifying Email...'}
              {status === 'success' && 'Email Verified!'}
              {status === 'error' && 'Verification Failed'}
            </h1>
            
            <p className="text-slate-300">
              {message}
            </p>
          </div>

          {/* Actions */}
          <div className="space-y-4">
            {status === 'success' && (
              <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                <p className="text-green-400 text-sm">
                  ✅ Your email has been verified successfully. Redirecting to login page...
                </p>
              </div>
            )}

            {status === 'error' && (
              <>
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                  <p className="text-red-400 text-sm mb-2">
                    ❌ {message}
                  </p>
                  {message.includes('expired') && (
                    <p className="text-slate-400 text-xs">
                      Your verification link has expired. Please request a new one below.
                    </p>
                  )}
                </div>

                {/* Resend verification form */}
                <div className="space-y-3">
                  <label className="block">
                    <span className="text-slate-300 text-sm font-medium">Email Address</span>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="your.email@example.com"
                      className="mt-1 block w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                    />
                  </label>

                  <button
                    onClick={handleResendVerification}
                    disabled={isResending || !email}
                    className="w-full px-4 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isResending ? (
                      <>
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Sending...
                      </>
                    ) : (
                      <>
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        Resend Verification Email
                      </>
                    )}
                  </button>
                </div>
              </>
            )}

            {/* Back to login */}
            <div className="pt-4 border-t border-slate-700">
              <Link
                href="/auth/login"
                className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white font-semibold rounded-lg transition-all"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                Back to Login
              </Link>
            </div>
          </div>
        </div>

        {/* Help text */}
        <div className="mt-6 text-center">
          <p className="text-slate-400 text-sm">
            Need help?{' '}
            <a href="mailto:support@tradebotmarketplace.com" className="text-blue-400 hover:text-blue-300 underline">
              Contact Support
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

