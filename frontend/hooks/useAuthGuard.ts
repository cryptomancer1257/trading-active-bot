'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import toast from 'react-hot-toast'

interface UseAuthGuardOptions {
  redirectTo?: string
  requireAuth?: boolean
  requiredRole?: string
}

export function useAuthGuard(options: UseAuthGuardOptions = {}) {
  const { 
    redirectTo = '/auth/login',
    requireAuth = true,
    requiredRole
  } = options
  
  const { user, loading, refreshAuth } = useAuth()
  const router = useRouter()

  useEffect(() => {
    // Don't do anything while loading
    if (loading) return

    console.log('AuthGuard check:', { user: !!user, requireAuth, requiredRole })

    // Refresh auth state on mount
    if (requireAuth) {
      refreshAuth()
    }

    // If auth is required but user is not logged in
    if (requireAuth && !user) {
      console.log('AuthGuard: User not authenticated, redirecting to:', redirectTo)
      toast.error('Please log in to access this page')
      router.push(redirectTo)
      return
    }

    // If specific role is required
    if (user && requiredRole && user.role !== requiredRole) {
      console.log('AuthGuard: Insufficient permissions, user role:', user.role, 'required:', requiredRole)
      toast.error('You do not have permission to access this page')
      router.push('/dashboard')
      return
    }

  }, [user, loading, requireAuth, requiredRole, redirectTo, router, refreshAuth])

  return {
    user,
    loading,
    isAuthenticated: !!user,
    hasRequiredRole: !requiredRole || (user && user.role === requiredRole)
  }
}
