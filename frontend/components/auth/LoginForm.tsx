'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { GoogleLogin, CredentialResponse } from '@react-oauth/google'
import toast from 'react-hot-toast'

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginFormData = z.infer<typeof loginSchema>

export default function LoginForm() {
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const { login } = useAuth()
  const router = useRouter()
  
  // Check if Google OAuth is configured
  const googleClientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID
  const isGoogleConfigured = googleClientId && googleClientId !== 'YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com'
  
  // Log on component mount
  useEffect(() => {
    console.log('🔵 LoginForm mounted')
    console.log('🔵 Google Client ID:', googleClientId ? googleClientId.substring(0, 20) + '...' : 'NOT SET')
    console.log('🔵 Google OAuth configured:', isGoogleConfigured ? 'YES ✅' : 'NO ❌')
    console.log('🔵 API URL:', process.env.NEXT_PUBLIC_API_URL)
  }, [googleClientId, isGoogleConfigured])

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  })

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true)
    try {
      const success = await login({
        username: data.email,
        password: data.password,
      })
      if (success) {
        router.push('/dashboard')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleSuccess = async (credentialResponse: CredentialResponse) => {
    setIsLoading(true)
    console.log('🔵 Google OAuth Started')
    
    try {
      if (!credentialResponse.credential) {
        toast.error('Failed to get Google credentials')
        return
      }

      console.log('🔵 Sending credential to backend...')
      
      // Send credential to backend
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          credential: credentialResponse.credential
        }),
      })

      console.log('🔵 Backend response status:', response.status)

      if (!response.ok) {
        const error = await response.json()
        console.error('❌ Backend error:', error)
        throw new Error(error.detail || 'Google authentication failed')
      }

      const data = await response.json()
      console.log('🔵 Backend returned data:', { 
        hasToken: !!data.access_token,
        tokenPreview: data.access_token ? data.access_token.substring(0, 30) + '...' : 'NO TOKEN'
      })
      
      if (!data.access_token) {
        throw new Error('No access token received from backend')
      }
      
      // Clear any existing tokens first
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      console.log('🔵 Cleared old tokens')
      
      // Store both access and refresh tokens
      localStorage.setItem('access_token', data.access_token)
      if (data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh_token)
        console.log('✅ Both access and refresh tokens saved')
      } else {
        console.log('✅ Access token saved (no refresh token in response)')
      }
      
      // Verify token was actually saved
      const verifyToken = localStorage.getItem('access_token')
      console.log('🔵 Verify token in localStorage:', verifyToken ? 'EXISTS ✅' : 'MISSING ❌')
      
      if (!verifyToken) {
        throw new Error('Failed to save token to localStorage - browser may be blocking storage')
      }
      
      // Fetch user profile to verify token works
      console.log('🔵 Fetching user profile...')
      try {
        const userResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
          headers: {
            'Authorization': `Bearer ${data.access_token}`
          }
        })
        
        console.log('🔵 User profile response:', userResponse.status)
        
        if (userResponse.ok) {
          const userData = await userResponse.json()
          console.log('✅ User profile loaded:', userData.email, 'Role:', userData.role)
        } else {
          const errorData = await userResponse.json()
          console.error('❌ Failed to load user profile:', errorData)
        }
      } catch (err) {
        console.error('❌ Error fetching user profile:', err)
      }
      
      toast.success('Successfully signed in with Google! Redirecting...')
      console.log('🔵 Redirecting to dashboard in 1 second...')
      
      // Force full page reload to reinitialize AuthContext with new token
      setTimeout(() => {
        console.log('🔵 Executing redirect now...')
        window.location.href = '/dashboard'
      }, 1000)
      
    } catch (error: any) {
      console.error('❌ Google auth error:', error)
      toast.error(error.message || 'Failed to sign in with Google')
    } finally {
      setIsLoading(false)
    }
  }

  const handleGoogleError = () => {
    toast.error('Google sign-in failed. Please try again.')
  }

  return (
    <>
      <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="form-label">
                Email
              </label>
              <input
                {...register('email')}
                type="email"
                id="email"
                name="email"
                autoComplete="email"
                className="form-input"
                placeholder="Enter your email"
              />
              {errors.email && (
                <p className="form-error">{errors.email.message}</p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="form-label">
                Password
              </label>
              <div className="relative">
                <input
                  {...register('password')}
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  autoComplete="current-password"
                  className="form-input pr-10"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
              {errors.password && (
                <p className="form-error">{errors.password.message}</p>
              )}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-sm">
              <Link href="/auth/forgot-password" className="font-medium text-primary-600 hover:text-primary-500">
                Forgot your password?
              </Link>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                'Sign In'
              )}
            </button>
          </div>
      </form>

      {/* Google OAuth Section - Only show if configured */}
      {isGoogleConfigured ? (
        <>
          {/* Divider */}
          <div className="relative mt-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-dark-800 text-gray-400">Or continue with</span>
            </div>
          </div>

          {/* Google Sign-In Button */}
          <div className="mt-6 flex justify-center">
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              useOneTap
              text="signin_with"
              size="large"
              width="100%"
            />
          </div>
        </>
      ) : (
        <div className="mt-6 p-4 bg-yellow-900/20 border border-yellow-500/30 rounded-lg text-center text-sm text-yellow-400">
          ⚠️ Google OAuth not configured. Check console for details.
        </div>
      )}
    </>
  )
}

