import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
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
      const response = await api.get('/api/plans/current')
      return response.data
    },
    enabled: !!token, // Only fetch if logged in
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false, // Don't retry on 401
  })

  // Get plan configs
  const { data: planConfigs } = useQuery<PlanConfigsResponse>({
    queryKey: ['plan-configs'],
    queryFn: async () => {
      const response = await api.get('/api/plans/config')
      return response.data
    },
    staleTime: 60 * 60 * 1000, // 1 hour
  })

  // Get usage limits
  const { data: limits, isLoading: isLoadingLimits } = useQuery<PlanLimits>({
    queryKey: ['plan-limits'],
    queryFn: async () => {
      const response = await api.get('/api/plans/limits')
      return response.data
    },
    enabled: !!token, // Only fetch if logged in
    staleTime: 1 * 60 * 1000, // 1 minute
    retry: false, // Don't retry on 401
  })

  // Upgrade to Pro mutation
  const upgradeToPro = useMutation({
    mutationFn: async (paymentId: string) => {
      const response = await api.post('/api/plans/upgrade', {
        payment_id: paymentId,
        payment_method: 'paypal',
        auto_renew: true
      })
      return response.data
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
      const response = await api.post('/api/plans/cancel')
      return response.data
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

