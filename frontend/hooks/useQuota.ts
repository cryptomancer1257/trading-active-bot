import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface QuotaUsage {
  total: number
  used: number
  remaining: number
  percentage: number
  reset_at: string | null
  plan_name: string
  can_purchase: boolean
}

export interface QuotaPackage {
  name: string
  quota: number
  price: number
  description: string
  icon: string
}

export interface QuotaPackages {
  packages: Record<string, QuotaPackage>
  currency: string
}

export interface QuotaTopUpHistory {
  topups: Array<{
    id: number
    quota_amount: number
    price_usd: number
    payment_method: string
    payment_status: string
    created_at: string
    applied_at: string | null
  }>
  total_purchased: number
  total_spent: number
}

export interface CreatePayPalOrderRequest {
  package: string
}

export interface CreatePayPalOrderResponse {
  order_id: string
  approve_url: string
  package: QuotaPackage
  amount: number
}

export interface PurchaseQuotaRequest {
  package: string
  payment_id: string
}

export interface PurchaseQuotaResponse {
  success: boolean
  message: string
  quota_added: number
  new_total: number
  remaining: number
}

// Hook for getting quota usage
export function useQuotaUsage() {
  return useQuery<QuotaUsage>({
    queryKey: ['quota-usage'],
    queryFn: async () => {
      console.log('🔐 Fetching quota usage from API')
      const response = await api.get('/quota-topups/usage')
      console.log('📊 Quota usage response:', response.data)
      return response.data
    },
    staleTime: 0, // Always fetch fresh data
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3, // Retry 3 times on failure
  })
}

// Hook for getting quota packages
export function useQuotaPackages() {
  return useQuery<QuotaPackages>({
    queryKey: ['quota-packages'],
    queryFn: async () => {
      try {
        const response = await api.get('/quota-topups/packages')
        console.log('📦 Quota packages response:', response.data)
        return response.data
      } catch (error: any) {
        console.error('❌ Failed to fetch quota packages:', error)
        throw error
      }
    },
    staleTime: 300000, // 5 minutes
    retry: 3, // Retry 3 times on failure
    retryDelay: 1000, // 1 second delay between retries
  })
}

// Hook for getting quota top-up history
export function useQuotaHistory() {
  return useQuery<QuotaTopUpHistory>({
    queryKey: ['quota-history'],
    queryFn: async () => {
      const response = await api.get('/quota-topups/history')
      return response.data
    },
    staleTime: 60000, // 1 minute
  })
}

// Hook for creating PayPal order
export function useCreatePayPalOrder() {
  const queryClient = useQueryClient()
  
  return useMutation<CreatePayPalOrderResponse, Error, CreatePayPalOrderRequest>({
    mutationFn: async (data) => {
      // Check if we're in demo mode (no authentication)
      const isDemoMode = !localStorage.getItem('access_token') || localStorage.getItem('access_token') === 'null'
      
      if (isDemoMode) {
        console.log('🎭 Demo mode: Using demo PayPal endpoint')
        const response = await api.post('/quota-topups/create-paypal-order-demo', data)
        return response.data
      } else {
        console.log('🔐 Auth mode: Using real PayPal endpoint')
        const response = await api.post('/quota-topups/create-paypal-order', data)
        return response.data
      }
    },
    onSuccess: () => {
      // Invalidate quota usage to refresh data
      queryClient.invalidateQueries({ queryKey: ['quota-usage'] })
    },
  })
}

// Hook for purchasing quota
export function usePurchaseQuota() {
  const queryClient = useQueryClient()
  
  return useMutation<PurchaseQuotaResponse, Error, PurchaseQuotaRequest>({
    mutationFn: async (data) => {
      const response = await api.post('/quota-topups/purchase', data)
      return response.data
    },
    onSuccess: () => {
      // Invalidate quota usage and history
      queryClient.invalidateQueries({ queryKey: ['quota-usage'] })
      queryClient.invalidateQueries({ queryKey: ['quota-history'] })
    },
  })
}
