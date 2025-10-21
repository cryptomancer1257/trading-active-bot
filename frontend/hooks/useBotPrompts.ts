import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'

// Types
export interface BotPrompt {
  id: number
  bot_id: number
  prompt_id: number
  is_active: boolean
  priority: number
  custom_override?: string
  attached_at: string
  created_at: string
  updated_at: string
  prompt_template: {
    id: number
    name: string
    description?: string
    content: string
    category: string
    is_active: boolean
    is_default: boolean
    created_at: string
    updated_at: string
  }
  bot: {
    id: number
    name: string
    description?: string
    bot_type: string
    status: string
  }
}

export interface AttachPromptRequest {
  priority?: number
  custom_override?: string
}

export interface UpdateBotPromptRequest {
  is_active?: boolean
  priority?: number
  custom_override?: string
}

// API functions
const API_BASE = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? window.location.origin : 'https://quantumforge.cryptomancer.ai')

const fetchBotPrompts = async (botId: number): Promise<BotPrompt[]> => {
  console.log(`🔍 Fetching bot prompts for bot ${botId} from ${API_BASE}/bot-prompts/bots/${botId}/prompts`)
  
  const token = localStorage.getItem('access_token')
  if (!token) {
    console.error('❌ No access token found')
    throw new Error('No access token found')
  }
  
  const response = await fetch(`${API_BASE}/bot-prompts/bots/${botId}/prompts`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  })
  
  if (!response.ok) {
    const errorText = await response.text()
    console.error(`❌ Failed to fetch bot prompts: ${response.status} ${response.statusText}`)
    console.error(`❌ Error details:`, errorText)
    
    if (response.status === 404) {
      throw new Error(`Bot ${botId} not found or you don't have access to it`)
    } else if (response.status === 403) {
      throw new Error(`You don't have permission to access bot ${botId}`)
    } else if (response.status === 401) {
      throw new Error('Authentication required - please login again')
    }
    
    throw new Error(`Failed to fetch bot prompts: ${response.status} ${response.statusText}`)
  }
  
  return response.json()
}

const fetchPromptBots = async (promptId: number): Promise<BotPrompt[]> => {
  const response = await fetch(`${API_BASE}/bot-prompts/prompts/${promptId}/bots`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
  })
  if (!response.ok) {
    throw new Error('Failed to fetch prompt bots')
  }
  return response.json()
}

const attachPromptToBot = async (botId: number, promptId: number, data: AttachPromptRequest): Promise<BotPrompt> => {
  const params = new URLSearchParams()
  if (data.priority !== undefined) params.append('priority', data.priority.toString())
  if (data.custom_override) params.append('custom_override', data.custom_override)

  const response = await fetch(`${API_BASE}/bot-prompts/bots/${botId}/prompts/${promptId}?${params}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
  })
  if (!response.ok) {
    throw new Error('Failed to attach prompt to bot')
  }
  return response.json()
}

const detachPromptFromBot = async (botId: number, promptId: number): Promise<void> => {
  const response = await fetch(`${API_BASE}/bot-prompts/bots/${botId}/prompts/${promptId}`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
  })
  if (!response.ok) {
    throw new Error('Failed to detach prompt from bot')
  }
}

const updateBotPrompt = async (botId: number, promptId: number, data: UpdateBotPromptRequest): Promise<BotPrompt> => {
  const response = await fetch(`${API_BASE}/bot-prompts/bots/${botId}/prompts/${promptId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    throw new Error('Failed to update bot prompt')
  }
  return response.json()
}

const fetchSuggestedPrompts = async (botId: number, limit: number = 10): Promise<any[]> => {
  const response = await fetch(`${API_BASE}/bot-prompts/bots/${botId}/suggested-prompts?limit=${limit}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
  })
  if (!response.ok) {
    throw new Error('Failed to fetch suggested prompts')
  }
  return response.json()
}

const fetchSuggestedBots = async (promptId: number, limit: number = 10): Promise<any[]> => {
  const response = await fetch(`${API_BASE}/bot-prompts/prompts/${promptId}/suggested-bots?limit=${limit}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
  })
  if (!response.ok) {
    throw new Error('Failed to fetch suggested bots')
  }
  return response.json()
}

// React Query hooks
export const useBotPrompts = (botId: number) => {
  return useQuery({
    queryKey: ['botPrompts', botId],
    queryFn: () => fetchBotPrompts(botId),
    enabled: !!botId,
  })
}

export const usePromptBots = (promptId: number) => {
  return useQuery({
    queryKey: ['promptBots', promptId],
    queryFn: () => fetchPromptBots(promptId),
    enabled: !!promptId,
  })
}

export const useAttachPrompt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ botId, promptId, data }: { botId: number; promptId: number; data: AttachPromptRequest }) =>
      attachPromptToBot(botId, promptId, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['botPrompts', variables.botId] })
      queryClient.invalidateQueries({ queryKey: ['promptBots', variables.promptId] })
      queryClient.invalidateQueries({ queryKey: ['suggestedPrompts', variables.botId] })
      toast.success('Prompt attached successfully!')
    },
    onError: () => {
      toast.error('Failed to attach prompt. Please try again.')
    },
  })
}

export const useDetachPrompt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ botId, promptId }: { botId: number; promptId: number }) =>
      detachPromptFromBot(botId, promptId),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['botPrompts', variables.botId] })
      queryClient.invalidateQueries({ queryKey: ['promptBots', variables.promptId] })
      queryClient.invalidateQueries({ queryKey: ['suggestedPrompts', variables.botId] })
      toast.success('Prompt detached successfully!')
    },
    onError: () => {
      toast.error('Failed to detach prompt. Please try again.')
    },
  })
}

export const useUpdateBotPrompt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ botId, promptId, data }: { botId: number; promptId: number; data: UpdateBotPromptRequest }) =>
      updateBotPrompt(botId, promptId, data),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['botPrompts', variables.botId] })
      queryClient.invalidateQueries({ queryKey: ['promptBots', variables.promptId] })
      toast.success('Bot prompt updated successfully!')
    },
    onError: () => {
      toast.error('Failed to update bot prompt. Please try again.')
    },
  })
}

export const useSuggestedPrompts = (botId: number, limit: number = 10) => {
  return useQuery({
    queryKey: ['suggestedPrompts', botId, limit],
    queryFn: () => fetchSuggestedPrompts(botId, limit),
    enabled: !!botId,
  })
}

export const useSuggestedBots = (promptId: number, limit: number = 10) => {
  return useQuery({
    queryKey: ['suggestedBots', promptId, limit],
    queryFn: () => fetchSuggestedBots(promptId, limit),
    enabled: !!promptId,
  })
}
