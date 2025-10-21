/**
 * Hook to fetch dynamic plan pricing from API
 * Includes support for discounts and campaign pricing
 */

import { useState, useEffect } from 'react'
import { config } from '@/lib/config'

export interface PlanPricing {
  id: number
  plan_name: string
  original_price_usd: number
  discount_percentage: number
  current_price_usd: number
  campaign_name?: string | null
  campaign_active: boolean
  campaign_start_date?: string | null
  campaign_end_date?: string | null
  created_at: string
  updated_at: string
}

export interface PlanPricingMap {
  free?: PlanPricing
  pro?: PlanPricing
  ultra?: PlanPricing
}

export function usePlanPricing() {
  const [pricings, setPricings] = useState<PlanPricingMap>({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    fetchPricings()
  }, [])

  const fetchPricings = async () => {
    try {
      setIsLoading(true)
      const plans = ['free', 'pro', 'ultra']
      const results: PlanPricingMap = {}
      
      for (const planName of plans) {
        try {
          const response = await fetch(`${config.studioBaseUrl}/admin/plan-pricing/${planName}`)
          if (response.ok) {
            const data = await response.json()
            // Convert string prices to numbers
            results[planName as keyof PlanPricingMap] = {
              ...data,
              original_price_usd: parseFloat(data.original_price_usd) || 0,
              discount_percentage: parseFloat(data.discount_percentage) || 0,
              current_price_usd: parseFloat(data.current_price_usd) || 0
            }
          }
        } catch (err) {
          console.warn(`Failed to fetch ${planName} pricing:`, err)
        }
      }
      
      setPricings(results)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch pricing:', err)
      setError(err instanceof Error ? err : new Error('Unknown error'))
    } finally {
      setIsLoading(false)
    }
  }

  // Helper function to get price with fallback
  const getPrice = (planName: 'free' | 'pro' | 'ultra', type: 'current' | 'original' = 'current'): number => {
    const pricing = pricings[planName]
    if (!pricing) {
      // Fallback prices
      const fallbacks = {
        free: { current: 0, original: 0 },
        pro: { current: 20, original: 40 },
        ultra: { current: 50, original: 100 }
      }
      return fallbacks[planName][type]
    }
    return type === 'current' ? pricing.current_price_usd : pricing.original_price_usd
  }

  // Helper function to get discount percentage
  const getDiscount = (planName: 'free' | 'pro' | 'ultra'): number => {
    const pricing = pricings[planName]
    return pricing?.discount_percentage || 0
  }

  // Helper function to check if there's an active campaign
  const hasActiveDiscount = (planName: 'free' | 'pro' | 'ultra'): boolean => {
    const pricing = pricings[planName]
    return pricing?.campaign_active && pricing.discount_percentage > 0 || false
  }

  return {
    pricings,
    isLoading,
    error,
    getPrice,
    getDiscount,
    hasActiveDiscount,
    refetch: fetchPricings
  }
}

