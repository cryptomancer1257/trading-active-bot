'use client'

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole, LLMProviderType, LLMProvider, LLMModel } from '@/lib/types'
import { 
  useLLMProviders, 
  useCreateLLMProvider, 
  useUpdateLLMProvider, 
  useDeleteLLMProvider,
  useCreateLLMModel,
  useUpdateLLMModel,
  useDeleteLLMModel
} from '@/hooks/useLLMProviders'
import { 
  PlusIcon, 
  PencilIcon, 
  TrashIcon, 
  EyeIcon, 
  EyeSlashIcon,
  CpuChipIcon,
  SparklesIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

// Schemas
const llmProviderSchema = z.object({
  provider_type: z.nativeEnum(LLMProviderType),
  name: z.string().min(1, 'Name is required'),
  api_key: z.string().min(1, 'API Key is required'),
  base_url: z.string().url().optional().or(z.literal('')),
  is_active: z.boolean().default(true),
  is_default: z.boolean().default(false)
})

const llmModelSchema = z.object({
  model_name: z.string().min(1, 'Model name is required'),
  display_name: z.string().min(1, 'Display name is required'),
  is_active: z.boolean().default(true),
  max_tokens: z.number().min(1).optional(),
  cost_per_1k_tokens: z.number().min(0).optional()
})

type LLMProviderFormData = z.infer<typeof llmProviderSchema>
type LLMModelFormData = z.infer<typeof llmModelSchema>

// Default models for each provider
const defaultModels = {
  [LLMProviderType.OPENAI]: [
    { model_name: 'gpt-4o', display_name: 'GPT-4o', max_tokens: 128000, cost_per_1k_tokens: 0.005 },
    { model_name: 'gpt-4o-mini', display_name: 'GPT-4o Mini', max_tokens: 128000, cost_per_1k_tokens: 0.00015 },
    { model_name: 'gpt-4-turbo', display_name: 'GPT-4 Turbo', max_tokens: 128000, cost_per_1k_tokens: 0.01 },
    { model_name: 'gpt-3.5-turbo', display_name: 'GPT-3.5 Turbo', max_tokens: 16385, cost_per_1k_tokens: 0.0015 }
  ],
  [LLMProviderType.ANTHROPIC]: [
    { model_name: 'claude-3-5-sonnet-20241022', display_name: 'Claude 3.5 Sonnet', max_tokens: 200000, cost_per_1k_tokens: 0.003 },
    { model_name: 'claude-3-opus-20240229', display_name: 'Claude 3 Opus', max_tokens: 200000, cost_per_1k_tokens: 0.015 },
    { model_name: 'claude-3-haiku-20240307', display_name: 'Claude 3 Haiku', max_tokens: 200000, cost_per_1k_tokens: 0.00025 }
  ],
  [LLMProviderType.GEMINI]: [
    { model_name: 'gemini-1.5-pro', display_name: 'Gemini 1.5 Pro', max_tokens: 2097152, cost_per_1k_tokens: 0.00125 },
    { model_name: 'gemini-1.5-flash', display_name: 'Gemini 1.5 Flash', max_tokens: 1048576, cost_per_1k_tokens: 0.000075 },
    { model_name: 'gemini-pro', display_name: 'Gemini Pro', max_tokens: 32768, cost_per_1k_tokens: 0.0005 }
  ],
  [LLMProviderType.GROQ]: [
    { model_name: 'llama-3.1-70b-versatile', display_name: 'Llama 3.1 70B', max_tokens: 131072, cost_per_1k_tokens: 0.00059 },
    { model_name: 'llama-3.1-8b-instant', display_name: 'Llama 3.1 8B', max_tokens: 131072, cost_per_1k_tokens: 0.00005 },
    { model_name: 'mixtral-8x7b-32768', display_name: 'Mixtral 8x7B', max_tokens: 32768, cost_per_1k_tokens: 0.00024 }
  ],
  [LLMProviderType.COHERE]: [
    { model_name: 'command-r-plus', display_name: 'Command R+', max_tokens: 128000, cost_per_1k_tokens: 0.003 },
    { model_name: 'command-r', display_name: 'Command R', max_tokens: 128000, cost_per_1k_tokens: 0.0005 },
    { model_name: 'command', display_name: 'Command', max_tokens: 4096, cost_per_1k_tokens: 0.001 }
  ]
}

export default function LLMProvidersPage() {
  const { user, loading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.DEVELOPER 
  })

  const [isProviderModalOpen, setIsProviderModalOpen] = useState(false)
  const [isModelModalOpen, setIsModelModalOpen] = useState(false)
  const [editingProvider, setEditingProvider] = useState<LLMProvider | null>(null)
  const [editingModel, setEditingModel] = useState<{ provider: LLMProvider, model: LLMModel | null }>({ provider: null as any, model: null })
  const [showSecrets, setShowSecrets] = useState<{ [key: number]: boolean }>({})
  const [expandedProvider, setExpandedProvider] = useState<number | null>(null)

  const { data: providers, isLoading } = useLLMProviders()
  const createProviderMutation = useCreateLLMProvider()
  const updateProviderMutation = useUpdateLLMProvider()
  const deleteProviderMutation = useDeleteLLMProvider()
  const createModelMutation = useCreateLLMModel()
  const updateModelMutation = useUpdateLLMModel()
  const deleteModelMutation = useDeleteLLMModel()

  // Provider form
  const {
    register: registerProvider,
    handleSubmit: handleSubmitProvider,
    reset: resetProvider,
    watch: watchProvider,
    setValue: setValueProvider,
    formState: { errors: errorsProvider }
  } = useForm<LLMProviderFormData>({
    resolver: zodResolver(llmProviderSchema)
  })

  // Model form
  const {
    register: registerModel,
    handleSubmit: handleSubmitModel,
    reset: resetModel,
    formState: { errors: errorsModel }
  } = useForm<LLMModelFormData>({
    resolver: zodResolver(llmModelSchema)
  })

  if (loading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading LLM providers...</p>
        </div>
      </div>
    )
  }

  const handleCreateProvider = () => {
    setEditingProvider(null)
    resetProvider()
    setIsProviderModalOpen(true)
  }

  const handleEditProvider = (provider: LLMProvider) => {
    setEditingProvider(provider)
    setValueProvider('provider_type', provider.provider_type)
    setValueProvider('name', provider.name)
    setValueProvider('api_key', provider.api_key)
    setValueProvider('base_url', provider.base_url || '')
    setValueProvider('is_active', provider.is_active)
    setValueProvider('is_default', provider.is_default)
    setIsProviderModalOpen(true)
  }

  const handleDeleteProvider = async (id: number) => {
    if (!confirm('Are you sure you want to delete this LLM provider?')) return

    try {
      await deleteProviderMutation.mutateAsync(id)
      toast.success('LLM provider deleted successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete LLM provider')
    }
  }

  const onSubmitProvider = async (data: LLMProviderFormData) => {
    try {
      if (editingProvider) {
        await updateProviderMutation.mutateAsync({
          providerId: editingProvider.id,
          data
        })
        toast.success('LLM provider updated successfully')
      } else {
        // Add default models when creating new provider
        const providerData = {
          ...data,
          models: defaultModels[data.provider_type] || []
        }
        await createProviderMutation.mutateAsync(providerData)
        toast.success('LLM provider created successfully')
      }
      setIsProviderModalOpen(false)
      resetProvider()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save LLM provider')
    }
  }

  const handleCreateModel = (provider: LLMProvider) => {
    setEditingModel({ provider, model: null })
    resetModel()
    setIsModelModalOpen(true)
  }

  const handleEditModel = (provider: LLMProvider, model: LLMModel) => {
    setEditingModel({ provider, model })
    resetModel({
      model_name: model.model_name,
      display_name: model.display_name,
      is_active: model.is_active,
      max_tokens: model.max_tokens || undefined,
      cost_per_1k_tokens: model.cost_per_1k_tokens || undefined
    })
    setIsModelModalOpen(true)
  }

  const handleDeleteModel = async (providerId: number, modelId: number) => {
    if (!confirm('Are you sure you want to delete this model?')) return

    try {
      await deleteModelMutation.mutateAsync({ providerId, modelId })
      toast.success('Model deleted successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete model')
    }
  }

  const onSubmitModel = async (data: LLMModelFormData) => {
    try {
      if (editingModel.model) {
        await updateModelMutation.mutateAsync({
          providerId: editingModel.provider.id,
          modelId: editingModel.model.id,
          data
        })
        toast.success('Model updated successfully')
      } else {
        await createModelMutation.mutateAsync({
          providerId: editingModel.provider.id,
          data
        })
        toast.success('Model created successfully')
      }
      setIsModelModalOpen(false)
      resetModel()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save model')
    }
  }

  const getProviderIcon = (type: LLMProviderType) => {
    switch (type) {
      case LLMProviderType.OPENAI: return '🤖'
      case LLMProviderType.ANTHROPIC: return '🧠'
      case LLMProviderType.GEMINI: return '💎'
      case LLMProviderType.GROQ: return '⚡'
      case LLMProviderType.COHERE: return '🔮'
      default: return '🤖'
    }
  }

  const getProviderColor = (type: LLMProviderType) => {
    switch (type) {
      case LLMProviderType.OPENAI: return 'from-green-500 to-teal-600'
      case LLMProviderType.ANTHROPIC: return 'from-orange-500 to-red-600'
      case LLMProviderType.GEMINI: return 'from-blue-500 to-purple-600'
      case LLMProviderType.GROQ: return 'from-yellow-500 to-orange-600'
      case LLMProviderType.COHERE: return 'from-purple-500 to-pink-600'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  return (
    <div className="min-h-screen neural-grid">
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold cyber-text flex items-center">
                <CpuChipIcon className="h-8 w-8 mr-3" />
                LLM Providers
              </h1>
              <p className="text-gray-400 mt-2">
                Manage your AI language model providers and their configurations
              </p>
            </div>
            <button
              onClick={handleCreateProvider}
              className="btn btn-primary flex items-center"
            >
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Provider
            </button>
          </div>
        </div>

        {/* Providers List */}
        <div className="space-y-6">
          {providers?.length === 0 ? (
            <div className="card-quantum p-12 text-center">
              <CpuChipIcon className="h-16 w-16 text-gray-500 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-300 mb-2">No LLM Providers</h3>
              <p className="text-gray-500 mb-6">
                Add your first LLM provider to start using AI-powered features
              </p>
              <button
                onClick={handleCreateProvider}
                className="btn btn-primary"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Your First Provider
              </button>
            </div>
          ) : (
            providers?.map((provider) => (
              <div key={provider.id} className="card-quantum">
                <div className="p-6">
                  {/* Provider Header */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-4">
                      <div className={`p-3 rounded-lg bg-gradient-to-r ${getProviderColor(provider.provider_type)} shadow-lg`}>
                        <span className="text-2xl">{getProviderIcon(provider.provider_type)}</span>
                      </div>
                      <div>
                        <div className="flex items-center space-x-3">
                          <h3 className="text-xl font-bold text-gray-200">{provider.name}</h3>
                          {provider.is_default && (
                            <span className="px-2 py-1 bg-quantum-500/20 text-quantum-400 text-xs rounded-full">
                              Default
                            </span>
                          )}
                          {provider.is_active ? (
                            <CheckCircleIcon className="h-5 w-5 text-green-400" />
                          ) : (
                            <XCircleIcon className="h-5 w-5 text-red-400" />
                          )}
                        </div>
                        <p className="text-gray-400 text-sm">{provider.provider_type}</p>
                        {provider.base_url && (
                          <p className="text-gray-500 text-xs">{provider.base_url}</p>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => setExpandedProvider(expandedProvider === provider.id ? null : provider.id)}
                        className="btn btn-secondary text-sm"
                      >
                        <SparklesIcon className="h-4 w-4 mr-1" />
                        Models ({provider.models?.length || 0})
                      </button>
                      <button
                        onClick={() => handleEditProvider(provider)}
                        className="btn btn-secondary p-2"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeleteProvider(provider.id)}
                        className="btn btn-danger p-2"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* API Key */}
                  <div className="mb-4">
                    <label className="text-sm text-gray-400 mb-1 block">API Key</label>
                    <div className="flex items-center space-x-2">
                      <input
                        type={showSecrets[provider.id] ? 'text' : 'password'}
                        value={provider.api_key}
                        readOnly
                        className="form-input flex-1 bg-gray-700/80 text-gray-200 border-gray-600"
                      />
                      <button
                        onClick={() => setShowSecrets(prev => ({ ...prev, [provider.id]: !prev[provider.id] }))}
                        className="btn btn-secondary p-2"
                      >
                        {showSecrets[provider.id] ? (
                          <EyeSlashIcon className="h-4 w-4" />
                        ) : (
                          <EyeIcon className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Models */}
                  {expandedProvider === provider.id && (
                    <div className="border-t border-gray-700 pt-4">
                      <div className="flex items-center justify-between mb-4">
                        <h4 className="text-lg font-semibold text-gray-200">Models</h4>
                        <button
                          onClick={() => handleCreateModel(provider)}
                          className="btn btn-primary text-sm"
                        >
                          <PlusIcon className="h-4 w-4 mr-1" />
                          Add Model
                        </button>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {provider.models?.map((model) => (
                          <div key={model.id} className="card-neural p-4">
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center space-x-2">
                                <h5 className="font-medium text-gray-200">{model.display_name}</h5>
                                {model.is_active ? (
                                  <CheckCircleIcon className="h-4 w-4 text-green-400" />
                                ) : (
                                  <XCircleIcon className="h-4 w-4 text-red-400" />
                                )}
                              </div>
                              <div className="flex items-center space-x-1">
                                <button
                                  onClick={() => handleEditModel(provider, model)}
                                  className="btn btn-secondary p-1"
                                >
                                  <PencilIcon className="h-3 w-3" />
                                </button>
                                <button
                                  onClick={() => handleDeleteModel(provider.id, model.id)}
                                  className="btn btn-danger p-1"
                                >
                                  <TrashIcon className="h-3 w-3" />
                                </button>
                              </div>
                            </div>
                            <p className="text-gray-400 text-sm mb-2">{model.model_name}</p>
                            <div className="flex items-center justify-between text-xs text-gray-500">
                              {model.max_tokens && (
                                <span>Max: {model.max_tokens.toLocaleString()} tokens</span>
                              )}
                              {model.cost_per_1k_tokens && (
                                <span>${model.cost_per_1k_tokens}/1K tokens</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Provider Modal */}
        {isProviderModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="card-cyber max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-white mb-6">
                  {editingProvider ? 'Edit LLM Provider' : 'Add New LLM Provider'}
                </h2>

                <form onSubmit={handleSubmitProvider(onSubmitProvider)} className="space-y-4">
                  {/* Provider Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Provider Type
                    </label>
                    <select
                      {...registerProvider('provider_type')}
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      disabled={!!editingProvider}
                    >
                      <option value="">Select Provider</option>
                      <option value={LLMProviderType.OPENAI}>🤖 OpenAI</option>
                      <option value={LLMProviderType.ANTHROPIC}>🧠 Anthropic</option>
                      <option value={LLMProviderType.GEMINI}>💎 Google Gemini</option>
                      <option value={LLMProviderType.GROQ}>⚡ Groq</option>
                      <option value={LLMProviderType.COHERE}>🔮 Cohere</option>
                    </select>
                    {errorsProvider.provider_type && (
                      <p className="text-red-400 text-sm mt-1">{errorsProvider.provider_type.message}</p>
                    )}
                  </div>

                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Name
                    </label>
                    <input
                      {...registerProvider('name')}
                      type="text"
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      placeholder="My OpenAI Provider"
                    />
                    {errorsProvider.name && (
                      <p className="text-red-400 text-sm mt-1">{errorsProvider.name.message}</p>
                    )}
                  </div>

                  {/* API Key */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      API Key
                    </label>
                    <input
                      {...registerProvider('api_key')}
                      type="password"
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      placeholder="sk-..."
                    />
                    {errorsProvider.api_key && (
                      <p className="text-red-400 text-sm mt-1">{errorsProvider.api_key.message}</p>
                    )}
                  </div>

                  {/* Base URL */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Base URL (Optional)
                    </label>
                    <input
                      {...registerProvider('base_url')}
                      type="url"
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      placeholder="https://api.openai.com/v1"
                    />
                    {errorsProvider.base_url && (
                      <p className="text-red-400 text-sm mt-1">{errorsProvider.base_url.message}</p>
                    )}
                  </div>

                  {/* Checkboxes */}
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <input
                        {...registerProvider('is_active')}
                        type="checkbox"
                        className="h-4 w-4 text-quantum-600 focus:ring-quantum-500 border-gray-300 rounded"
                      />
                      <label className="ml-2 block text-sm text-gray-300">
                        Active
                      </label>
                    </div>

                    <div className="flex items-center">
                      <input
                        {...registerProvider('is_default')}
                        type="checkbox"
                        className="h-4 w-4 text-quantum-600 focus:ring-quantum-500 border-gray-300 rounded"
                      />
                      <label className="ml-2 block text-sm text-gray-300">
                        Set as default provider
                      </label>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setIsProviderModalOpen(false)}
                      className="btn btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createProviderMutation.isPending || updateProviderMutation.isPending}
                      className="btn btn-primary"
                    >
                      {createProviderMutation.isPending || updateProviderMutation.isPending ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Saving...
                        </>
                      ) : (
                        editingProvider ? 'Update Provider' : 'Create Provider'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

        {/* Model Modal */}
        {isModelModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="card-cyber max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-white mb-6">
                  {editingModel.model ? 'Edit Model' : 'Add New Model'}
                </h2>

                <form onSubmit={handleSubmitModel(onSubmitModel)} className="space-y-4">
                  {/* Model Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Model Name
                    </label>
                    <input
                      {...registerModel('model_name')}
                      type="text"
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      placeholder="gpt-4o"
                    />
                    {errorsModel.model_name && (
                      <p className="text-red-400 text-sm mt-1">{errorsModel.model_name.message}</p>
                    )}
                  </div>

                  {/* Display Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Display Name
                    </label>
                    <input
                      {...registerModel('display_name')}
                      type="text"
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      placeholder="GPT-4o"
                    />
                    {errorsModel.display_name && (
                      <p className="text-red-400 text-sm mt-1">{errorsModel.display_name.message}</p>
                    )}
                  </div>

                  {/* Max Tokens */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Max Tokens (Optional)
                    </label>
                    <input
                      {...registerModel('max_tokens', { valueAsNumber: true })}
                      type="number"
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      placeholder="128000"
                    />
                    {errorsModel.max_tokens && (
                      <p className="text-red-400 text-sm mt-1">{errorsModel.max_tokens.message}</p>
                    )}
                  </div>

                  {/* Cost per 1K tokens */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Cost per 1K Tokens (Optional)
                    </label>
                    <input
                      {...registerModel('cost_per_1k_tokens', { valueAsNumber: true })}
                      type="number"
                      step="0.00001"
                      className="form-input bg-gray-700/80 text-gray-200 border-gray-600"
                      placeholder="0.005"
                    />
                    {errorsModel.cost_per_1k_tokens && (
                      <p className="text-red-400 text-sm mt-1">{errorsModel.cost_per_1k_tokens.message}</p>
                    )}
                  </div>

                  {/* Active */}
                  <div className="flex items-center">
                    <input
                      {...registerModel('is_active')}
                      type="checkbox"
                      className="h-4 w-4 text-quantum-600 focus:ring-quantum-500 border-gray-300 rounded"
                    />
                    <label className="ml-2 block text-sm text-gray-300">
                      Active
                    </label>
                  </div>

                  {/* Actions */}
                  <div className="flex justify-end space-x-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setIsModelModalOpen(false)}
                      className="btn btn-secondary"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createModelMutation.isPending || updateModelMutation.isPending}
                      className="btn btn-primary"
                    >
                      {createModelMutation.isPending || updateModelMutation.isPending ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Saving...
                        </>
                      ) : (
                        editingModel.model ? 'Update Model' : 'Create Model'
                      )}
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
