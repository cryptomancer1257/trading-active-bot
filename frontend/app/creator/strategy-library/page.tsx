'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { api } from '@/lib/api'
import { usePlan } from '@/hooks/usePlan'
import { useFeatureFlags } from '@/hooks/useFeatureFlags'
import { 
  DocumentTextIcon, 
  ArrowLeftIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  ClockIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  StarIcon
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

export default function StrategyLibraryPage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true, 
    requiredRole: UserRole.DEVELOPER 
  })
  
  const router = useRouter()
  const { currentPlan, isFree } = usePlan()
  const { isPlanPackageEnabled } = useFeatureFlags()
  const [strategies, setStrategies] = useState<StrategyTemplate[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedTimeframe, setSelectedTimeframe] = useState('all')
  const [showFilters, setShowFilters] = useState(false)

  // Plan limits - only apply if plan package feature is enabled
  // If feature is disabled, don't apply any limits (treat as Pro plan)
  // If feature is enabled and plan is not loaded yet or user is free, treat as free plan
  const isFreePlan = isPlanPackageEnabled && (!currentPlan || isFree)
  const FREE_STRATEGY_LIMIT = 5
  
  // Debug plan
  console.log('🔍 Strategy Library Debug:', {
    isPlanPackageEnabled,
    currentPlan,
    planName: currentPlan?.plan_name,
    isFree,
    isFreePlan,
    strategiesCount: strategies.length,
    willShowLocked: isFreePlan && strategies.length > FREE_STRATEGY_LIMIT
  })

  // Fetch strategies from API
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await api.get('/prompts/prompt-templates')
        setStrategies(response.data)
      } catch (error) {
        console.error('Error fetching strategies:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStrategies()
  }, [])

  // Get unique categories and timeframes for filters
  const categories = Array.from(new Set(strategies.map(s => s.category)))
  const timeframes = Array.from(new Set(strategies.map(s => s.timeframe).filter(Boolean)))

  // Filter strategies
  const filteredStrategies = strategies.filter(strategy => {
    const matchesSearch = strategy.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         strategy.prompt.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = selectedCategory === 'all' || strategy.category === selectedCategory
    const matchesTimeframe = selectedTimeframe === 'all' || strategy.timeframe === selectedTimeframe
    
    return matchesSearch && matchesCategory && matchesTimeframe
  })

  // Apply plan limits
  const visibleStrategies = isFreePlan 
    ? filteredStrategies.slice(0, FREE_STRATEGY_LIMIT)
    : filteredStrategies
  
  const lockedStrategies = isFreePlan 
    ? filteredStrategies.slice(FREE_STRATEGY_LIMIT)
    : []

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

  if (authLoading || loading) {
    return (
      <div className="min-h-screen neural-grid flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quantum-400 mx-auto"></div>
          <p className="text-gray-400 mt-4">Loading Strategy Library...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen neural-grid">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <button
                  onClick={() => router.back()}
                  className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <ArrowLeftIcon className="h-6 w-6 text-gray-400" />
                </button>
                <DocumentTextIcon className="h-8 w-8 text-quantum-400" />
                <h1 className="text-4xl font-bold bg-gradient-to-r from-quantum-400 to-emerald-400 bg-clip-text text-transparent">
                  Strategy Library
                </h1>
              </div>
              <p className="text-gray-300 text-lg">
                Browse and discover pre-built trading strategy templates
              </p>
            </div>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="mb-8">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search strategies..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-quantum-500 focus:border-transparent"
                />
              </div>
            </div>

            {/* Filter Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn btn-secondary flex items-center gap-2"
            >
              <FunnelIcon className="h-5 w-5" />
              Filters
            </button>
          </div>

          {/* Filters Panel */}
          {showFilters && (
            <div className="mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Category Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Category</label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-quantum-500"
                  >
                    <option value="all">All Categories</option>
                    {categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>

                {/* Timeframe Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">Timeframe</label>
                  <select
                    value={selectedTimeframe}
                    onChange={(e) => setSelectedTimeframe(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-2 focus:ring-quantum-500"
                  >
                    <option value="all">All Timeframes</option>
                    {timeframes.map(timeframe => (
                      <option key={timeframe} value={timeframe}>{timeframe}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Results Count */}
        <div className="mb-6">
          <p className="text-gray-400">
            Showing {visibleStrategies.length} of {filteredStrategies.length} strategies
            {isFreePlan && lockedStrategies.length > 0 && (
              <span className="text-quantum-400 ml-2">
                ({lockedStrategies.length} locked - upgrade to unlock)
              </span>
            )}
          </p>
        </div>

        {/* Strategies Grid */}
        {filteredStrategies.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {/* Visible Strategies */}
            {visibleStrategies.map((strategy) => (
              <div key={strategy.id} className="bg-gray-800 rounded-lg border border-gray-700 p-6 hover:border-quantum-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-quantum-500/10">
                {/* Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-bold text-white mb-2 line-clamp-2">
                      {strategy.title}
                    </h3>
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(strategy.category)}`}>
                        {strategy.category}
                      </span>
                      {strategy.timeframe && (
                        <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded-full">
                          {strategy.timeframe}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Stats */}
                <div className="space-y-3 mb-4">
                  {strategy.win_rate_estimate && (
                    <div className="flex items-center gap-2">
                      <ChartBarIcon className="h-4 w-4 text-gray-400" />
                      <span className="text-sm text-gray-300">Win Rate:</span>
                      <span className={`text-sm font-medium ${getWinRateColor(strategy.win_rate_estimate)}`}>
                        {strategy.win_rate_estimate}
                      </span>
                    </div>
                  )}
                  
                  {strategy.best_for && (
                    <div className="flex items-start gap-2">
                      <StarIcon className="h-4 w-4 text-gray-400 mt-0.5" />
                      <div>
                        <span className="text-sm text-gray-300">Best for:</span>
                        <p className="text-sm text-gray-400 mt-1">{strategy.best_for}</p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Prompt Preview */}
                <div className="mb-4">
                  <p className="text-sm text-gray-400 line-clamp-3">
                    {strategy.prompt}
                  </p>
                </div>

                {/* Risk Management */}
                {strategy.risk_management && (
                  <div className="mb-4">
                    <div className="flex items-center gap-2 mb-2">
                      <ShieldCheckIcon className="h-4 w-4 text-gray-400" />
                      <span className="text-sm font-medium text-gray-300">Risk Management</span>
                    </div>
                    <p className="text-sm text-gray-400 line-clamp-2">
                      {strategy.risk_management}
                    </p>
                  </div>
                )}

                {/* Actions */}
                <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <ClockIcon className="h-4 w-4" />
                    <span>Updated {new Date(strategy.updated_at).toLocaleDateString()}</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => router.push(`/creator/strategy-library/${strategy.id}`)}
                      className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                      title="View Details"
                    >
                      <EyeIcon className="h-4 w-4 text-gray-400" />
                    </button>
                  </div>
                </div>
              </div>
            ))}

            {/* Locked Strategies for Free Plan */}
            {isFreePlan && lockedStrategies.map((strategy) => (
              <div key={strategy.id} className="bg-gray-800 rounded-lg border border-gray-700 p-6 relative opacity-60">
                {/* Lock Overlay */}
                <div className="absolute inset-0 bg-gray-900/80 rounded-lg flex items-center justify-center z-10">
                  <div className="text-center">
                    <div className="w-16 h-16 bg-quantum-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                      <svg className="w-8 h-8 text-quantum-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-white mb-2">Premium Strategy</h3>
                    <p className="text-gray-400 text-sm mb-4">Upgrade to Pro to unlock this strategy</p>
                    <button
                      onClick={() => router.push('/plans')}
                      className="btn btn-primary"
                    >
                      Unlock Strategy
                    </button>
                  </div>
                </div>

                {/* Strategy Content (blurred) */}
                <div className="filter blur-sm">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <h3 className="text-xl font-bold text-white mb-2 line-clamp-2">
                        {strategy.title}
                      </h3>
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(strategy.category)}`}>
                          {strategy.category}
                        </span>
                        {strategy.timeframe && (
                          <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded-full">
                            {strategy.timeframe}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-3 mb-4">
                    {strategy.win_rate_estimate && (
                      <div className="flex items-center gap-2">
                        <ChartBarIcon className="h-4 w-4 text-gray-400" />
                        <span className="text-sm text-gray-300">Win Rate:</span>
                        <span className={`text-sm font-medium ${getWinRateColor(strategy.win_rate_estimate)}`}>
                          {strategy.win_rate_estimate}
                        </span>
                      </div>
                    )}
                    
                    {strategy.best_for && (
                      <div className="flex items-start gap-2">
                        <StarIcon className="h-4 w-4 text-gray-400 mt-0.5" />
                        <div>
                          <span className="text-sm text-gray-300">Best for:</span>
                          <p className="text-sm text-gray-400 mt-1">{strategy.best_for}</p>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="mb-4">
                    <p className="text-sm text-gray-400 line-clamp-3">
                      {strategy.prompt}
                    </p>
                  </div>

                  {strategy.risk_management && (
                    <div className="mb-4">
                      <div className="flex items-center gap-2 mb-2">
                        <ShieldCheckIcon className="h-4 w-4 text-gray-400" />
                        <span className="text-sm font-medium text-gray-300">Risk Management</span>
                      </div>
                      <p className="text-sm text-gray-400 line-clamp-2">
                        {strategy.risk_management}
                      </p>
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-4 border-t border-gray-700">
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      <ClockIcon className="h-4 w-4" />
                      <span>Updated {new Date(strategy.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <DocumentTextIcon className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-300 mb-2">No strategies found</h3>
            <p className="text-gray-400">
              {searchTerm || selectedCategory !== 'all' || selectedTimeframe !== 'all'
                ? 'Try adjusting your search or filters'
                : 'No strategies available in the library'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
