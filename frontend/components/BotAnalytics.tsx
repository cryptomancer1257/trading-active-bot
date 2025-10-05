'use client'

import { useState, useEffect } from 'react'
import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  UsersIcon,
  CurrencyDollarIcon,
  CheckCircleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import config from '@/lib/config'

interface AnalyticsData {
  bot_id: number
  bot_name: string
  period_days: number
  summary: {
    total_subscriptions: number
    active_subscriptions: number
    total_transactions: number
    winning_trades: number
    losing_trades: number
    win_rate: number
    total_pnl: number
  }
  chart_data: Array<{
    date: string
    transactions: number
    pnl: number
  }>
  recent_transactions: Array<{
    id: number
    trading_pair: string
    action: string
    quantity: number
    entry_price: number
    exit_price: number
    realized_pnl: number
    created_at: string
    closed_at: string | null
  }>
}

interface BotAnalyticsProps {
  botId: number
}

export default function BotAnalytics({ botId }: BotAnalyticsProps) {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [periodDays, setPeriodDays] = useState(30)

  useEffect(() => {
    fetchAnalytics()
  }, [botId, periodDays])

  const fetchAnalytics = async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `${config.studioBaseUrl}/bots/${botId}/analytics?days=${periodDays}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      )

      if (!response.ok) {
        throw new Error('Failed to fetch analytics')
      }

      const data = await response.json()
      setAnalytics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  if (error || !analytics) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
        <p className="text-red-400">{error || 'Failed to load analytics'}</p>
      </div>
    )
  }

  const { summary, chart_data, recent_transactions } = analytics

  return (
    <div className="space-y-6">
      {/* Period Selector */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Analytics</h2>
        <div className="flex space-x-2">
          {[7, 30, 90].map((days) => (
            <button
              key={days}
              onClick={() => setPeriodDays(days)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                periodDays === days
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              }`}
            >
              {days}D
            </button>
          ))}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Subscriptions */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Subscriptions</p>
              <p className="text-3xl font-bold text-white mt-2">
                {summary.active_subscriptions}
                <span className="text-sm text-gray-400 ml-1">
                  / {summary.total_subscriptions}
                </span>
              </p>
              <p className="text-xs text-gray-500 mt-1">Active / Total</p>
            </div>
            <UsersIcon className="h-10 w-10 text-blue-400" />
          </div>
        </div>

        {/* Total Transactions */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Transactions</p>
              <p className="text-3xl font-bold text-white mt-2">
                {summary.total_transactions}
              </p>
              <p className="text-xs text-gray-500 mt-1">Last {periodDays} days</p>
            </div>
            <ChartBarIcon className="h-10 w-10 text-purple-400" />
          </div>
        </div>

        {/* Win Rate */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Win Rate</p>
              <p className="text-3xl font-bold text-white mt-2">
                {summary.win_rate.toFixed(1)}%
              </p>
              <p className="text-xs text-gray-500 mt-1">
                <span className="text-green-400">{summary.winning_trades}W</span>
                {' / '}
                <span className="text-red-400">{summary.losing_trades}L</span>
              </p>
            </div>
            {summary.win_rate >= 50 ? (
              <ArrowTrendingUpIcon className="h-10 w-10 text-green-400" />
            ) : (
              <ArrowTrendingDownIcon className="h-10 w-10 text-red-400" />
            )}
          </div>
        </div>

        {/* Total P&L */}
        <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total P&L</p>
              <p
                className={`text-3xl font-bold mt-2 ${
                  summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {summary.total_pnl >= 0 ? '+' : ''}
                ${summary.total_pnl.toFixed(2)}
              </p>
              <p className="text-xs text-gray-500 mt-1">Realized</p>
            </div>
            <CurrencyDollarIcon
              className={`h-10 w-10 ${
                summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
              }`}
            />
          </div>
        </div>
      </div>

      {/* Performance Chart */}
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Performance Over Time</h3>
        
        {chart_data.length > 0 ? (
          <div className="space-y-4">
            {/* Simple bar chart */}
            <div className="h-64 flex items-end space-x-2">
              {chart_data.map((item, index) => {
                const maxPnl = Math.max(...chart_data.map((d) => Math.abs(d.pnl)))
                const height = maxPnl > 0 ? (Math.abs(item.pnl) / maxPnl) * 100 : 0
                const isPositive = item.pnl >= 0

                return (
                  <div
                    key={index}
                    className="flex-1 flex flex-col justify-end items-center group relative"
                  >
                    {/* Tooltip */}
                    <div className="hidden group-hover:block absolute bottom-full mb-2 px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-xs whitespace-nowrap z-10">
                      <p className="text-gray-400">
                        {new Date(item.date).toLocaleDateString()}
                      </p>
                      <p className="text-white font-semibold">
                        {item.transactions} trades
                      </p>
                      <p
                        className={
                          isPositive ? 'text-green-400' : 'text-red-400'
                        }
                      >
                        {isPositive ? '+' : ''}${item.pnl.toFixed(2)}
                      </p>
                    </div>

                    {/* Bar */}
                    <div
                      className={`w-full rounded-t transition-all ${
                        isPositive ? 'bg-green-500' : 'bg-red-500'
                      } group-hover:opacity-80`}
                      style={{ height: `${height}%` }}
                    />
                  </div>
                )
              })}
            </div>

            {/* Date labels (show every 3rd date) */}
            <div className="flex space-x-2 text-xs text-gray-500">
              {chart_data.map((item, index) => (
                <div key={index} className="flex-1 text-center">
                  {index % 3 === 0
                    ? new Date(item.date).toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                      })
                    : ''}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            No trading data available for this period
          </div>
        )}
      </div>

      {/* Recent Transactions */}
      <div className="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-4">Recent Transactions</h3>
        
        {recent_transactions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="text-xs text-gray-400 uppercase border-b border-gray-700">
                <tr>
                  <th className="py-3 px-4 text-left">Date</th>
                  <th className="py-3 px-4 text-left">Pair</th>
                  <th className="py-3 px-4 text-center">Action</th>
                  <th className="py-3 px-4 text-right">Quantity</th>
                  <th className="py-3 px-4 text-right">Entry</th>
                  <th className="py-3 px-4 text-right">Exit</th>
                  <th className="py-3 px-4 text-right">P&L</th>
                </tr>
              </thead>
              <tbody className="text-sm">
                {recent_transactions.map((tx) => (
                  <tr key={tx.id} className="border-b border-gray-700 hover:bg-gray-700/50">
                    <td className="py-3 px-4 text-gray-300">
                      {new Date(tx.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-white font-mono">
                      {tx.trading_pair}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium ${
                          tx.action === 'BUY'
                            ? 'bg-green-900/50 text-green-400'
                            : 'bg-red-900/50 text-red-400'
                        }`}
                      >
                        {tx.action === 'BUY' ? (
                          <CheckCircleIcon className="h-3 w-3 mr-1" />
                        ) : (
                          <XCircleIcon className="h-3 w-3 mr-1" />
                        )}
                        {tx.action}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-gray-300">
                      {tx.quantity.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-300">
                      ${tx.entry_price.toFixed(2)}
                    </td>
                    <td className="py-3 px-4 text-right text-gray-300">
                      {tx.exit_price > 0 ? `$${tx.exit_price.toFixed(2)}` : '-'}
                    </td>
                    <td className="py-3 px-4 text-right font-semibold">
                      <span
                        className={
                          tx.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'
                        }
                      >
                        {tx.realized_pnl >= 0 ? '+' : ''}$
                        {tx.realized_pnl.toFixed(2)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12 text-gray-400">
            No transactions yet
          </div>
        )}
      </div>
    </div>
  )
}

