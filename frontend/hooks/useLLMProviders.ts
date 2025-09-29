'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { 
  LLMProvider, 
  LLMProviderCreate, 
  LLMProviderUpdate,
  LLMModel,
  LLMModelCreate,
  LLMModelUpdate
} from '@/lib/types'

// LLM Provider Hooks
export const useLLMProviders = () => {
  return useQuery<LLMProvider[]>({
    queryKey: ['llm-providers'],
    queryFn: async () => {
      const response = await api.get('/developer/llm-providers/')
      return response.data
    }
  })
}

export const useLLMProvider = (providerId: number) => {
  return useQuery<LLMProvider>({
    queryKey: ['llm-provider', providerId],
    queryFn: async () => {
      const response = await api.get(`/developer/llm-providers/${providerId}`)
      return response.data
    },
    enabled: !!providerId
  })
}

export const useCreateLLMProvider = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: LLMProviderCreate) => {
      const response = await api.post('/developer/llm-providers/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    }
  })
}

export const useUpdateLLMProvider = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ providerId, data }: { providerId: number, data: LLMProviderUpdate }) => {
      const response = await api.put(`/developer/llm-providers/${providerId}`, data)
      return response.data
    },
    onSuccess: (_, { providerId }) => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
      queryClient.invalidateQueries({ queryKey: ['llm-provider', providerId] })
    }
  })
}

export const useDeleteLLMProvider = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (providerId: number) => {
      await api.delete(`/developer/llm-providers/${providerId}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    }
  })
}

// LLM Model Hooks
export const useLLMModels = (providerId: number) => {
  return useQuery<LLMModel[]>({
    queryKey: ['llm-models', providerId],
    queryFn: async () => {
      const response = await api.get(`/developer/llm-providers/${providerId}/models`)
      return response.data
    },
    enabled: !!providerId
  })
}

export const useCreateLLMModel = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ providerId, data }: { providerId: number, data: LLMModelCreate }) => {
      const response = await api.post(`/developer/llm-providers/${providerId}/models`, data)
      return response.data
    },
    onSuccess: (_, { providerId }) => {
      queryClient.invalidateQueries({ queryKey: ['llm-models', providerId] })
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    }
  })
}

export const useUpdateLLMModel = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ providerId, modelId, data }: { 
      providerId: number, 
      modelId: number, 
      data: LLMModelUpdate 
    }) => {
      const response = await api.put(`/developer/llm-providers/${providerId}/models/${modelId}`, data)
      return response.data
    },
    onSuccess: (_, { providerId }) => {
      queryClient.invalidateQueries({ queryKey: ['llm-models', providerId] })
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    }
  })
}

export const useDeleteLLMModel = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ providerId, modelId }: { providerId: number, modelId: number }) => {
      await api.delete(`/developer/llm-providers/${providerId}/models/${modelId}`)
    },
    onSuccess: (_, { providerId }) => {
      queryClient.invalidateQueries({ queryKey: ['llm-models', providerId] })
      queryClient.invalidateQueries({ queryKey: ['llm-providers'] })
    }
  })
}

// Utility hooks
export const useDefaultLLMProvider = () => {
  const { data: providers } = useLLMProviders()
  return providers?.find(p => p.is_default && p.is_active)
}

export const useActiveLLMProviders = () => {
  const { data: providers } = useLLMProviders()
  return providers?.filter(p => p.is_active) || []
}
