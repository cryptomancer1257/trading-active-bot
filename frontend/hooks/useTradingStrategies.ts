import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface TradingStrategy {
  id: number
  template_id: string
  title: string
  category: string
  timeframe?: string
  win_rate_estimate?: string
  prompt: string
  risk_management?: string
  best_for?: string
  metadata?: any
  created_at?: string
}

export interface TradingStrategyCategory {
  id: number
  category_name: string
  description?: string
  parent_category?: string
  template_count: number
  display_order: number
}

// Get all trading strategy templates
export const useTradingStrategies = (params?: {
  category?: string
  search?: string
  timeframe?: string
  min_win_rate?: number
  skip?: number
  limit?: number
}) => {
  return useQuery({
    queryKey: ['tradingStrategies', params],
    queryFn: async () => {
      const response = await api.get('/prompts/templates', { params })
      return response.data as TradingStrategy[]
    },
  })
}

// Get single trading strategy
export const useTradingStrategy = (templateId: string) => {
  return useQuery({
    queryKey: ['tradingStrategy', templateId],
    queryFn: async () => {
      const response = await api.get(`/prompts/templates/${templateId}`)
      return response.data as TradingStrategy
    },
    enabled: !!templateId,
  })
}

// Get all categories
export const useTradingStrategyCategories = () => {
  return useQuery({
    queryKey: ['tradingStrategyCategories'],
    queryFn: async () => {
      const response = await api.get('/prompts/categories')
      return response.data as TradingStrategyCategory[]
    },
  })
}

