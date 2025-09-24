'use client'

import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { CpuChipIcon, PlusIcon, ChartBarIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline'
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
      toast.success('🗑️ Neural Entity successfully deleted from quantum matrix')
    } catch (error: any) {
      const message = error.response?.data?.detail || error.message || 'Failed to delete entity'
      toast.error(`Deletion failed: ${message}`)
    } finally {
      setDeletingBotId(null)
    }
  }

  const getBotTypeColor = (type: string) => {
    switch (type) {
      case 'FUTURES': return 'from-quantum-500 to-purple-600'
      case 'FUTURES_RPA': return 'from-cyber-500 to-blue-600'
      case 'LLM': return 'from-neural-500 to-green-600'
      case 'SPOT': return 'from-yellow-500 to-orange-600'
      default: return 'from-gray-500 to-gray-600'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'APPROVED': return 'text-neural-400 bg-neural-500/10'
      case 'PENDING': return 'text-yellow-400 bg-yellow-500/10'
      case 'REJECTED': return 'text-danger-400 bg-danger-500/10'
      default: return 'text-gray-400 bg-gray-500/10'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Accessing Neural Database...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="text-danger-400 mb-4">⚠️ Neural Network Error</div>
          <p className="text-gray-300">Failed to access neural database. Please try again.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-extrabold cyber-text">
            ⚡ My AI Entities
          </h1>
          <p className="text-gray-400 mt-2">
            Command your autonomous trading army
          </p>
        </div>
        <Link
          href="/creator/forge"
          className="btn btn-primary px-6 py-3 flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>🧠 Forge New Entity</span>
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card-cyber p-6 text-center animate-fade-in">
          <div className="text-3xl font-bold cyber-text animate-neural-pulse">
            {botsArray.length}
          </div>
          <div className="text-sm text-gray-400 mt-1">Total Entities</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="text-3xl font-bold text-neural-400 animate-neural-pulse">
            {botsArray.filter(bot => bot.status === 'APPROVED').length}
          </div>
          <div className="text-sm text-gray-400 mt-1">Active Entities</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div className="text-3xl font-bold text-yellow-400 animate-neural-pulse">
            {botsArray.reduce((sum, bot) => sum + (bot.total_subscribers || 0), 0)}
          </div>
          <div className="text-sm text-gray-400 mt-1">Total Subscribers</div>
        </div>
      </div>

      {/* Bots List or Empty State */}
        {botsArray.length === 0 ? (
        <div className="card-quantum p-12 text-center">
          <div className="relative mx-auto h-24 w-24 mb-6">
            <CpuChipIcon className="h-24 w-24 text-gray-600 animate-neural-pulse" />
            <div className="absolute inset-0 bg-gradient-to-r from-quantum-500/20 to-cyber-500/20 rounded-full blur-xl"></div>
          </div>
          
          <h3 className="text-2xl font-bold cyber-text mb-4">
            Neural Database Empty
          </h3>
          <p className="text-gray-400 mb-8 max-w-md mx-auto">
            Your AI entity arsenal is currently empty. Begin your journey into autonomous trading by forging your first neural entity.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/creator/forge"
              className="btn btn-primary px-8 py-3"
            >
              🧠 Forge First Entity
            </Link>
            <Link
              href="/arsenal"
              className="btn btn-secondary px-8 py-3"
            >
              🔍 Study Existing Entities
            </Link>
          </div>
          
          <div className="mt-8 text-sm text-gray-500">
            <p>💡 Pro Tip: Start with analyzing successful entities in the arsenal</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {botsArray.map((bot, index) => (
            <div
              key={bot.id}
              className="card-quantum p-6 hover:shadow-2xl hover:shadow-quantum-500/20 transition-all duration-300 transform hover:-translate-y-1 animate-fade-in"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className={`p-3 rounded-lg bg-gradient-to-r ${getBotTypeColor(bot.bot_type)} shadow-lg`}>
                    <CpuChipIcon className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-gray-200">{bot.name}</h3>
                    <p className="text-sm text-gray-400">{bot.bot_type}</p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(bot.status)}`}>
                  {bot.status}
                </span>
              </div>

              {/* Description */}
              <p className="text-gray-400 mb-4 leading-relaxed text-sm line-clamp-3">
                {bot.description}
              </p>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 mb-4 text-center">
                <div>
                  <div className="text-lg font-bold text-quantum-400">{bot.total_subscribers}</div>
                  <div className="text-xs text-gray-500">Subscribers</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-cyber-400">{bot.average_rating.toFixed(1)}</div>
                  <div className="text-xs text-gray-500">Rating</div>
                </div>
              </div>

              {/* Config Info */}
              <div className="text-xs text-gray-500 mb-4 space-y-1">
                <div>Exchange: {bot.exchange_type}</div>
                <div>Pair: {bot.trading_pair} | {bot.timeframe}</div>
                <div>Mode: {bot.bot_mode} | v{bot.version}</div>
              </div>

              {/* Actions */}
              <div className="flex space-x-2">
                <Link 
                  href={`/creator/entities/${bot.id}/edit`}
                  className="btn btn-secondary flex-1 py-2 text-sm flex items-center justify-center"
                >
                  <PencilIcon className="h-4 w-4 mr-1" />
                  Edit
                </Link>
                <button
                  onClick={() => handleDeleteBot(bot.id, bot.name)}
                  disabled={deletingBotId === bot.id}
                  className="btn btn-danger px-3 py-2 text-sm flex items-center justify-center disabled:opacity-50"
                >
                  {deletingBotId === bot.id ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <TrashIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
              
              <div className="text-xs text-gray-500 mt-2">
                Created: {new Date(bot.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Floating Elements */}
      <div className="fixed top-24 right-16 w-1 h-1 bg-quantum-500 rounded-full animate-neural-pulse opacity-40"></div>
      <div className="fixed bottom-24 left-16 w-1.5 h-1.5 bg-cyber-400 rounded-full animate-neural-pulse opacity-50" style={{ animationDelay: '1s' }}></div>
    </div>
  )
}
