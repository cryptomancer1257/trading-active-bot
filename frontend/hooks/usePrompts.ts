import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

export interface PromptTemplate {
  id: number
  name: string
  description?: string
  content: string
  category: 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT'
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
  created_by: number
}

export interface CreatePromptRequest {
  name: string
  description?: string
  content: string
  category: 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT'
  is_active?: boolean
  is_default?: boolean
}

export interface UpdatePromptRequest {
  name?: string
  description?: string
  content?: string
  category?: 'TRADING' | 'ANALYSIS' | 'RISK_MANAGEMENT'
  is_active?: boolean
  is_default?: boolean
}

// Get all prompt templates
export const usePrompts = (params?: {
  skip?: number
  limit?: number
  category?: string
  is_active?: boolean
}) => {
  return useQuery({
    queryKey: ['prompts', params],
    queryFn: async () => {
      const response = await api.get('/prompts/', { params })
      return response.data as PromptTemplate[]
    },
  })
}

// Get my prompt templates (developer only)
export const useMyPrompts = (params?: {
  skip?: number
  limit?: number
}) => {
  return useQuery({
    queryKey: ['myPrompts', params],
    queryFn: async () => {
      const response = await api.get('/prompts/my', { params })
      return response.data as PromptTemplate[]
    },
  })
}

// Get default prompt template by category
export const useDefaultPrompt = (category: string) => {
  return useQuery({
    queryKey: ['defaultPrompt', category],
    queryFn: async () => {
      const response = await api.get(`/prompts/default/${category}`)
      return response.data as PromptTemplate
    },
    enabled: !!category,
  })
}

// Get single prompt template
export const usePrompt = (promptId: number) => {
  return useQuery({
    queryKey: ['prompt', promptId],
    queryFn: async () => {
      const response = await api.get(`/prompts/${promptId}`)
      return response.data as PromptTemplate
    },
    enabled: !!promptId,
  })
}

// Create prompt template
export const useCreatePrompt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: CreatePromptRequest) => {
      const response = await api.post('/prompts/', data)
      return response.data as PromptTemplate
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      queryClient.invalidateQueries({ queryKey: ['myPrompts'] })
    },
  })
}

// Update prompt template
export const useUpdatePrompt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ promptId, data }: { promptId: number; data: UpdatePromptRequest }) => {
      console.log('🔄 Updating prompt:', { promptId, data })
      const response = await api.put(`/prompts/${promptId}`, data)
      console.log('✅ Update response:', response.data)
      return response.data as PromptTemplate
    },
    onSuccess: (data, variables) => {
      // Invalidate all prompt-related queries
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      queryClient.invalidateQueries({ queryKey: ['myPrompts'] })
      queryClient.invalidateQueries({ queryKey: ['prompt', variables.promptId] })
      
      // Also refetch the specific prompt to ensure fresh data
      queryClient.refetchQueries({ queryKey: ['prompt', variables.promptId] })
    },
  })
}

// Delete prompt template
export const useDeletePrompt = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (promptId: number) => {
      await api.delete(`/prompts/${promptId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['prompts'] })
      queryClient.invalidateQueries({ queryKey: ['myPrompts'] })
    },
  })
}
