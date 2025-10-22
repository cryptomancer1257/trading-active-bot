'use client'

import { useEffect, useState } from 'react'
import { ChartBarIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import ActivityItem from './ActivityItem'

interface Activity {
  id: string
  type: 'TRADE' | 'RISK_ALERT' | 'BOT_EXECUTION'
  timestamp: string
  bot_name: string
  bot_id?: number
  subscription_id?: number
  [key: string]: any
}

interface DashboardStats {
  active_subscriptions: number
  trades_today: number
  total_pnl_today: number
  win_rate_today: number
}

export default function ActivityFeed() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [networkTab, setNetworkTab] = useState<'mainnet' | 'testnet'>('mainnet')  // Default to mainnet

  const fetchActivityData = async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true)
    else setLoading(true)

    try {
      const token = localStorage.getItem('access_token')
      
      // Build query params with network filter
      const activityParams = new URLSearchParams({
        limit: '20',
        hours: '24',
        network_filter: networkTab
      })
      const statsParams = new URLSearchParams({
        network_filter: networkTab
      })
      
      // Fetch activity and stats in parallel
      const [activityRes, statsRes] = await Promise.all([
        fetch(`/api/v1/dashboard/activity?${activityParams.toString()}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`/api/v1/dashboard/stats?${statsParams.toString()}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ])

      if (activityRes.ok && statsRes.ok) {
        const activityData = await activityRes.json()
        const statsData = await statsRes.json()
        
        setActivities(activityData.activities || [])
        setStats(statsData)
      }
    } catch (error) {
      console.error('Failed to fetch activity data:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchActivityData()
  }, [networkTab])  // Re-fetch when network tab changes

  // Auto-refresh every 120 seconds
  useEffect(() => {
    if (!autoRefresh) return

    const interval = setInterval(() => {
      fetchActivityData(true)
    }, 120000)

    return () => clearInterval(interval)
  }, [autoRefresh])

  const handleManualRefresh = () => {
    fetchActivityData(true)
  }

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-quantum-500 mx-auto mb-4"></div>
        <p className="text-gray-400">Loading activity feed...</p>
      </div>
    )
  }

  return (
    <div>
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

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-gradient-to-br from-blue-500/10 to-blue-600/10 border border-blue-500/20 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-blue-400 text-xs font-medium">Active Bots</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.active_subscriptions}</p>
              </div>
              <div className="text-blue-400 text-xl">🤖</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/10 border border-purple-500/20 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-purple-400 text-xs font-medium">Trades Today</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.trades_today}</p>
              </div>
              <div className="text-purple-400 text-xl">📊</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-green-500/10 to-green-600/10 border border-green-500/20 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-green-400 text-xs font-medium">Today P&L</p>
                <p className={`text-2xl font-bold mt-1 ${
                  stats.total_pnl_today >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  ${stats.total_pnl_today >= 0 ? '+' : ''}{stats.total_pnl_today}
                </p>
              </div>
              <div className="text-green-400 text-xl">💰</div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-cyan-500/10 to-cyan-600/10 border border-cyan-500/20 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-cyan-400 text-xs font-medium">Win Rate</p>
                <p className="text-2xl font-bold text-white mt-1">{stats.win_rate_today}%</p>
              </div>
              <div className="text-cyan-400 text-xl">🎯</div>
            </div>
          </div>
        </div>
      )}

      {/* Activity Feed Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-200 flex items-center">
          <ChartBarIcon className="h-5 w-5 mr-2" />
          Recent Activity (24h)
        </h3>
        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-sm text-gray-400">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded border-gray-600 text-quantum-500 focus:ring-quantum-500"
            />
            <span>Auto-refresh</span>
          </label>
          <button
            onClick={handleManualRefresh}
            disabled={refreshing}
            className="flex items-center space-x-1 text-sm text-quantum-400 hover:text-quantum-300 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Activity List */}
      {activities.length > 0 ? (
        <div className="space-y-3">
          {activities.map((activity) => (
            <ActivityItem key={activity.id} activity={activity} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-400">
          <div className="relative mx-auto h-16 w-16 mb-4">
            <ChartBarIcon className="h-16 w-16 text-gray-600 animate-pulse" />
            <div className="absolute inset-0 bg-gradient-to-r from-quantum-500/20 to-cyber-500/20 rounded-full blur-xl"></div>
          </div>
          <p className="text-gray-300 font-medium">No Recent Activity</p>
          <p className="text-sm mt-1 text-gray-500">Your bot trades and events will appear here</p>
        </div>
      )}
    </div>
  )
}

