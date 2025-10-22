'use client'

import { useState } from 'react'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { ChartBarIcon, CpuChipIcon, RocketLaunchIcon, BoltIcon, TrophyIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import Link from 'next/link'

export default function AnalyticsPage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.DEVELOPER 
  })

  const [networkTab, setNetworkTab] = useState<'mainnet' | 'testnet'>('mainnet')  // Default to mainnet

  // Fetch analytics data
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['developer-analytics', networkTab],  // Add networkTab to query key
    queryFn: async () => {
      const params = new URLSearchParams({
        days: '30',
        network_filter: networkTab
      })
      const response = await api.get(`/bots/analytics/overview?${params.toString()}`)
      return response.data
    },
    enabled: !!user,
    refetchInterval: 60000, // Refresh every minute
  })

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading Neural Analytics...</p>
        </div>
      </div>
    )
  }

  const stats = [
    {
      name: 'Total Entities',
      value: analytics?.total_bots || 0,
      icon: CpuChipIcon,
      gradient: 'from-quantum-500 to-purple-600',
      suffix: ''
    },
    {
      name: 'Active Deployments',
      value: analytics?.active_subscriptions || 0,
      icon: RocketLaunchIcon,
      gradient: 'from-cyber-500 to-blue-600',
      suffix: ''
    },
    {
      name: 'Total Trades',
      value: analytics?.total_transactions || 0,
      icon: BoltIcon,
      gradient: 'from-neural-500 to-green-600',
      suffix: ''
    },
    {
      name: 'Win Rate',
      value: analytics?.win_rate || 0,
      icon: TrophyIcon,
      gradient: 'from-yellow-500 to-orange-600',
      suffix: '%'
    },
  ]

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-4xl font-extrabold cyber-text mb-2">
          📊 Neural Analytics
        </h1>
        <p className="text-xl text-gray-400">
          Deep analysis of your AI entities' performance and behavior patterns
          {networkTab === 'mainnet' 
            ? ' - Live trading on real markets.' 
            : ' - Backtesting on testnet environments.'
          }
        </p>
      </div>

      {/* Network Type Tabs */}
      <div className="flex justify-center mb-6">
        <div className="inline-flex bg-dark-800 rounded-lg p-1 border border-quantum-500/20">
          <button
            onClick={() => setNetworkTab('mainnet')}
            className={`px-6 py-2 rounded-md font-medium transition-all ${
              networkTab === 'mainnet'
                ? 'bg-gradient-to-r from-neural-500 to-green-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            🟢 Mainnet (Live Trading)
          </button>
          <button
            onClick={() => setNetworkTab('testnet')}
            className={`px-6 py-2 rounded-md font-medium transition-all ${
              networkTab === 'testnet'
                ? 'bg-gradient-to-r from-cyber-500 to-blue-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-gray-200'
            }`}
          >
            🧪 Backtest (Testnet)
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat) => (
          <div key={stat.name} className="card-quantum p-6">
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-lg bg-gradient-to-r ${stat.gradient}`}>
                <stat.icon className="h-6 w-6 text-white" />
              </div>
            </div>
            <div className="text-3xl font-bold cyber-text mb-1">
              {stat.value.toLocaleString()}{stat.suffix}
            </div>
            <div className="text-sm text-gray-400">{stat.name}</div>
          </div>
        ))}
      </div>

      {/* Total P&L Card */}
      <div className="card-cyber p-8 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-400 mb-2">Total P&L (30 Days)</h3>
            <div className={`text-5xl font-bold ${(analytics?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {(analytics?.total_pnl || 0) >= 0 ? '+' : ''}{(analytics?.total_pnl || 0).toLocaleString()} USDT
            </div>
          </div>
          <ArrowTrendingUpIcon className={`h-16 w-16 ${(analytics?.total_pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`} />
        </div>
      </div>

      {/* Top Performing Bots */}
      <div className="card-quantum p-6">
        <h2 className="text-2xl font-bold cyber-text mb-6">🏆 Top Performing Entities</h2>
        
        {analytics?.top_bots && analytics.top_bots.length > 0 ? (
          <div className="space-y-4">
            {analytics.top_bots.map((bot: any, index: number) => (
              <Link 
                key={bot.id} 
                href={`/creator/entities/${bot.id}`}
                className="block p-4 rounded-lg bg-dark-800/50 hover:bg-dark-700/50 transition-all border border-quantum-500/20 hover:border-quantum-500/40"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="text-2xl font-bold text-quantum-400">#{index + 1}</div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-200">{bot.name}</h3>
                      <div className="text-sm text-gray-400">
                        {bot.active_subscriptions} active • {bot.total_trades} trades
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${bot.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {bot.pnl >= 0 ? '+' : ''}{bot.pnl.toLocaleString()} USDT
                    </div>
                    <div className="text-sm text-gray-400">
                      Win Rate: {bot.win_rate}%
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <ChartBarIcon className="h-16 w-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400">No trading data yet. Deploy your entities to see analytics.</p>
            <Link 
              href="/creator/entities"
              className="btn btn-cyber mt-4 inline-block"
            >
              View My Entities
            </Link>
          </div>
        )}
      </div>
    </div>
  )
}
