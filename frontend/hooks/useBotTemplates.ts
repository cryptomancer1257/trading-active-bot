import { useQuery } from '@tanstack/react-query'
import config from '../lib/config'
// import { Bot } from '@/lib/types'
interface Bot {
  id: number;
  name: string;
  description: string;
  bot_type: string;
  exchange_type: string;
}

interface BotTemplatesResponse {
  templates: Bot[]
  total: number
}

export const useBotTemplates = (params?: {
  skip?: number
  limit?: number
  bot_type?: string
  exchange_type?: string
}) => {
  return useQuery<BotTemplatesResponse>({
    queryKey: ['bot-templates', params],
    queryFn: async () => {
      const searchParams = new URLSearchParams()
      
      if (params?.skip) searchParams.append('skip', params.skip.toString())
      if (params?.limit) searchParams.append('limit', params.limit.toString())
      if (params?.bot_type) searchParams.append('bot_type', params.bot_type)
      if (params?.exchange_type) searchParams.append('exchange_type', params.exchange_type)
      
      const response = await fetch(`${config.apiUrl}/bots/templates?${searchParams.toString()}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch bot templates')
      }
      
      const templates = await response.json()
      
      return {
        templates,
        total: templates.length
      }
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}

export const useBotTemplate = (templateId: number) => {
  return useQuery<Bot>({
    queryKey: ['bot-template', templateId],
    queryFn: async () => {
      const response = await fetch(`${config.apiUrl}/bots/${templateId}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch bot template')
      }
      
      return response.json()
    },
    enabled: !!templateId,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
  })
}
