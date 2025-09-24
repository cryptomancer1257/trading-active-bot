'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, LoginRequest, UserCreate } from '@/lib/types'
import api from '@/lib/api'
import toast from 'react-hot-toast'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (credentials: LoginRequest) => Promise<boolean>
  register: (userData: UserCreate) => Promise<boolean>
  logout: () => void
  updateProfile: (userData: Partial<User>) => Promise<boolean>
  refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastAuthCheck, setLastAuthCheck] = useState<number>(0)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async (force: boolean = false) => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        console.log('No token found, user not authenticated')
        setLoading(false)
        return
      }

      // Prevent too frequent auth checks (max once per 60 seconds)
      const now = Date.now()
      const timeSinceLastCheck = now - lastAuthCheck
      if (!force && timeSinceLastCheck < 60000 && user) {
        console.log('⏰ Skipping auth check - too recent (', Math.round(timeSinceLastCheck / 1000), 's ago)')
        setLoading(false)
        return
      }

      console.log('🔐 Checking auth with token:', token.substring(0, 20) + '...')
      const response = await api.get('/auth/me')
      console.log('✅ Auth check successful:', response.data)
      setUser(response.data)
      setLastAuthCheck(now)
    } catch (error: any) {
      console.error('❌ Auth check failed:', error)
      console.error('Auth error response:', error.response?.data)
      
      // Only remove token if it's actually invalid (401), not for network errors
      if (error.response?.status === 401) {
        localStorage.removeItem('access_token')
        setUser(null)
        setLastAuthCheck(0)
      }
    } finally {
      setLoading(false)
    }
  }

  const login = async (credentials: LoginRequest): Promise<boolean> => {
    try {
      const formData = new FormData()
      formData.append('username', credentials.username)
      formData.append('password', credentials.password)

      console.log('Attempting login with:', credentials.username)
      const response = await api.post('/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      console.log('Login response status:', response.status)
      console.log('Login response data:', response.data)
      
      const { access_token, token_type } = response.data
      
      if (!access_token) {
        console.error('No access token in response')
        throw new Error('No access token received')
      }
      
      localStorage.setItem('access_token', access_token)
      console.log('Token saved to localStorage:', access_token.substring(0, 20) + '...')
      
      try {
        // Get user profile
        console.log('Fetching user profile...')
        const userResponse = await api.get('/auth/me', {
          headers: {
            'Authorization': `Bearer ${access_token}`
          }
        })
        console.log('User profile response status:', userResponse.status)
        console.log('User profile data:', userResponse.data)
        setUser(userResponse.data)
        
        toast.success('Login successful!')
        return true
      } catch (profileError: any) {
        console.error('Profile fetch error:', profileError)
        console.error('Profile error response:', profileError.response?.data)
        
        // Even if profile fetch fails, login was successful
        // We'll set a basic user object
        setUser({
          id: 0,
          email: credentials.username,
          role: 'USER' as any,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        })
        
        toast.success('Login successful! (Profile loading failed)')
        return true
      }
      
    } catch (error: any) {
      console.error('Login error:', error)
      console.error('Error response data:', error.response?.data)
      console.error('Error response status:', error.response?.status)
      
      // Remove token if login failed
      localStorage.removeItem('access_token')
      
      let message = 'Login failed'
      if (error.response?.status === 401) {
        message = 'Invalid email or password'
      } else if (error.response?.data?.detail) {
        message = error.response.data.detail
      } else if (error.message) {
        message = error.message
      }
      
      toast.error(message)
      return false
    }
  }

  const register = async (userData: UserCreate): Promise<boolean> => {
    try {
      const response = await api.post('/auth/register', userData)
      toast.success('Registration successful! Please login.')
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Registration failed'
      toast.error(message)
      return false
    }
  }

  const logout = () => {
    console.log('Logging out user')
    localStorage.removeItem('access_token')
    setUser(null)
    toast.success('Logged out successfully')
  }

  const refreshAuth = async () => {
    console.log('🔄 Refreshing auth state...')
    await checkAuth(false) // Don't force, respect cooldown
  }

  const updateProfile = async (userData: Partial<User>): Promise<boolean> => {
    try {
      const response = await api.put('/auth/me', userData)
      setUser(response.data)
      toast.success('Profile updated successfully!')
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Update failed'
      toast.error(message)
      return false
    }
  }

  return (
    <AuthContext.Provider value={{
      user,
      loading,
      login,
      register,
      logout,
      updateProfile,
      refreshAuth,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

