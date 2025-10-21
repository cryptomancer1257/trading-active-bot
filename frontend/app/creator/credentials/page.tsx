'use client'

import { useState } from 'react'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { 
  KeyIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { useCredentials, useCreateCredentials, useUpdateCredentials, useDeleteCredentials, CreateCredentialsData, UpdateCredentialsData } from '@/hooks/useCredentials'
import toast from 'react-hot-toast'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

// Form schemas
const credentialsSchema = z.object({
  exchange_type: z.enum(['BINANCE', 'BYBIT', 'OKX', 'BITGET', 'KRAKEN', 'HUOBI']),
  credential_type: z.enum(['SPOT', 'FUTURES', 'MARGIN']),
  network_type: z.enum(['TESTNET', 'MAINNET']),
  name: z.string().min(1, 'Name is required').max(100, 'Name too long'),
  api_key: z.string().min(10, 'API Key must be at least 10 characters'),
  api_secret: z.string().min(10, 'API Secret must be at least 10 characters'),
  passphrase: z.string().optional(),
  is_default: z.boolean().default(false),
  is_active: z.boolean().default(true)
})

type CredentialsFormData = z.infer<typeof credentialsSchema>

export default function CredentialsPage() {
  const { user, loading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.DEVELOPER 
  })

  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingCredentials, setEditingCredentials] = useState<any>(null)
  const [showSecrets, setShowSecrets] = useState<{ [key: number]: boolean }>({})

  const { data: credentials, isLoading } = useCredentials()
  const createMutation = useCreateCredentials()
  const updateMutation = useUpdateCredentials()
  const deleteMutation = useDeleteCredentials()

  const {
    register,
    handleSubmit,
    reset,
    watch,
    setValue,
    formState: { errors }
  } = useForm<CredentialsFormData>({
    resolver: zodResolver(credentialsSchema)
  })

  if (loading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading credentials...</p>
        </div>
      </div>
    )
  }

  const handleCreate = () => {
    setEditingCredentials(null)
    reset()
    setIsModalOpen(true)
  }

  const handleEdit = (cred: any) => {
    setEditingCredentials(cred)
    setValue('exchange_type', cred.exchange_type)
    setValue('credential_type', cred.credential_type)
    setValue('network_type', cred.network_type)
    setValue('name', cred.name)
    setValue('is_default', cred.is_default)
    setValue('is_active', cred.is_active)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete these credentials?')) return

    try {
      await deleteMutation.mutateAsync(id)
      toast.success('Credentials deleted successfully')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to delete credentials')
    }
  }

  const onSubmit = async (data: CredentialsFormData) => {
    try {
      if (editingCredentials) {
        // Update existing credentials
        const updateData: UpdateCredentialsData = {
          name: data.name,
          is_default: data.is_default,
          is_active: data.is_active
        }
        
        // Only include secrets if they were provided
        if (data.api_key) updateData.api_key = data.api_key
        if (data.api_secret) updateData.api_secret = data.api_secret
        if (data.passphrase) updateData.passphrase = data.passphrase

        await updateMutation.mutateAsync({ id: editingCredentials.id, data: updateData })
        toast.success('Credentials updated successfully')
      } else {
        // Create new credentials
        await createMutation.mutateAsync(data)
        toast.success('Credentials created successfully')
      }
      
      setIsModalOpen(false)
      reset()
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to save credentials')
    }
  }

  const toggleShowSecret = (id: number) => {
    setShowSecrets(prev => ({ ...prev, [id]: !prev[id] }))
  }

  const getExchangeIcon = (exchange: string) => {
    const icons = {
      BINANCE: '🟡',
      COINBASE: '🔵', 
      KRAKEN: '🟣',
      BYBIT: '🟠',
      HUOBI: '🔴'
    }
    return icons[exchange as keyof typeof icons] || '🔗'
  }

  const getNetworkBadge = (network: string) => {
    return network === 'TESTNET' 
      ? <span className="badge badge-warning">Testnet</span>
      : <span className="badge badge-success">Mainnet</span>
  }

  const getTypeBadge = (type: string) => {
    const colors = {
      SPOT: 'badge-info',
      FUTURES: 'badge-primary', 
      MARGIN: 'badge-secondary'
    }
    return <span className={`badge ${colors[type as keyof typeof colors]}`}>{type}</span>
  }

  return (
    <div className="min-h-screen neural-grid">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-quantum-400 to-neural-400 bg-clip-text text-transparent">
              🔐 API Credentials
            </h1>
            <p className="text-gray-400 mt-2">
              Manage your exchange API keys and secrets securely
            </p>
          </div>
          
          <button
            onClick={handleCreate}
            className="btn btn-primary flex items-center gap-2"
          >
            <PlusIcon className="w-5 h-5" />
            Add Credentials
          </button>
        </div>

        {/* IP Whitelist Warning */}
        <div className="mb-6 bg-gradient-to-r from-orange-500/10 to-yellow-500/10 border-l-4 border-orange-500 rounded-lg p-4 shadow-lg">
          <div className="flex items-start gap-3">
            <ExclamationTriangleIcon className="w-6 h-6 text-orange-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-orange-300 mb-2 flex items-center gap-2">
                ⚠️ Important: Add Our Server IP to Exchange Whitelist
              </h3>
              <div className="space-y-3 text-sm text-gray-300">
                <p>
                  For your API keys to work with our trading bots, you <strong className="text-white">MUST whitelist our server IP</strong> in your exchange's API settings.
                </p>
                
                <div className="bg-gray-900/50 rounded-md p-3 border border-orange-500/30">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-400 mb-1">Server IP Address:</p>
                      <code className="text-lg font-mono text-orange-300 font-bold">35.197.130.241</code>
                    </div>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText('35.197.130.241')
                        toast.success('IP address copied to clipboard!')
                      }}
                      className="px-3 py-1.5 bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 rounded-md text-xs font-medium transition-colors border border-orange-500/30"
                    >
                      📋 Copy IP
                    </button>
                  </div>
                </div>

                <div className="text-xs text-gray-400">
                  <p className="mb-1">📖 <strong>How to whitelist IP:</strong></p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li><strong>Binance:</strong> API Management → Edit API → IP Access Restrictions → Add IP</li>
                    <li><strong>Bybit:</strong> API Management → Select API → IP Restrictions → Add Trusted IP</li>
                    <li><strong>OKX:</strong> API Management → API Key Settings → IP Whitelist → Add IP</li>
                    <li><strong>Others:</strong> Check your exchange's API settings for IP whitelist/restrictions</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Credentials Grid */}
        {!credentials || credentials.length === 0 ? (
          <div className="card-cyber p-8 text-center">
            <KeyIcon className="w-16 h-16 text-gray-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-300 mb-2">No Credentials Yet</h3>
            <p className="text-gray-500 mb-4">
              Add your first exchange API credentials to start testing and deploying bots
            </p>
            <button
              onClick={handleCreate}
              className="btn btn-primary"
            >
              Add Your First Credentials
            </button>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {credentials.map((cred) => (
              <div key={cred.id} className="card-cyber p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{getExchangeIcon(cred.exchange_type)}</span>
                    <div>
                      <h3 className="font-semibold text-white">{cred.name}</h3>
                      <div className="flex gap-2 mt-1">
                        {getTypeBadge(cred.credential_type)}
                        {getNetworkBadge(cred.network_type)}
                      </div>
                    </div>
                  </div>
                  
                  {cred.is_default && (
                    <CheckCircleIcon className="w-5 h-5 text-green-400" title="Default" />
                  )}
                </div>

                <div className="space-y-2 text-sm text-gray-400">
                  <div>Exchange: <span className="text-white">{cred.exchange_type}</span></div>
                  <div>Last Used: <span className="text-white">
                    {cred.last_used_at ? new Date(cred.last_used_at).toLocaleDateString() : 'Never'}
                  </span></div>
                  <div>Created: <span className="text-white">
                    {new Date(cred.created_at).toLocaleDateString()}
                  </span></div>
                </div>

                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => handleEdit(cred)}
                    className="btn btn-secondary btn-sm flex-1"
                  >
                    <PencilIcon className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(cred.id)}
                    className="btn btn-danger btn-sm flex-1"
                    disabled={deleteMutation.isPending}
                  >
                    <TrashIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Modal */}
        {isModalOpen && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="card-cyber max-w-lg w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <h2 className="text-2xl font-bold text-white mb-4">
                  {editingCredentials ? 'Edit Credentials' : 'Add New Credentials'}
                </h2>

                {/* IP Whitelist Reminder in Modal */}
                {!editingCredentials && (
                  <div className="mb-6 bg-orange-500/10 border border-orange-500/30 rounded-lg p-3">
                    <div className="flex items-start gap-2">
                      <ExclamationTriangleIcon className="w-5 h-5 text-orange-400 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm text-orange-300 font-medium mb-1">
                          📌 Before adding API keys, whitelist our IP!
                        </p>
                        <div className="bg-gray-900/50 rounded px-2 py-1.5 mb-2">
                          <code className="text-xs font-mono text-orange-300">35.197.130.241</code>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText('35.197.130.241')
                              toast.success('IP copied!')
                            }}
                            className="ml-2 text-xs text-orange-400 hover:text-orange-300 underline"
                          >
                            copy
                          </button>
                        </div>
                        <p className="text-xs text-gray-400">
                          Add this IP to your exchange's API whitelist settings, otherwise your API keys won't work.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                  {/* Exchange Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Exchange
                    </label>
                    <select
                      {...register('exchange_type')}
                      className="form-input"
                      disabled={!!editingCredentials}
                    >
                      <option value="">Select Exchange</option>
                      <option value="BINANCE">🟡 Binance</option>
                      <option value="BYBIT">🟠 Bybit</option>
                      <option value="OKX">⚫ OKX</option>
                      <option value="BITGET">🟢 Bitget</option>
                      <option value="KRAKEN">🟣 Kraken</option>
                      <option value="HUOBI">🔴 Huobi/HTX</option>
                    </select>
                    {errors.exchange_type && (
                      <p className="text-red-400 text-sm mt-1">{errors.exchange_type.message}</p>
                    )}
                  </div>

                  {/* Credential Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Type
                    </label>
                    <select
                      {...register('credential_type')}
                      className="form-input"
                      disabled={!!editingCredentials}
                    >
                      <option value="">Select Type</option>
                      <option value="SPOT">Spot Trading</option>
                      <option value="FUTURES">Futures Trading</option>
                      <option value="MARGIN">Margin Trading</option>
                    </select>
                    {errors.credential_type && (
                      <p className="text-red-400 text-sm mt-1">{errors.credential_type.message}</p>
                    )}
                  </div>

                  {/* Network Type */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Network
                    </label>
                    <select
                      {...register('network_type')}
                      className="form-input"
                      disabled={!!editingCredentials}
                    >
                      <option value="">Select Network</option>
                      <option value="TESTNET">Testnet (Safe for testing)</option>
                      <option value="MAINNET">Mainnet (Real trading)</option>
                    </select>
                    {errors.network_type && (
                      <p className="text-red-400 text-sm mt-1">{errors.network_type.message}</p>
                    )}
                  </div>

                  {/* Name */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Name
                    </label>
                    <input
                      type="text"
                      {...register('name')}
                      className="form-input"
                      placeholder="e.g., Binance Futures Testnet"
                    />
                    {errors.name && (
                      <p className="text-red-400 text-sm mt-1">{errors.name.message}</p>
                    )}
                  </div>

                  {/* API Key */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      API Key {editingCredentials && <span className="text-xs text-gray-500">(leave blank to keep existing)</span>}
                    </label>
                    <input
                      type="text"
                      {...register('api_key', { required: !editingCredentials })}
                      className="form-input"
                      placeholder="Enter your API key"
                    />
                    {errors.api_key && (
                      <p className="text-red-400 text-sm mt-1">{errors.api_key.message}</p>
                    )}
                  </div>

                  {/* API Secret */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      API Secret {editingCredentials && <span className="text-xs text-gray-500">(leave blank to keep existing)</span>}
                    </label>
                    <input
                      type="password"
                      {...register('api_secret', { required: !editingCredentials })}
                      className="form-input"
                      placeholder="Enter your API secret"
                    />
                    {errors.api_secret && (
                      <p className="text-red-400 text-sm mt-1">{errors.api_secret.message}</p>
                    )}
                  </div>

                  {/* Passphrase (optional) */}
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Passphrase (Optional)
                    </label>
                    <input
                      type="password"
                      {...register('passphrase')}
                      className="form-input"
                      placeholder="Enter passphrase if required"
                    />
                  </div>

                  {/* Checkboxes */}
                  <div className="space-y-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        {...register('is_default')}
                        className="rounded"
                      />
                      <span className="text-sm text-gray-300">Set as default for this exchange/type/network</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        {...register('is_active')}
                        className="rounded"
                        defaultChecked
                      />
                      <span className="text-sm text-gray-300">Active</span>
                    </label>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-3 pt-4">
                    <button
                      type="button"
                      onClick={() => setIsModalOpen(false)}
                      className="btn btn-secondary flex-1"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={createMutation.isPending || updateMutation.isPending}
                      className="btn btn-primary flex-1"
                    >
                      {(createMutation.isPending || updateMutation.isPending) ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                          Saving...
                        </>
                      ) : (
                        editingCredentials ? 'Update' : 'Create'
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
