'use client'

import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { CpuChipIcon, PlusIcon, ChartBarIcon, TrashIcon, PencilIcon, EyeIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useMyBots, useDeleteBot } from '@/hooks/useBots'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function MyEntitiesPage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.DEVELOPER 
  })
  
  const { data: bots, isLoading: botsLoading, error } = useMyBots()
  const deleteBotMutation = useDeleteBot()
  const [deletingBotId, setDeletingBotId] = useState<number | null>(null)

  const loading = authLoading || botsLoading
  
  // Ensure bots is always an array
  const botsArray = Array.isArray(bots) ? bots : []

  const handleDeleteBot = async (botId: number, botName: string) => {
    if (!confirm(`Are you sure you want to delete "${botName}"? This action cannot be undone.`)) {
      return
    }

    setDeletingBotId(botId)
    try {
      await deleteBotMutation.mutateAsync(botId)
      toast.success(`Bot "${botName}" deleted successfully`)
    } catch (error) {
      toast.error('Failed to delete bot. Please try again.')
    } finally {
      setDeletingBotId(null)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Approved
          </span>
        )
      case 'PENDING':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            Pending
          </span>
        )
      case 'REJECTED':
        return (
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Rejected
          </span>
        )
      default:
        return null
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-white mb-2">Error loading bots</h2>
          <p className="text-gray-400 mb-4">{error.message}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-white">My AI Entities</h1>
            <p className="text-gray-300 mt-2">Command your autonomous trading army</p>
          </div>
          <Link href="/creator/forge" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
            <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
            Forge New Entity
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
            <div className="flex items-center">
              <CpuChipIcon className="h-8 w-8 text-purple-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Entities</p>
                <p className="text-2xl font-bold text-white">{botsArray.length}</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-green-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Active Entities</p>
                <p className="text-2xl font-bold text-white">{botsArray.filter(b => b.status === 'APPROVED').length}</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
            <div className="flex items-center">
              <CpuChipIcon className="h-8 w-8 text-blue-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">Total Subscribers</p>
                <p className="text-2xl font-bold text-white">{botsArray.reduce((sum, bot) => sum + (bot.total_subscribers || 0), 0)}</p>
              </div>
            </div>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg shadow-md border border-gray-700">
            <div className="flex items-center">
              <CpuChipIcon className="h-8 w-8 text-yellow-400" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-400">ICP Total Revenue Potential</p>
                <p className="text-2xl font-bold text-white">{botsArray.reduce((sum, bot) => sum + (parseFloat(String(bot.price_per_month || '0')) || 0), 0).toFixed(1)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Bot Grid */}
        {botsArray.length === 0 ? (
          <div className="text-center py-12">
            <CpuChipIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-300 mb-2">No entities found</h3>
            <p className="text-gray-400 mb-6">Get started by creating your first AI trading entity.</p>
            <Link href="/creator/forge" className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
              <PlusIcon className="-ml-1 mr-2 h-5 w-5" />
              Create Your First Entity
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {botsArray.map((bot) => (
              <div key={bot.id} className="bg-gray-800 rounded-lg shadow-md border border-gray-700 p-6 hover:shadow-lg transition-shadow">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center">
                    <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                      <CpuChipIcon className="h-6 w-6 text-white" />
                    </div>
                    <div className="ml-3">
                      <h3 className="text-lg font-semibold text-white">{bot.name}</h3>
                      {getStatusBadge(bot.status)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-400">Price/Month</div>
                    <div className="text-lg font-bold text-purple-400">{bot.price_per_month} ICP</div>
                  </div>
                </div>

                <p className="text-gray-300 text-sm mb-4 line-clamp-2">{bot.description}</p>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Subscribers:</span>
                    <span className="text-white">{bot.total_subscribers || 0}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Rating:</span>
                    <span className="text-white">{(bot.average_rating || 0).toFixed(1)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Exchange:</span>
                    <span className="text-white">{bot.exchange_type}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Pair:</span>
                    <span className="text-white">{bot.trading_pair} | {bot.timeframe}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-400">Mode:</span>
                    <span className="text-white">ACTIVE | v{bot.version}</span>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                  <div className="text-xs text-gray-500">Created: {new Date(bot.created_at).toLocaleDateString()}</div>
                  
                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <Link href={`/creator/entities/${bot.id}`}>
                      <button className="p-2 text-blue-400 hover:text-blue-600 rounded-md hover:bg-blue-50" title="View Details">
                        <EyeIcon className="h-5 w-5" />
                      </button>
                    </Link>
                    
                    <Link href={`/creator/entities/${bot.id}/edit`}>
                      <button className="p-2 text-blue-400 hover:text-blue-600 rounded-md hover:bg-blue-50" title="Edit Bot">
                        <PencilIcon className="h-5 w-5" />
                      </button>
                    </Link>

                    <button
                      onClick={() => handleDeleteBot(bot.id, bot.name)}
                      disabled={deletingBotId === bot.id}
                      className="p-2 text-red-400 hover:text-red-600 rounded-md hover:bg-red-50 disabled:opacity-50"
                      title="Delete Bot"
                    >
                      {deletingBotId === bot.id ? (
                        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-400"></div>
                      ) : (
                        <TrashIcon className="h-5 w-5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}