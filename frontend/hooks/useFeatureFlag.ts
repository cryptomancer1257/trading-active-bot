import { useQuery } from '@tanstack/react-query'
import api from '@/lib/api'

export interface FeatureFlag {
  flag_key: string
  is_enabled: boolean
}

/**
 * Hook to check if a feature flag is enabled
 * @param flagKey - The feature flag key to check
 * @returns {boolean} - Whether the feature is enabled
 */
export function useFeatureFlag(flagKey: string): boolean {
  const { data } = useQuery({
    queryKey: ['feature-flag', flagKey],
    queryFn: async () => {
      const response = await api.get(`/feature-flags/check/${flagKey}`)
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })

  return data?.is_enabled ?? false
}

/**
 * Hook to get all enabled feature flags
 * @returns {string[]} - Array of enabled feature flag keys
 */
export function useFeatureFlags() {
  const { data, isLoading } = useQuery({
    queryKey: ['feature-flags'],
    queryFn: async () => {
      const response = await api.get('/feature-flags/public')
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })

  const enabledFlags = (data || []).map((flag: FeatureFlag) => flag.flag_key)

  return {
    isEnabled: (flagKey: string) => enabledFlags.includes(flagKey),
    enabledFlags,
    isLoading,
  }
}

/**
 * Feature flag keys used in the application
 */
export const FEATURE_FLAGS = {
  MARKETPLACE_PUBLISH_BOT: 'marketplace_publish_bot',
  MARKETPLACE_REPUBLISH_BOT: 'marketplace_republish_bot',
  LLM_QUOTA_SYSTEM: 'llm_quota_system',
  ADVANCED_ANALYTICS: 'advanced_analytics',
  MULTI_EXCHANGE_TRADING: 'multi_exchange_trading',
} as const

