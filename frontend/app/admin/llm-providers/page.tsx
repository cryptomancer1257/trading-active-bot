'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useRouter } from 'next/navigation'
import { UserRole } from '@/lib/types'
import api from '@/lib/api'

interface PlatformLLMProvider {
  id: number
  provider_type: string
  name: string
  api_key: string
  base_url: string | null
  is_active: boolean
  is_default: boolean
  created_by: number | null
  created_at: string
  updated_at: string
  models: PlatformLLMModel[]
}

interface PlatformLLMModel {
  id: number
  provider_id: number
  model_name: string
  display_name: string
  is_active: boolean
  max_tokens: number | null
  cost_per_1k_tokens: number | null
  created_at: string
  updated_at: string
}

interface ProviderFormData {
  provider_type: string
  name: string
  api_key: string
  base_url: string
  is_active: boolean
  is_default: boolean
}

export default function AdminLLMProvidersPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()
  const [providers, setProviders] = useState<PlatformLLMProvider[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showApiKey, setShowApiKey] = useState<{ [key: number]: boolean }>({})
  
  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [selectedProvider, setSelectedProvider] = useState<PlatformLLMProvider | null>(null)
  const [formData, setFormData] = useState<ProviderFormData>({
    provider_type: 'OPENAI',
    name: '',
    api_key: '',
    base_url: '',
    is_active: true,
    is_default: false,
  })

  useEffect(() => {
    console.log('🔐 Admin Page - Auth Loading:', authLoading)
    console.log('🔐 Admin Page - User:', user)
    console.log('🔐 Admin Page - User Role:', user?.role)
    
    // Wait for auth to finish loading
    if (authLoading) {
      console.log('⏳ Auth still loading, waiting...')
      return
    }
    
    // After loading, check if user exists
    if (!user) {
      console.log('❌ No user after loading, redirecting to login')
      router.push('/auth/login')
      return
    }

    // Normalize role to string to avoid enum narrowing/type mismatch at build time
    const userRoleStr = (user as any)?.role ? String((user as any).role) : ''
    if (userRoleStr !== 'ADMIN') {
      console.log('❌ User is not ADMIN, redirecting to home')
      console.log('User role:', userRoleStr)
      router.push('/')
      return
    }

    console.log('✅ User is ADMIN, fetching providers')
    fetchProviders()
  }, [user, authLoading, router])

  const fetchProviders = async () => {
    try {
      setLoading(true)
      const response = await api.get('/admin/llm-providers/')
      setProviders(response.data)
      setError(null)
    } catch (err: any) {
      console.error('Failed to fetch providers:', err)
      setError(err.response?.data?.detail || err.message || 'Failed to fetch providers')
    } finally {
      setLoading(false)
    }
  }

  const toggleApiKeyVisibility = (providerId: number) => {
    setShowApiKey(prev => ({
      ...prev,
      [providerId]: !prev[providerId]
    }))
  }

  const maskApiKey = (apiKey: string) => {
    if (apiKey.length <= 8) return '****'
    return `${apiKey.substring(0, 4)}...${apiKey.substring(apiKey.length - 4)}`
  }

  const toggleProviderStatus = async (providerId: number, currentStatus: boolean) => {
    try {
      await api.put(`/admin/llm-providers/${providerId}`, {
        is_active: !currentStatus
      })
      fetchProviders()
    } catch (err: any) {
      console.error('Failed to update provider:', err)
      alert(err.response?.data?.detail || err.message || 'Failed to update provider')
    }
  }

  const handleCreateProvider = async () => {
    try {
      await api.post('/admin/llm-providers/', formData)
      setShowCreateModal(false)
      resetForm()
      fetchProviders()
    } catch (err: any) {
      console.error('Failed to create provider:', err)
      alert(err.response?.data?.detail || err.message || 'Failed to create provider')
    }
  }

  const handleEditProvider = async () => {
    if (!selectedProvider) return
    try {
      await api.put(`/admin/llm-providers/${selectedProvider.id}`, formData)
      setShowEditModal(false)
      setSelectedProvider(null)
      resetForm()
      fetchProviders()
    } catch (err: any) {
      console.error('Failed to update provider:', err)
      alert(err.response?.data?.detail || err.message || 'Failed to update provider')
    }
  }

  const handleDeleteProvider = async () => {
    if (!selectedProvider) return
    try {
      await api.delete(`/admin/llm-providers/${selectedProvider.id}`)
      setShowDeleteModal(false)
      setSelectedProvider(null)
      fetchProviders()
    } catch (err: any) {
      console.error('Failed to delete provider:', err)
      alert(err.response?.data?.detail || err.message || 'Failed to delete provider')
    }
  }

  const openEditModal = (provider: PlatformLLMProvider) => {
    setSelectedProvider(provider)
    setFormData({
      provider_type: provider.provider_type,
      name: provider.name,
      api_key: provider.api_key,
      base_url: provider.base_url || '',
      is_active: provider.is_active,
      is_default: provider.is_default,
    })
    setShowEditModal(true)
  }

  const openDeleteModal = (provider: PlatformLLMProvider) => {
    setSelectedProvider(provider)
    setShowDeleteModal(true)
  }

  const resetForm = () => {
    setFormData({
      provider_type: 'OPENAI',
      name: '',
      api_key: '',
      base_url: '',
      is_active: true,
      is_default: false,
    })
  }

  // Show loading while auth is checking
  if (authLoading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-quantum-500"></div>
          <p className="mt-4 text-gray-400">Checking authentication...</p>
        </div>
      </div>
    )
  }

  // Show loading while fetching providers
  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-quantum-500"></div>
          <p className="mt-4 text-gray-400">Loading providers...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-dark-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <h1 className="text-2xl font-bold text-gray-200 mb-2">Error</h1>
          <p className="text-red-400">{error}</p>
          <button
            onClick={fetchProviders}
            className="mt-4 px-4 py-2 bg-quantum-600 text-white rounded-lg hover:bg-quantum-700"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-dark-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-quantum-400 to-cyber-400 bg-clip-text text-transparent">
              🔐 Platform LLM Providers
            </h1>
            <p className="mt-2 text-gray-400">
              Manage LLM providers and API keys for the entire platform
            </p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-3 bg-gradient-to-r from-quantum-600 to-cyber-600 text-white rounded-lg hover:from-quantum-700 hover:to-cyber-700 transition-all duration-200 font-medium shadow-lg shadow-quantum-500/20"
          >
            ➕ Create Provider
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-dark-800/50 backdrop-blur-sm border border-quantum-500/20 rounded-lg p-4">
            <div className="text-sm text-gray-400">Total Providers</div>
            <div className="text-2xl font-bold text-gray-200 mt-1">{providers.length}</div>
          </div>
          <div className="bg-dark-800/50 backdrop-blur-sm border border-quantum-500/20 rounded-lg p-4">
            <div className="text-sm text-gray-400">Active Providers</div>
            <div className="text-2xl font-bold text-green-400 mt-1">
              {providers.filter(p => p.is_active).length}
            </div>
          </div>
          <div className="bg-dark-800/50 backdrop-blur-sm border border-quantum-500/20 rounded-lg p-4">
            <div className="text-sm text-gray-400">Total Models</div>
            <div className="text-2xl font-bold text-blue-400 mt-1">
              {providers.reduce((acc, p) => acc + p.models.length, 0)}
            </div>
          </div>
          <div className="bg-dark-800/50 backdrop-blur-sm border border-quantum-500/20 rounded-lg p-4">
            <div className="text-sm text-gray-400">Default Provider</div>
            <div className="text-2xl font-bold text-quantum-400 mt-1">
              {providers.find(p => p.is_default)?.provider_type || 'None'}
            </div>
          </div>
        </div>

        {/* Providers List */}
        <div className="space-y-4">
          {providers.map((provider) => (
            <div
              key={provider.id}
              className="bg-dark-800/50 backdrop-blur-sm border border-quantum-500/20 rounded-lg p-6"
            >
              {/* Provider Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-4">
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    provider.provider_type === 'OPENAI' ? 'bg-green-500/20 text-green-400' :
                    provider.provider_type === 'ANTHROPIC' ? 'bg-purple-500/20 text-purple-400' :
                    provider.provider_type === 'GEMINI' ? 'bg-blue-500/20 text-blue-400' :
                    'bg-gray-500/20 text-gray-400'
                  }`}>
                    {provider.provider_type === 'OPENAI' && '🤖'}
                    {provider.provider_type === 'ANTHROPIC' && '🧠'}
                    {provider.provider_type === 'GEMINI' && '💎'}
                    {!['OPENAI', 'ANTHROPIC', 'GEMINI'].includes(provider.provider_type) && '🔮'}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-gray-200">{provider.name}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className="text-sm text-gray-400">{provider.provider_type}</span>
                      {provider.is_default && (
                        <span className="px-2 py-0.5 bg-quantum-500/20 text-quantum-400 text-xs rounded-full">
                          Default
                        </span>
                      )}
                      <span className={`px-2 py-0.5 text-xs rounded-full ${
                        provider.is_active
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {provider.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => openEditModal(provider)}
                    className="px-4 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 font-medium transition-colors"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    onClick={() => toggleProviderStatus(provider.id, provider.is_active)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                      provider.is_active
                        ? 'bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30'
                        : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                    }`}
                  >
                    {provider.is_active ? '⏸️ Deactivate' : '▶️ Activate'}
                  </button>
                  <button
                    onClick={() => openDeleteModal(provider)}
                    className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 font-medium transition-colors"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>

              {/* API Key */}
              <div className="mb-4 p-4 bg-dark-700/50 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="text-sm text-gray-400 mb-1">API Key</div>
                    <div className="font-mono text-gray-200">
                      {showApiKey[provider.id] ? provider.api_key : maskApiKey(provider.api_key)}
                    </div>
                  </div>
                  <button
                    onClick={() => toggleApiKeyVisibility(provider.id)}
                    className="ml-4 px-3 py-1 bg-quantum-500/20 text-quantum-400 rounded hover:bg-quantum-500/30 text-sm"
                  >
                    {showApiKey[provider.id] ? '🙈 Hide' : '👁️ Show'}
                  </button>
                </div>
                {provider.base_url && (
                  <div className="mt-2">
                    <div className="text-sm text-gray-400">Base URL</div>
                    <div className="text-sm text-gray-300">{provider.base_url}</div>
                  </div>
                )}
              </div>

              {/* Models */}
              <div>
                <h4 className="text-sm font-medium text-gray-400 mb-2">
                  Models ({provider.models.length})
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                  {provider.models.map((model) => (
                    <div
                      key={model.id}
                      className={`p-3 rounded-lg border ${
                        model.is_active
                          ? 'bg-dark-700/30 border-quantum-500/30'
                          : 'bg-dark-700/10 border-gray-700/30 opacity-50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-200">
                            {model.display_name}
                          </div>
                          <div className="text-xs text-gray-400 mt-0.5">
                            {model.model_name}
                          </div>
                          {model.cost_per_1k_tokens && (
                            <div className="text-xs text-quantum-400 mt-1">
                              ${model.cost_per_1k_tokens}/1K tokens
                            </div>
                          )}
                        </div>
                        <div className={`w-2 h-2 rounded-full ${
                          model.is_active ? 'bg-green-400' : 'bg-gray-600'
                        }`} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Metadata */}
              <div className="mt-4 pt-4 border-t border-quantum-500/10 text-xs text-gray-500">
                <div className="flex items-center justify-between">
                  <span>Created: {new Date(provider.created_at).toLocaleString()}</span>
                  <span>Updated: {new Date(provider.updated_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {providers.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔮</div>
            <h3 className="text-xl font-medium text-gray-300 mb-2">No Providers Yet</h3>
            <p className="text-gray-500">
              Use the API to create your first platform LLM provider
            </p>
            <a
              href="http://localhost:8000/docs#/Admin%20LLM%20Providers"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-4 px-4 py-2 bg-quantum-600 text-white rounded-lg hover:bg-quantum-700"
            >
              Open API Docs
            </a>
          </div>
        )}

        {/* API Documentation Link */}
        <div className="mt-8 p-4 bg-quantum-500/10 border border-quantum-500/20 rounded-lg">
          <div className="flex items-start space-x-3">
            <div className="text-2xl">📚</div>
            <div className="flex-1">
              <h4 className="font-medium text-gray-200 mb-1">API Documentation</h4>
              <p className="text-sm text-gray-400 mb-2">
                To create, update, or delete providers, use the Admin API endpoints
              </p>
              <a
                href="http://localhost:8000/docs#/Admin%20LLM%20Providers"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-quantum-400 hover:text-quantum-300 underline"
              >
                View API Documentation →
              </a>
            </div>
          </div>
        </div>

        {/* Create/Edit Modal */}
        {(showCreateModal || showEditModal) && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-dark-800 border border-quantum-500/30 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-gray-200 mb-6">
                  {showCreateModal ? '➕ Create New Provider' : '✏️ Edit Provider'}
                </h2>
                
                <div className="space-y-4">
                  {/* Provider Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Provider Type *
                    </label>
                    <select
                      value={formData.provider_type}
                      onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                      className="w-full bg-dark-700 border border-quantum-500/30 rounded-lg px-4 py-2 text-gray-200 focus:outline-none focus:border-quantum-500"
                      disabled={showEditModal}
                    >
                      <option value="OPENAI">OpenAI</option>
                      <option value="ANTHROPIC">Anthropic (Claude)</option>
                      <option value="GEMINI">Google Gemini</option>
                      <option value="GROQ">Groq</option>
                      <option value="COHERE">Cohere</option>
                    </select>
                  </div>

                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Provider Name *
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="e.g., Platform OpenAI"
                      className="w-full bg-dark-700 border border-quantum-500/30 rounded-lg px-4 py-2 text-gray-200 focus:outline-none focus:border-quantum-500"
                    />
                  </div>

                  {/* API Key */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      API Key *
                    </label>
                    <input
                      type="password"
                      value={formData.api_key}
                      onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                      placeholder="sk-..."
                      className="w-full bg-dark-700 border border-quantum-500/30 rounded-lg px-4 py-2 text-gray-200 font-mono focus:outline-none focus:border-quantum-500"
                    />
                  </div>

                  {/* Base URL */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Base URL (Optional)
                    </label>
                    <input
                      type="text"
                      value={formData.base_url}
                      onChange={(e) => setFormData({ ...formData, base_url: e.target.value })}
                      placeholder="https://api.openai.com/v1"
                      className="w-full bg-dark-700 border border-quantum-500/30 rounded-lg px-4 py-2 text-gray-200 focus:outline-none focus:border-quantum-500"
                    />
                  </div>

                  {/* Checkboxes */}
                  <div className="flex items-center space-x-6">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="w-4 h-4 rounded border-quantum-500/30 bg-dark-700 text-quantum-600 focus:ring-quantum-500"
                      />
                      <span className="text-sm text-gray-300">Active</span>
                    </label>
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.is_default}
                        onChange={(e) => setFormData({ ...formData, is_default: e.target.checked })}
                        className="w-4 h-4 rounded border-quantum-500/30 bg-dark-700 text-quantum-600 focus:ring-quantum-500"
                      />
                      <span className="text-sm text-gray-300">Set as Default</span>
                    </label>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center justify-end space-x-3 mt-6 pt-6 border-t border-quantum-500/20">
                  <button
                    onClick={() => {
                      showCreateModal ? setShowCreateModal(false) : setShowEditModal(false)
                      resetForm()
                      setSelectedProvider(null)
                    }}
                    className="px-4 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={showCreateModal ? handleCreateProvider : handleEditProvider}
                    disabled={!formData.name || !formData.api_key}
                    className="px-6 py-2 bg-gradient-to-r from-quantum-600 to-cyber-600 text-white rounded-lg hover:from-quantum-700 hover:to-cyber-700 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {showCreateModal ? 'Create Provider' : 'Save Changes'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        {showDeleteModal && selectedProvider && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-dark-800 border border-red-500/30 rounded-xl max-w-md w-full shadow-2xl">
              <div className="p-6">
                <div className="text-center">
                  <div className="text-6xl mb-4">⚠️</div>
                  <h2 className="text-2xl font-bold text-gray-200 mb-2">Delete Provider?</h2>
                  <p className="text-gray-400 mb-4">
                    Are you sure you want to delete <span className="font-bold text-red-400">{selectedProvider.name}</span>?
                  </p>
                  <p className="text-sm text-gray-500 mb-6">
                    This action cannot be undone. All associated models will also be deleted.
                  </p>
                </div>

                <div className="flex items-center justify-center space-x-3">
                  <button
                    onClick={() => {
                      setShowDeleteModal(false)
                      setSelectedProvider(null)
                    }}
                    className="px-6 py-2 bg-dark-700 text-gray-300 rounded-lg hover:bg-dark-600 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleDeleteProvider}
                    className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Delete Provider
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

