import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '@/lib/api'

export interface Bot {
  id: number
  name: string
  description: string
  bot_type: string
  bot_mode: string
  status: string
  exchange_type: string
  trading_pair: string
  timeframe: string
  version: string
  created_at: string
  updated_at: string
  total_subscribers: number
  average_rating: number
  developer_id: number
  category_id?: number
  image_url?: string
  // Advanced config
  leverage?: number
  risk_percentage?: number
  stop_loss_percentage?: number
  take_profit_percentage?: number
}

export interface CreateBotRequest {
  name: string
  description: string
  bot_type: string
  bot_mode: string
  exchange_type: string
  trading_pair: string
  timeframe: string
  timeframes: string[]
  version: string
  template: string
  templateFile?: string // Template file name to copy
  leverage?: number
  risk_percentage?: number
  stop_loss_percentage?: number
  take_profit_percentage?: number
  llm_provider?: string
  enable_image_analysis?: boolean
  enable_sentiment_analysis?: boolean
}

// Get user's bots
export const useMyBots = () => {
  return useQuery<Bot[]>({
    queryKey: ['myBots'],
    queryFn: async () => {
      const response = await api.get('/bots/me/bots')
      return response.data || []  // This endpoint returns direct array
    },
    staleTime: 30 * 1000, // 30 seconds (shorter for fresh data)
    gcTime: 5 * 60 * 1000, // 5 minutes (renamed from cacheTime in v4)
    refetchOnWindowFocus: true, // Refetch when user comes back to tab
    refetchOnMount: true, // Always refetch on component mount
  })
}

// Get all public bots
export const usePublicBots = () => {
  return useQuery<Bot[]>({
    queryKey: ['publicBots'],
    queryFn: async () => {
      const response = await api.get('/bots')
      return response.data.bots || []  // Extract bots array from response
    },
    staleTime: 5 * 60 * 1000,
  })
}

// Get single bot by ID
export const useGetBot = (botId: string | number) => {
  return useQuery<Bot>({
    queryKey: ['bot', botId],
    queryFn: async () => {
      const response = await api.get(`/bots/${botId}`)
      return response.data
    },
    enabled: !!botId,
    staleTime: 5 * 60 * 1000,
  })
}

// Create new bot
export const useCreateBot = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (botData: CreateBotRequest) => {
      const response = await api.post('/bots/', botData)
      return response.data
    },
    onSuccess: () => {
      // Force invalidate and refetch immediately
      queryClient.invalidateQueries({ queryKey: ['myBots'] })
      queryClient.invalidateQueries({ queryKey: ['publicBots'] })
      // Force refetch myBots immediately
      queryClient.refetchQueries({ queryKey: ['myBots'] })
      console.log('✅ Bot created successfully - cache invalidated and refetched')
    },
  })
}

// Update bot
export const useUpdateBot = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ botId, data }: { botId: number; data: Partial<CreateBotRequest> }) => {
      const response = await api.put(`/bots/${botId}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myBots'] })
      queryClient.invalidateQueries({ queryKey: ['publicBots'] })
    },
  })
}

// Delete bot
export const useDeleteBot = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (botId: number) => {
      await api.delete(`/bots/${botId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myBots'] })
      queryClient.invalidateQueries({ queryKey: ['publicBots'] })
    },
  })
}