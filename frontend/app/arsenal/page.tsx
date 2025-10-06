'use client'

import { useState, useMemo } from 'react'
import { MagnifyingGlassIcon, FunnelIcon, CpuChipIcon, ShieldCheckIcon, BoltIcon } from '@heroicons/react/24/outline'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import Link from 'next/link'

// Fetch bots from API
const fetchPublicBots = async () => {
  const response = await api.get('/bots/?limit=100')
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
  
  return {
    id: bot.id,
    name: bot.name,
    description: bot.description || 'No description available',
    category,
    performance: `+${bot.average_rating || 0}%`,
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

  // Fetch bots from API
  const { data: botsData, isLoading, error } = useQuery({
    queryKey: ['public-bots'],
    queryFn: fetchPublicBots,
    staleTime: 60000, // Cache for 1 minute
  })

  // Map and filter bots
  const filteredBots = useMemo(() => {
    if (!botsData?.bots) return []
    
    const mappedBots = botsData.bots.map(mapBotToDisplay)
    
    return mappedBots.filter((bot: any) => {
      const matchesSearch = bot.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           bot.description.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesCategory = selectedCategory === "All" || bot.category === selectedCategory
      const matchesRisk = selectedRisk === "All" || bot.risk === selectedRisk
      
      return matchesSearch && matchesCategory && matchesRisk
    })
  }, [botsData, searchTerm, selectedCategory, selectedRisk])

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
          Total Bots: {botsData?.total || 0} | Showing: {filteredBots.length}
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
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input pl-10 w-full"
            />
          </div>

          {/* Category Filter */}
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
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
              onChange={(e) => setSelectedRisk(e.target.value)}
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
            {filteredBots.length}
          </div>
          <div className="text-sm text-gray-400 mt-1">Active Entities</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div className="text-3xl font-bold text-neural-400 animate-neural-pulse">
            {filteredBots.reduce((sum, bot) => sum + bot.deployments, 0).toLocaleString()}
          </div>
          <div className="text-sm text-gray-400 mt-1">Total Deployments</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.3s' }}>
          <div className="text-3xl font-bold text-cyber-400 animate-neural-pulse">
            {Math.round(filteredBots.reduce((sum, bot) => sum + parseFloat(bot.performance.replace('%', '').replace('+', '')), 0) / filteredBots.length)}%
          </div>
          <div className="text-sm text-gray-400 mt-1">Avg Performance</div>
        </div>
        <div className="card-cyber p-6 text-center animate-fade-in" style={{ animationDelay: '0.4s' }}>
          <div className="text-3xl font-bold text-yellow-400 animate-neural-pulse">
            {filteredBots.filter(bot => bot.status === 'Active').length}
          </div>
          <div className="text-sm text-gray-400 mt-1">Online Now</div>
        </div>
      </div>

      {/* AI Entities Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredBots.map((bot, index) => (
          <div
            key={bot.id}
            className="card-quantum p-6 hover:shadow-2xl hover:shadow-quantum-500/20 transition-all duration-300 transform hover:-translate-y-1 animate-fade-in"
            style={{ animationDelay: `${0.5 + index * 0.1}s` }}
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`p-3 rounded-lg bg-gradient-to-r ${bot.gradient} shadow-lg`}>
                  <CpuChipIcon className="h-6 w-6 text-white" />
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
                <div className="text-lg font-bold text-neural-400">{bot.performance}</div>
                <div className="text-xs text-gray-500">Performance</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-cyber-400">{bot.deployments.toLocaleString()}</div>
                <div className="text-xs text-gray-500">Deployments</div>
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
                  // Set analytics tab when clicking
                  localStorage.setItem('bot-detail-tab', 'analytics')
                }}
              >
                🧠 Analyze Entity
              </Link>
              <Link 
                href={`/creator/entities/${bot.id}`}
                className="btn btn-secondary flex-1 py-2 text-sm text-center"
                onClick={(e) => {
                  // Set analytics tab for performance view
                  localStorage.setItem('bot-detail-tab', 'analytics')
                }}
              >
                📊 View Performance
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
      {filteredBots.length === 0 && (
        <div className="card-quantum p-12 text-center">
          <CpuChipIcon className="h-16 w-16 text-gray-600 mx-auto mb-4 animate-neural-pulse" />
          <h3 className="text-xl font-bold text-gray-300 mb-2">No AI Entities Found</h3>
          <p className="text-gray-400">
            Try adjusting your search criteria or explore different categories.
          </p>
        </div>
      )}

      {/* Floating Neural Particles */}
      <div className="fixed top-32 left-16 w-1 h-1 bg-quantum-500 rounded-full animate-neural-pulse opacity-40"></div>
      <div className="fixed top-48 right-24 w-1.5 h-1.5 bg-cyber-400 rounded-full animate-neural-pulse opacity-50" style={{ animationDelay: '1s' }}></div>
      <div className="fixed bottom-32 left-24 w-2 h-2 bg-neural-500 rounded-full animate-neural-pulse opacity-30" style={{ animationDelay: '2s' }}></div>
    </div>
  )
}
