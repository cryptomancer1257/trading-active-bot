import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import config from '@/lib/config'
import type { UserPlan, PlanConfig, PlanLimits } from '@/types/plan'

interface PlanConfigsResponse {
  free: PlanConfig
  pro: PlanConfig
}

export const usePlan = () => {
  const queryClient = useQueryClient()
  
  // Check if user is logged in
  const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null

  // Get current plan
  const { data: currentPlan, isLoading: isLoadingPlan, error: planError } = useQuery<UserPlan>({
    queryKey: ['current-plan'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${config.studioBaseUrl}/api/plans/current`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch current plan')
      }
      
      return response.json()
    },
    enabled: !!token, // Only fetch if logged in
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  // Get plan configs
  const { data: planConfigs } = useQuery<PlanConfigsResponse>({
    queryKey: ['plan-configs'],
    queryFn: async () => {
      const response = await fetch(`${config.studioBaseUrl}/api/plans/config`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch plan configs')
      }
      
      return response.json()
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  })

  // Get usage limits
  const { data: limits, isLoading: isLoadingLimits } = useQuery<PlanLimits>({
    queryKey: ['plan-limits'],
    queryFn: async () => {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${config.studioBaseUrl}/api/plans/limits`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch plan limits')
      }
      
      return response.json()
    },
    enabled: !!token, // Only fetch if logged in
    staleTime: 1 * 60 * 1000, // 1 minute
  })

  // Upgrade to Pro mutation
  const upgradeToPro = useMutation({
    mutationFn: async (paymentId: string) => {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${config.studioBaseUrl}/api/plans/upgrade`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          payment_id: paymentId,
          payment_method: 'paypal',
          auto_renew: true
        })
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to upgrade plan')
      }
      
      return response.json()
    },
    onSuccess: () => {
      // Invalidate queries to refetch updated data
      queryClient.invalidateQueries({ queryKey: ['current-plan'] })
      queryClient.invalidateQueries({ queryKey: ['plan-limits'] })
    }
  })

  // Cancel Pro plan mutation
  const cancelPlan = useMutation({
    mutationFn: async () => {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`${config.studioBaseUrl}/api/plans/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to cancel plan')
      }
      
      return response.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['current-plan'] })
      queryClient.invalidateQueries({ queryKey: ['plan-limits'] })
    }
  })

  return {
    currentPlan,
    isLoadingPlan,
    planError,
    planConfigs,
    limits,
    isLoadingLimits,
    upgradeToPro,
    cancelPlan,
    isPro: currentPlan?.plan_name === 'pro',
    isFree: currentPlan?.plan_name === 'free'
  }
}

