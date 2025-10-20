'use client'

import { useState, useMemo } from 'react'
import { MagnifyingGlassIcon, FunnelIcon, CpuChipIcon, ShieldCheckIcon, BoltIcon } from '@heroicons/react/24/outline'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import Link from 'next/link'

// Fetch bots from API with sorting
const fetchPublicBots = async (sortBy: string = 'performance', order: string = 'desc') => {
  const response = await api.get(`/bots/?limit=100&sort_by=${sortBy}&order=${order}`)
  return response.data
}

const categories = ["All", "Arbitrage", "Risk Management", "Trend Following", "Scalping", "Market Making", "Technical", "ML", "LLM"]
const riskLevels = ["All", "Low", "Medium", "High"]

// Helper to map bot data to display format
const mapBotToDisplay = (bot: any) => {
  // Map risk based on risk_percentage
  let risk = "Medium"
  const riskPct = bot.risk_percentage || 2
  if (riskPct < 2) risk = "Low"
  else if (riskPct > 5) risk = "High"
  
  // Map status
  const statusMap: Record<string, string> = {
    'APPROVED': 'Active',
    'ACTIVE': 'Active',
    'PENDING': 'Maintenance',
    'REJECTED': 'Offline',
    'INACTIVE': 'Offline'
  }
  const status = statusMap[bot.status] || 'Maintenance'
  
  // Map category
  const category = bot.bot_type || 'Technical'
  
  // Calculate gradient based on bot type
  const gradients: Record<string, string> = {
    'LLM': 'from-quantum-500 to-purple-600',
    'ML': 'from-neural-500 to-green-600',
    'DL': 'from-cyber-500 to-blue-600',
    'TECHNICAL': 'from-yellow-500 to-orange-600'
  }
  const gradient = gradients[bot.bot_type] || 'from-gray-500 to-gray-600'
  
  // Use actual performance data from backend
  const totalPnl = parseFloat(bot.total_pnl || 0)
  const winRate = parseFloat(bot.win_rate || 0)
  const totalTrades = parseInt(bot.total_trades || 0)
  const winningTrades = parseInt(bot.winning_trades || 0)
  
  // Format performance display - prioritize P&L if available
  let performanceDisplay = '0.0%'
  if (totalPnl !== 0) {
    // Show P&L if there are transactions
    const performanceSign = totalPnl >= 0 ? '+' : ''
    performanceDisplay = `${performanceSign}$${totalPnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  } else if (winRate > 0) {
    // Fallback to win rate if no P&L but has win rate
    performanceDisplay = `${winRate.toFixed(1)}%`
  }
  
  return {
    id: bot.id,
    name: bot.name,
    description: bot.description || 'No description available',
    category,
    performance: performanceDisplay,
    performanceValue: totalPnl, // For sorting
    winRate: winRate,
    totalPnl: totalPnl,
    totalTrades: totalTrades,
    winningTrades: winningTrades,
    risk,
    status,
    creator: bot.developer?.username || 'Unknown',
    deployments: bot.total_subscribers || 0,
    gradient
  }
}

export default function ArsenalPage() {
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("All")
  const [selectedRisk, setSelectedRisk] = useState("All")
  const [currentPage, setCurrentPage] = useState(1)
  const [sortBy, setSortBy] = useState<'performance' | 'deployments' | 'name'>('performance')
  const botsPerPage = 10

  // Fetch bots from API with sorting
  const { data: botsData, isLoading, error } = useQuery({
    queryKey: ['public-bots', sortBy],
    queryFn: () => {
      // Map frontend sortBy to backend sort_by
      const backendSortBy = sortBy === 'performance' ? 'total_pnl' : sortBy === 'deployments' ? 'rating' : 'name'
      return fetchPublicBots(backendSortBy, 'desc')
    },
    staleTime: 60000, // Cache for 1 minute
  })

  // Map, filter, and paginate bots (backend already sorted)
  const { filteredBots, totalPages, allFilteredCount, allFilteredBots } = useMemo(() => {
    if (!botsData?.bots) return { filteredBots: [], totalPages: 0, allFilteredCount: 0, allFilteredBots: [] }
    
    const mappedBots = botsData.bots.map(mapBotToDisplay)
    
    // Filter bots (backend already sorted)
    const filtered = mappedBots.filter((bot: any) => {
      const matchesSearch = bot.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           bot.description.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesCategory = selectedCategory === "All" || bot.category === selectedCategory
      const matchesRisk = selectedRisk === "All" || bot.risk === selectedRisk
      
      return matchesSearch && matchesCategory && matchesRisk
    })
    
    // No need to sort here - backend already sorted by total_pnl
    
    const totalPages = Math.ceil(filtered.length / botsPerPage)
    const startIndex = (currentPage - 1) * botsPerPage
    const paginatedBots = filtered.slice(startIndex, startIndex + botsPerPage)
    
    return { 
      filteredBots: paginatedBots, 
      totalPages, 
      allFilteredCount: filtered.length,
      allFilteredBots: filtered // Keep all filtered bots for stats calculation
    }
  }, [botsData, searchTerm, selectedCategory, selectedRisk, currentPage])

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case "Low": return "text-neural-400 bg-neural-500/10"
      case "Medium": return "text-yellow-400 bg-yellow-500/10"
      case "High": return "text-danger-400 bg-danger-500/10"
      default: return "text-gray-400 bg-gray-500/10"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Active": return "text-neural-400 bg-neural-500/10"
      case "Maintenance": return "text-yellow-400 bg-yellow-500/10"
      case "Offline": return "text-danger-400 bg-danger-500/10"
      default: return "text-gray-400 bg-gray-500/10"
    }
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold cyber-text mb-4">
            🤖 AI Entity Arsenal
          </h1>
        </div>
        <div className="card-quantum p-12 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading AI Entities...</p>
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-extrabold cyber-text mb-4">
            🤖 AI Entity Arsenal
          </h1>
        </div>
        <div className="card-quantum p-12 text-center">
          <CpuChipIcon className="h-16 w-16 text-danger-500 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-300 mb-2">Failed to Load Entities</h3>
          <p className="text-gray-400 mb-4">
            {error instanceof Error ? error.message : 'An error occurred while fetching bots'}
          </p>
          <button 
            onClick={() => window.location.reload()} 
            className="btn btn-primary"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold cyber-text mb-4">
          🤖 AI Entity Arsenal
        </h1>
        <p className="text-xl text-gray-400 max-w-3xl mx-auto">
          Discover and analyze autonomous trading entities created by the neural network community.
          Each AI entity represents years of algorithmic evolution.
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Total Bots: {botsData?.total || 0} | Showing: {filteredBots.length} of {allFilteredCount} (Page {currentPage}/{totalPages})
        </p>
      </div>

      {/* Search and Filters */}
      <div className="card-quantum p-6 mb-8 animate-fade-in">
        <div className="flex flex-col lg:flex-row gap-4 items-center">
          {/* Search */}
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search AI entities..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setCurrentPage(1) // Reset to page 1 on search
              }}
              className="form-input pl-10 w-full"
            />
          </div>

          {/* Sort By */}
          <div className="flex items-center space-x-2">
            <BoltIcon className="h-5 w-5 text-gray-400" />
            <select
              value={sortBy}
              onChange={(e) => {
                setSortBy(e.target.value as 'performance' | 'deployments' | 'name')
                setCurrentPage(1) // Reset to page 1 on sort change
              }}
              className="form-input"
            >
              <option value="performance">🏆 Top Performance</option>
              <option value="deployments">👥 Most Popular</option>
              <option value="name">📝 Name (A-Z)</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value)
                setCurrentPage(1) // Reset to page 1 on filter change
              }}
              className="form-input"
            >
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>

          {/* Risk Filter */}
          <div className="flex items-center space-x-2">
            <ShieldCheckIcon className="h-5 w-5 text-gray-400" />
            <select
              value={selectedRisk}
              onChange={(e) => {
                setSelectedRisk(e.target.value)
                setCurrentPage(1) // Reset to page 1 on filter change
              }}
              className="form-input"
            >
              {riskLevels.map(risk => (
                <option key={risk} value={risk}>Risk: {risk}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <div className="text-3xl font-bold cyber-text animate-neural-pulse">
            {allFilteredCount}
          </div>
          <div className="text-sm text-gray-400 mt-1">Active Entities</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div className="text-3xl font-bold text-neural-400 animate-neural-pulse">
            {allFilteredBots.reduce((sum: number, bot: any) => sum + bot.deployments, 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-400 mt-1">Total Deployments</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <div className="text-3xl font-bold text-cyber-400 animate-neural-pulse">
            {(() => {
              // Only count bots with win_rate > 0
              const botsWithWinRate = allFilteredBots.filter((bot: any) => bot.winRate > 0)
              if (botsWithWinRate.length === 0) return 0
              const avgWinRate = botsWithWinRate.reduce((sum: number, bot: any) => sum + bot.winRate, 0) / botsWithWinRate.length
              return Math.round(avgWinRate)
            })()}%
          </div>
          <div className="text-sm text-gray-400 mt-1">Avg Win Rate</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.4s' }}>
          <div className="text-3xl font-bold text-yellow-400 animate-neural-pulse">
            {allFilteredBots.filter((bot: any) => bot.status === 'Active').length}
          </div>
          <div className="text-sm text-gray-400 mt-1">Online Now</div>
        </div>
      </div>

      {/* AI Entities Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredBots.map((bot: any, index: number) => (
          <div
            key={bot.id}
            className="card-quantum p-6 hover:shadow-2xl hover:shadow-quantum-500/20 transition-all duration-300 transform hover:-translate-y-1 animate-fade-in"
            style={{ animationDelay: `${0.5 + index * 0.1}s` }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 rounded-lg overflow-hidden shadow-lg">
                  {bot.image_url ? (
                    <img 
                      src={bot.image_url} 
                      alt={bot.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className={`w-full h-full bg-gradient-to-r ${bot.gradient} flex items-center justify-center`}>
                      <CpuChipIcon className="h-6 w-6 text-white" />
                    </div>
                  )}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-200">{bot.name}</h3>
                  <p className="text-sm text-gray-400">by {bot.creator}</p>
                </div>
              </div>
              <div className="flex flex-col items-end space-y-2">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(bot.status)}`}>
                  {bot.status}
                </span>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRiskColor(bot.risk)}`}>
                  {bot.risk} Risk
                </span>
              </div>
            </div>

            {/* Description */}
            <p className="text-gray-400 mb-4 leading-relaxed">
              {bot.description}
            </p>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="text-lg font-bold text-neural-400">{bot.winRate.toFixed(1)}%</div>
                <div className="text-xs text-gray-500">Win Rate</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-cyber-400">{bot.performance}</div>
                <div className="text-xs text-gray-500">P&L</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-quantum-400">{bot.category}</div>
                <div className="text-xs text-gray-500">Category</div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex space-x-3">
              <Link 
                href={`/creator/entities/${bot.id}`} 
                className="btn btn-primary flex-1 py-2 text-sm text-center"
                onClick={(e) => {
                  // Set analytics tab when clicking View Performance
                  localStorage.setItem('bot-detail-tab', 'analytics')
                }}
              >
                📊 View Performance
              </Link>
              <Link 
                href={`/creator/entities/${bot.id}`}
                className="btn btn-secondary flex-1 py-2 text-sm text-center"
                onClick={(e) => {
                  // Set subscriptions tab when clicking View Subscriptions
                  localStorage.setItem('bot-detail-tab', 'subscriptions')
                }}
              >
                👥 View Subscriptions
              </Link>
              <Link 
                href={`/marketplace/${bot.id}`} 
                className="btn btn-cyber px-4 py-2 text-sm"
                title="Subscribe to bot"
              >
                ⚡
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* No Results */}
      {filteredBots.length === 0 && allFilteredCount === 0 && (
        <div className="card-quantum p-12 text-center">
          <CpuChipIcon className="h-16 w-16 text-gray-600 mx-auto mb-4 animate-neural-pulse" />
          <h3 className="text-xl font-bold text-gray-300 mb-2">No AI Entities Found</h3>
          <p className="text-gray-400">
            Try adjusting your search criteria or explore different categories.
          </p>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="card-quantum p-6 mt-8 flex items-center justify-between">
          <div className="text-sm text-gray-400">
            Showing {((currentPage - 1) * botsPerPage) + 1} - {Math.min(currentPage * botsPerPage, allFilteredCount)} of {allFilteredCount} bots
          </div>
          
          <div className="flex space-x-2">
            {/* Previous Button */}
            <button
              onClick={() => {
                setCurrentPage(prev => Math.max(1, prev - 1))
                window.scrollTo({ top: 0, behavior: 'smooth' })
              }}
              disabled={currentPage === 1}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                currentPage === 1
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-quantum-600 hover:bg-quantum-700 text-white'
              }`}
            >
              ← Previous
            </button>

            {/* Page Numbers */}
            <div className="hidden md:flex space-x-2">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
                // Show first page, last page, current page, and pages around current
                if (
                  page === 1 ||
                  page === totalPages ||
                  (page >= currentPage - 1 && page <= currentPage + 1)
                ) {
                  return (
                    <button
                      key={page}
                      onClick={() => {
                        setCurrentPage(page)
                        window.scrollTo({ top: 0, behavior: 'smooth' })
                      }}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        currentPage === page
                          ? 'bg-quantum-600 text-white'
                          : 'bg-gray-700 hover:bg-gray-600 text-gray-300'
                      }`}
                    >
                      {page}
                    </button>
                  )
                } else if (
                  (page === currentPage - 2 && page > 1) ||
                  (page === currentPage + 2 && page < totalPages)
                ) {
                  return <span key={page} className="px-2 text-gray-500">...</span>
                }
                return null
              })}
            </div>

            {/* Next Button */}
            <button
              onClick={() => {
                setCurrentPage(prev => Math.min(totalPages, prev + 1))
                window.scrollTo({ top: 0, behavior: 'smooth' })
              }}
              disabled={currentPage === totalPages}
              className={`px-4 py-2 rounded-lg font-medium transition-all ${
                currentPage === totalPages
                  ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                  : 'bg-quantum-600 hover:bg-quantum-700 text-white'
              }`}
            >
              Next →
            </button>
          </div>

          {/* Mobile Page Info */}
          <div className="md:hidden text-sm text-gray-400">
            Page {currentPage} of {totalPages}
          </div>
        </div>
      )}

      {/* Floating Neural Particles */}
      <div className="fixed top-32 left-16 w-1 h-1 bg-quantum-500 rounded-full animate-neural-pulse opacity-40"></div>
      <div className="fixed top-48 right-24 w-1.5 h-1.5 bg-cyber-400 rounded-full animate-neural-pulse opacity-50" style={{ animationDelay: '1s' }}></div>
      <div className="fixed bottom-32 left-24 w-2 h-2 bg-neural-500 rounded-full animate-neural-pulse opacity-30" style={{ animationDelay: '2s' }}></div>
    </div>
  )
}
