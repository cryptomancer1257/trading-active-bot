import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

// Types
export interface ExchangeCredentials {
  id: number
  user_id: number
  exchange_type: 'BINANCE' | 'COINBASE' | 'KRAKEN' | 'BYBIT' | 'HUOBI'
  credential_type: 'SPOT' | 'FUTURES' | 'MARGIN'
  network_type: 'TESTNET' | 'MAINNET'
  name: string
  is_default: boolean
  is_active: boolean
  last_used_at?: string
  created_at: string
  updated_at: string
}

export interface ExchangeCredentialsWithSecrets extends ExchangeCredentials {
  api_key: string
  api_secret: string
  passphrase?: string
}

export interface CreateCredentialsData {
  exchange_type: 'BINANCE' | 'COINBASE' | 'KRAKEN' | 'BYBIT' | 'HUOBI'
  credential_type: 'SPOT' | 'FUTURES' | 'MARGIN'
  network_type: 'TESTNET' | 'MAINNET'
  name: string
  api_key: string
  api_secret: string
  passphrase?: string
  is_default?: boolean
  is_active?: boolean
}

export interface UpdateCredentialsData {
  name?: string
  api_key?: string
  api_secret?: string
  passphrase?: string
  is_default?: boolean
  is_active?: boolean
}

// Hooks
export const useCredentials = () => {
  return useQuery<ExchangeCredentials[]>({
    queryKey: ['credentials'],
    queryFn: async () => {
      const response = await api.get('/developer/credentials/')
      return response.data
    }
  })
}

export const useCredentialsWithSecrets = (credentialsId: number) => {
  return useQuery<ExchangeCredentialsWithSecrets>({
    queryKey: ['credentials', credentialsId, 'secrets'],
    queryFn: async () => {
      const response = await api.get(`/developer/credentials/${credentialsId}`)
      return response.data
    },
    enabled: !!credentialsId
  })
}

export const useDefaultCredentials = (
  exchangeType: string, 
  credentialType: string, 
  networkType: string,
  enabled: boolean = true
) => {
  return useQuery<ExchangeCredentialsWithSecrets | null>({
    queryKey: ['credentials', 'default', exchangeType, credentialType, networkType],
    queryFn: async () => {
      const response = await api.get(`/developer/credentials/default/${exchangeType}/${credentialType}/${networkType}`)
      return response.data
    },
    enabled: enabled && !!exchangeType && !!credentialType && !!networkType
  })
}

export const useCreateCredentials = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (data: CreateCredentialsData) => {
      const response = await api.post('/developer/credentials/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
    }
  })
}

export const useUpdateCredentials = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: UpdateCredentialsData }) => {
      const response = await api.put(`/developer/credentials/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
    }
  })
}

export const useDeleteCredentials = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.delete(`/developer/credentials/${id}`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
    }
  })
}

export const useMarkCredentialsUsed = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post(`/developer/credentials/${id}/mark-used`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['credentials'] })
    }
  })
}
