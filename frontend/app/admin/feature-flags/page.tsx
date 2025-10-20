'use client'

import { useState, useEffect } from 'react'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import api from '@/lib/api'
import toast from 'react-hot-toast'
import {
  FlagIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline'

interface FeatureFlag {
  id: number
  flag_key: string
  flag_name: string
  description?: string
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export default function FeatureFlagsPage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.ADMIN 
  })

  const [flags, setFlags] = useState<FeatureFlag[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [selectedFlag, setSelectedFlag] = useState<FeatureFlag | null>(null)
  const [formData, setFormData] = useState({
    flag_key: '',
    flag_name: '',
    description: '',
    is_enabled: false
  })

  useEffect(() => {
    if (user && user.role === UserRole.ADMIN) {
      fetchFlags()
    }
  }, [user])

  const fetchFlags = async () => {
    try {
      setLoading(true)
      const response = await api.get('/feature-flags/')
      setFlags(response.data.flags)
    } catch (error: any) {
      console.error('Failed to fetch feature flags:', error)
      toast.error('Failed to load feature flags')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    try {
      await api.post('/feature-flags/', formData)
      toast.success('Feature flag created successfully')
      setShowCreateModal(false)
      setFormData({ flag_key: '', flag_name: '', description: '', is_enabled: false })
      fetchFlags()
    } catch (error: any) {
      console.error('Failed to create feature flag:', error)
      toast.error(error.response?.data?.detail || 'Failed to create feature flag')
    }
  }

  const handleUpdate = async () => {
    if (!selectedFlag) return

    try {
      await api.put(`/feature-flags/${selectedFlag.id}`, {
        flag_name: formData.flag_name,
        description: formData.description,
        is_enabled: formData.is_enabled
      })
      toast.success('Feature flag updated successfully')
      setShowEditModal(false)
      setSelectedFlag(null)
      setFormData({ flag_key: '', flag_name: '', description: '', is_enabled: false })
      fetchFlags()
    } catch (error: any) {
      console.error('Failed to update feature flag:', error)
      toast.error('Failed to update feature flag')
    }
  }

  const handleToggle = async (flag: FeatureFlag) => {
    try {
      await api.patch(`/feature-flags/${flag.id}/toggle`)
      toast.success(`Feature flag ${flag.is_enabled ? 'disabled' : 'enabled'}`)
      fetchFlags()
    } catch (error: any) {
      console.error('Failed to toggle feature flag:', error)
      toast.error('Failed to toggle feature flag')
    }
  }

  const handleDelete = async (flag: FeatureFlag) => {
    if (!confirm(`Are you sure you want to delete "${flag.flag_name}"?`)) return

    try {
      await api.delete(`/feature-flags/${flag.id}`)
      toast.success('Feature flag deleted successfully')
      fetchFlags()
    } catch (error: any) {
      console.error('Failed to delete feature flag:', error)
      toast.error('Failed to delete feature flag')
    }
  }

  const openEditModal = (flag: FeatureFlag) => {
    setSelectedFlag(flag)
    setFormData({
      flag_key: flag.flag_key,
      flag_name: flag.flag_name,
      description: flag.description || '',
      is_enabled: flag.is_enabled
    })
    setShowEditModal(true)
  }

  if (authLoading || loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cyber-400"></div>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold cyber-text flex items-center">
                <FlagIcon className="h-8 w-8 mr-3 text-cyber-400" />
                Feature Flags Management
              </h1>
              <p className="text-gray-400 mt-2">
                Control feature visibility across the platform
              </p>
            </div>
            <div className="flex gap-3">
              <button
                onClick={fetchFlags}
                className="btn btn-secondary flex items-center gap-2"
              >
                <ArrowPathIcon className="h-5 w-5" />
                Refresh
              </button>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn btn-primary flex items-center gap-2"
              >
                <PlusIcon className="h-5 w-5" />
                Create Flag
              </button>
            </div>
          </div>
        </div>

        {/* Flags List */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {flags.map((flag) => (
            <div key={flag.id} className="card-cyber p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {flag.is_enabled ? (
                      <CheckCircleIcon className="h-6 w-6 text-green-400" />
                    ) : (
                      <XCircleIcon className="h-6 w-6 text-red-400" />
                    )}
                    <h3 className="text-lg font-bold text-white">
                      {flag.flag_name}
                    </h3>
                  </div>
                  <code className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
                    {flag.flag_key}
                  </code>
                </div>
              </div>

              {flag.description && (
                <p className="text-sm text-gray-400 mb-4 line-clamp-3">
                  {flag.description}
                </p>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                <span className={`text-sm font-medium ${flag.is_enabled ? 'text-green-400' : 'text-red-400'}`}>
                  {flag.is_enabled ? 'Enabled' : 'Disabled'}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggle(flag)}
                    className={`p-2 rounded-lg transition-colors ${
                      flag.is_enabled
                        ? 'bg-red-900/20 hover:bg-red-900/30 text-red-400'
                        : 'bg-green-900/20 hover:bg-green-900/30 text-green-400'
                    }`}
                    title={flag.is_enabled ? 'Disable' : 'Enable'}
                  >
                    {flag.is_enabled ? (
                      <XCircleIcon className="h-5 w-5" />
                    ) : (
                      <CheckCircleIcon className="h-5 w-5" />
                    )}
                  </button>
                  <button
                    onClick={() => openEditModal(flag)}
                    className="p-2 bg-blue-900/20 hover:bg-blue-900/30 text-blue-400 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <PencilIcon className="h-5 w-5" />
                  </button>
                  <button
                    onClick={() => handleDelete(flag)}
                    className="p-2 bg-red-900/20 hover:bg-red-900/30 text-red-400 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <TrashIcon className="h-5 w-5" />
                  </button>
                </div>
              </div>

              <div className="mt-3 text-xs text-gray-500">
                Updated: {new Date(flag.updated_at).toLocaleString()}
              </div>
            </div>
          ))}
        </div>

        {flags.length === 0 && !loading && (
          <div className="text-center py-12 text-gray-400">
            <FlagIcon className="h-16 w-16 mx-auto mb-4 text-gray-600" />
            <p>No feature flags found. Create your first flag to get started.</p>
          </div>
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="card-cyber p-8 max-w-lg w-full">
            <h2 className="text-2xl font-bold mb-6 cyber-text">Create Feature Flag</h2>
            
            <div className="space-y-4">
              <div>
                <label className="form-label">Flag Key</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. marketplace_publish_bot"
                  value={formData.flag_key}
                  onChange={(e) => setFormData({ ...formData, flag_key: e.target.value })}
                />
                <p className="text-xs text-gray-400 mt-1">
                  Use lowercase with underscores. Cannot be changed after creation.
                </p>
              </div>

              <div>
                <label className="form-label">Display Name</label>
                <input
                  type="text"
                  className="form-input"
                  placeholder="e.g. Marketplace Bot Publishing"
                  value={formData.flag_name}
                  onChange={(e) => setFormData({ ...formData, flag_name: e.target.value })}
                />
              </div>

              <div>
                <label className="form-label">Description</label>
                <textarea
                  className="form-input"
                  rows={3}
                  placeholder="Describe what this feature flag controls..."
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="is_enabled"
                  className="w-4 h-4 rounded border-gray-600 bg-dark-800 text-cyber-400 focus:ring-cyber-400"
                  checked={formData.is_enabled}
                  onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                />
                <label htmlFor="is_enabled" className="text-white font-medium">
                  Enable this flag immediately
                </label>
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button
                onClick={() => {
                  setShowCreateModal(false)
                  setFormData({ flag_key: '', flag_name: '', description: '', is_enabled: false })
                }}
                className="btn btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="btn btn-primary flex-1"
                disabled={!formData.flag_key || !formData.flag_name}
              >
                Create Flag
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Modal */}
      {showEditModal && selectedFlag && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="card-cyber p-8 max-w-lg w-full">
            <h2 className="text-2xl font-bold mb-6 cyber-text">Edit Feature Flag</h2>
            
            <div className="space-y-4">
              <div>
                <label className="form-label">Flag Key</label>
                <input
                  type="text"
                  className="form-input bg-gray-800 text-gray-500 cursor-not-allowed"
                  value={formData.flag_key}
                  disabled
                />
                <p className="text-xs text-gray-400 mt-1">
                  Flag key cannot be changed
                </p>
              </div>

              <div>
                <label className="form-label">Display Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={formData.flag_name}
                  onChange={(e) => setFormData({ ...formData, flag_name: e.target.value })}
                />
              </div>

              <div>
                <label className="form-label">Description</label>
                <textarea
                  className="form-input"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="is_enabled_edit"
                  className="w-4 h-4 rounded border-gray-600 bg-dark-800 text-cyber-400 focus:ring-cyber-400"
                  checked={formData.is_enabled}
                  onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                />
                <label htmlFor="is_enabled_edit" className="text-white font-medium">
                  Enable this flag
                </label>
              </div>
            </div>

            <div className="flex gap-3 mt-8">
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setSelectedFlag(null)
                  setFormData({ flag_key: '', flag_name: '', description: '', is_enabled: false })
                }}
                className="btn btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                onClick={handleUpdate}
                className="btn btn-primary flex-1"
                disabled={!formData.flag_name}
              >
                Update Flag
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
