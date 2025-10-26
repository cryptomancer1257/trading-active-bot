'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { api } from '@/lib/api'
import { usePlan } from '@/hooks/usePlan'
import { useFeatureFlags } from '@/hooks/useFeatureFlags'
import { 
  DocumentTextIcon, 
  ArrowLeftIcon,
  ClockIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  StarIcon,
  ClipboardDocumentIcon,
  EyeIcon
} from '@heroicons/react/24/outline'

interface StrategyTemplate {
  id: number
  template_id: string
  title: string
  category: string
  timeframe?: string
  win_rate_estimate?: string
  prompt: string
  risk_management?: string
  best_for?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export default function StrategyDetailsPage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.DEVELOPER 
  })
  
  const router = useRouter()
  const params = useParams()
  const strategyId = params?.id as string
  const { currentPlan, isFree } = usePlan()
  const { isPlanPackageEnabled } = useFeatureFlags()
  
  const [strategy, setStrategy] = useState<StrategyTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  // Plan limits - only apply if plan package feature is enabled
  // If feature is disabled, don't apply any limits (treat as Pro plan)
  // If feature is enabled and plan is not loaded yet or user is free, treat as free plan
  const isFreePlan = isPlanPackageEnabled && (!currentPlan || isFree)
  const FREE_STRATEGY_LIMIT = 5
  
  // Debug
  console.log('🔍 Strategy Details Debug:', {
    strategyId,
    isPlanPackageEnabled,
    currentPlan,
    isFree,
    isFreePlan,
    isLocked: isFreePlan && parseInt(strategyId) > FREE_STRATEGY_LIMIT
  })

  // Fetch strategy details from API
  useEffect(() => {
    const fetchStrategy = async () => {
      try {
        const response = await api.get(`/prompts/templates/by-id/${strategyId}`)
        setStrategy(response.data)
      } catch (error) {
        console.error('Error fetching strategy:', error)
        // Redirect back to library if not found
        router.push('/creator/strategy-library')
      } finally {
        setLoading(false)
      }
    }

    if (strategyId) {
      fetchStrategy()
    }
  }, [strategyId, router])

  // Check if strategy is locked for free plan
  const isStrategyLocked = isFreePlan && strategy && parseInt(strategyId) > FREE_STRATEGY_LIMIT

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'trading': return 'bg-blue-100 text-blue-800'
      case 'analysis': return 'bg-green-100 text-green-800'
      case 'risk_management': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getWinRateColor = (winRate: string) => {
    const rate = parseInt(winRate.replace(/[^\d]/g, ''))
    if (rate >= 80) return 'text-green-400'
    if (rate >= 70) return 'text-yellow-400'
    return 'text-red-400'
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (error) {
      console.error('Failed to copy text:', error)
    }
  }

  if (authLoading || loading) {
    return (
      <div className="min-h-screen neural-grid flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quantum-400 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading Strategy Details...</p>
        </div>
      </div>
    )
  }

  if (!strategy) {
    return (
      <div className="min-h-screen neural-grid flex items-center justify-center">
        <div className="text-center">
          <DocumentTextIcon className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-300 mb-2">Strategy not found</h3>
          <p className="text-gray-400 mb-4">The strategy you're looking for doesn't exist.</p>
          <button
            onClick={() => router.push('/creator/strategy-library')}
            className="btn btn-primary"
          >
            Back to Strategy Library
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen neural-grid">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={() => router.back()}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ArrowLeftIcon className="h-6 w-6 text-gray-400" />
            </button>
            <DocumentTextIcon className="h-8 w-8 text-quantum-400" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-quantum-400 to-emerald-400 bg-clip-text text-transparent">
              Strategy Details
            </h1>
          </div>
        </div>

        {/* Strategy Content */}
        <div className="max-w-4xl mx-auto">
          {/* Locked Strategy Overlay */}
          {isStrategyLocked && (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 mb-6 text-center">
              <div className="w-20 h-20 bg-quantum-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <svg className="w-10 h-10 text-quantum-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                </svg>
              </div>
              <h2 className="text-2xl font-bold text-white mb-4">Premium Strategy</h2>
              <p className="text-gray-400 mb-6">
                This strategy is available for Pro plan users only. Upgrade to unlock access to all premium strategies.
              </p>
              <button
                onClick={() => router.push('/plans')}
                className="btn btn-primary text-lg px-8 py-3"
              >
                Upgrade to Pro
              </button>
            </div>
          )}

          {/* Strategy Content (only show if not locked) */}
          {!isStrategyLocked && (
            <>
            {/* Strategy Header */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <h2 className="text-2xl font-bold text-white mb-3">{strategy.title}</h2>
                <div className="flex items-center gap-3 mb-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getCategoryColor(strategy.category)}`}>
                    {strategy.category}
                  </span>
                  {strategy.timeframe && (
                    <span className="px-3 py-1 bg-gray-700 text-gray-300 text-sm rounded-full">
                      {strategy.timeframe}
                    </span>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <button
                  onClick={() => copyToClipboard(strategy.prompt)}
                  className="btn btn-secondary flex items-center gap-2"
                >
                  <ClipboardDocumentIcon className="h-4 w-4" />
                  {copied ? 'Copied!' : 'Copy Strategy'}
                </button>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {strategy.win_rate_estimate && (
                <div className="flex items-center gap-2">
                  <ChartBarIcon className="h-5 w-5 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-300">Win Rate:</span>
                    <span className={`ml-2 text-lg font-bold ${getWinRateColor(strategy.win_rate_estimate)}`}>
                      {strategy.win_rate_estimate}
                    </span>
                  </div>
                </div>
              )}
              
              <div className="flex items-center gap-2">
                <ClockIcon className="h-5 w-5 text-gray-400" />
                <div>
                  <span className="text-sm text-gray-300">Updated:</span>
                  <span className="ml-2 text-sm text-gray-400">
                    {new Date(strategy.updated_at).toLocaleDateString()}
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <EyeIcon className="h-5 w-5 text-gray-400" />
                <div>
                  <span className="text-sm text-gray-300">Template ID:</span>
                  <span className="ml-2 text-sm text-gray-400 font-mono">
                    {strategy.template_id}
                  </span>
                </div>
              </div>
            </div>

            {/* Best For */}
            {strategy.best_for && (
              <div className="mb-6">
                <div className="flex items-center gap-2 mb-3">
                  <StarIcon className="h-5 w-5 text-gray-400" />
                  <h3 className="text-lg font-semibold text-white">Best For</h3>
                </div>
                <p className="text-gray-300 leading-relaxed">{strategy.best_for}</p>
              </div>
            )}
          </div>

          {/* Strategy Prompt */}
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Strategy Prompt</h3>
              <button
                onClick={() => copyToClipboard(strategy.prompt)}
                className="btn btn-sm btn-secondary flex items-center gap-2"
              >
                <ClipboardDocumentIcon className="h-4 w-4" />
                Copy
              </button>
            </div>
            <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
              <pre className="text-gray-300 whitespace-pre-wrap font-mono text-sm leading-relaxed">
                {strategy.prompt}
              </pre>
            </div>
          </div>

          {/* Risk Management */}
          {strategy.risk_management && (
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 mb-6">
              <div className="flex items-center gap-2 mb-4">
                <ShieldCheckIcon className="h-5 w-5 text-gray-400" />
                <h3 className="text-lg font-semibold text-white">Risk Management</h3>
              </div>
              <div className="bg-gray-900 rounded-lg p-4 border border-gray-600">
                <p className="text-gray-300 leading-relaxed">{strategy.risk_management}</p>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between">
            <button
              onClick={() => router.back()}
              className="btn btn-secondary flex items-center gap-2"
            >
              <ArrowLeftIcon className="h-4 w-4" />
              Back to Library
            </button>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => copyToClipboard(strategy.prompt)}
                className="btn btn-primary flex items-center gap-2"
              >
                <ClipboardDocumentIcon className="h-4 w-4" />
                Copy Full Strategy
              </button>
            </div>
          </div>
          </>
          )}
        </div>
      </div>
    </div>
  )
}
