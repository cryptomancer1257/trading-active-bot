'use client'

import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

interface Subscription {
  id: number
  instance_name: string
  user_principal_id: string | null
  user_id: number | null
  status: string
  trading_pair: string
  secondary_trading_pairs: string[]
  timeframe: string | null
  timeframes: string[]
  is_testnet: boolean
  network_type: string | null
  started_at: string | null
  expires_at: string | null
  last_run_at: string | null
  next_run_at: string | null
  payment_method: string | null
  total_trades: number
  open_positions: number
  closed_positions: number
  total_pnl: number
}

interface SubscriptionsData {
  bot_id: number
  bot_name: string
  subscriptions: Subscription[]
  pagination: {
    current_page: number
    total_pages: number
    total_items: number
    items_per_page: number
    has_next: boolean
    has_prev: boolean
  }
  filters_applied: {
    principal_id: string | null
    user_id: number | null
    trading_pair: string | null
    status: string | null
    start_date: string | null
    end_date: string | null
    search: string | null
  }
}

interface BotSubscriptionsProps {
  botId: number
}

export default function BotSubscriptions({ botId }: BotSubscriptionsProps) {
  const [subscriptions, setSubscriptions] = useState<SubscriptionsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [currentPage, setCurrentPage] = useState(1)
  const [itemsPerPage, setItemsPerPage] = useState(10)
  const [cancellingId, setCancellingId] = useState<number | null>(null)
  
  // Filter states
  const [filters, setFilters] = useState({
    principal_id: '',
    user_id: '',
    trading_pair: '',
    status: '',
    start_date: '',
    end_date: '',
    search: ''
  })

  const fetchSubscriptions = async () => {
    setLoading(true)
    try {
      const token = localStorage.getItem('access_token')
      const params = new URLSearchParams({
        page: currentPage.toString(),
        limit: itemsPerPage.toString()
      })

      // Add filters to params
      if (filters.principal_id) params.append('principal_id', filters.principal_id)
      if (filters.user_id) params.append('user_id', filters.user_id)
      if (filters.trading_pair) params.append('trading_pair', filters.trading_pair)
      if (filters.status) params.append('status', filters.status)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)
      if (filters.search) params.append('search', filters.search)

      const response = await fetch(
        `/api/bots/${botId}/subscriptions?${params}`,
        {
          headers: {
            Authorization: `Bearer ${token}`
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setSubscriptions(data)
      }
    } catch (error) {
      console.error('Error fetching subscriptions:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSubscriptions()
  }, [botId, currentPage, itemsPerPage])

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleApplyFilters = () => {
    setCurrentPage(1) // Reset to first page
    fetchSubscriptions()
  }

  const handleCancelSubscription = async (subscriptionId: number) => {
    if (!confirm('Are you sure you want to cancel this subscription? This action cannot be undone.')) {
      return
    }

    setCancellingId(subscriptionId)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(
        `/api/subscriptions/${subscriptionId}/cancel`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      )

      if (response.ok) {
        // Show success message
        alert('✅ Subscription cancelled successfully!')
        // Refresh subscriptions list
        fetchSubscriptions()
      } else {
        const error = await response.json()
        alert(`❌ Failed to cancel subscription: ${error.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error)
      alert('❌ Failed to cancel subscription. Please try again.')
    } finally {
      setCancellingId(null)
    }
  }

  const handleClearFilters = () => {
    setFilters({
      principal_id: '',
      user_id: '',
      trading_pair: '',
      status: '',
      start_date: '',
      end_date: '',
      search: ''
    })
    setCurrentPage(1)
    setTimeout(fetchSubscriptions, 100)
  }

  const getStatusBadgeColor = (status: string) => {
    switch (status?.toUpperCase()) {
      case 'ACTIVE':
        return 'bg-green-500/20 text-green-400 border-green-500'
      case 'PAUSED':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500'
      case 'CANCELLED':
        return 'bg-red-500/20 text-red-400 border-red-500'
      case 'EXPIRED':
        return 'bg-gray-500/20 text-gray-400 border-gray-500'
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500'
    }
  }

  const getPnlColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-400'
    if (pnl < 0) return 'text-red-400'
    return 'text-gray-400'
  }

  if (loading && !subscriptions) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Subscriptions</h2>
          <p className="text-gray-400 text-sm mt-1">
            {subscriptions?.pagination.total_items || 0} total subscriptions
          </p>
        </div>
        
        {/* Search */}
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search principal ID, instance name..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleApplyFilters()}
            className="px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
          />
          <button
            onClick={handleApplyFilters}
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
          >
            Search
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-white font-semibold">Filters</h3>
          <button
            onClick={handleClearFilters}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Clear all
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
            >
              <option value="">All Status</option>
              <option value="ACTIVE">Active</option>
              <option value="PAUSED">Paused</option>
              <option value="CANCELLED">Cancelled</option>
              <option value="EXPIRED">Expired</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Trading Pair</label>
            <input
              type="text"
              placeholder="e.g., BTC/USDT"
              value={filters.trading_pair}
              onChange={(e) => handleFilterChange('trading_pair', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Principal ID</label>
            <input
              type="text"
              placeholder="User principal ID"
              value={filters.principal_id}
              onChange={(e) => handleFilterChange('principal_id', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">User ID</label>
            <input
              type="number"
              placeholder="Developer user ID"
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Start Date (From)</label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => handleFilterChange('start_date', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">End Date (To)</label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => handleFilterChange('end_date', e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-purple-500"
            />
          </div>

          <div className="flex items-end">
            <button
              onClick={handleApplyFilters}
              className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-medium"
            >
              Apply Filters
            </button>
          </div>
        </div>
      </div>

      {/* Summary Info */}
      {subscriptions && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-lg px-6 py-4">
          <div className="grid grid-cols-4 gap-4">
            <div>
              <div className="text-sm text-gray-400">Total Subscriptions</div>
              <div className="text-2xl font-bold text-white mt-1">
                {subscriptions.pagination.total_items}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Current Page</div>
              <div className="text-2xl font-bold text-purple-400 mt-1">
                {subscriptions.pagination.current_page} / {subscriptions.pagination.total_pages}
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Showing</div>
              <div className="text-2xl font-bold text-blue-400 mt-1">
                {subscriptions.subscriptions.length} items
              </div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Per Page</div>
              <div className="text-2xl font-bold text-green-400 mt-1">
                {subscriptions.pagination.items_per_page}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Subscriptions Table */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-900 border-b border-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Instance Name
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Principal ID / User ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Trading Pairs
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Network
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Trades
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Expires
                </th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {subscriptions?.subscriptions.map((sub) => (
                <tr key={sub.id} className="hover:bg-gray-700/50 transition-colors">
                  <td className="px-4 py-4 text-sm text-white font-mono">
                    #{sub.id}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <div className="text-white font-medium">{sub.instance_name}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{sub.timeframe}</div>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    {sub.user_principal_id && (
                      <div className="text-white font-mono text-xs mb-1">
                        🔑 {sub.user_principal_id.substring(0, 16)}...
                      </div>
                    )}
                    {sub.user_id && (
                      <div className="text-gray-400 text-xs">
                        👤 User #{sub.user_id}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full border ${getStatusBadgeColor(sub.status)}`}>
                      {sub.status}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <div className="text-white font-medium">{sub.trading_pair}</div>
                    {sub.secondary_trading_pairs && sub.secondary_trading_pairs.length > 0 && (
                      <div className="text-xs text-gray-400 mt-1">
                        +{sub.secondary_trading_pairs.length} secondary: {sub.secondary_trading_pairs.join(', ')}
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <div className="flex items-center gap-1">
                      {sub.is_testnet ? (
                        <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-xs">
                          TESTNET
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-400 rounded text-xs">
                          MAINNET
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <div className="text-white font-medium">{sub.total_trades}</div>
                    <div className="text-xs text-gray-400 mt-0.5">
                      {sub.open_positions} open, {sub.closed_positions} closed
                    </div>
                  </td>
                  <td className="px-4 py-4 text-sm">
                    <div className={`font-bold ${getPnlColor(sub.total_pnl)}`}>
                      ${sub.total_pnl >= 0 ? '+' : ''}{sub.total_pnl.toFixed(2)}
                    </div>
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-400">
                    {sub.started_at ? new Date(sub.started_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-4 py-4 text-sm text-gray-400">
                    {sub.expires_at ? new Date(sub.expires_at).toLocaleDateString() : 'No expiry'}
                  </td>
                  <td className="px-4 py-4 text-sm text-center">
                    {sub.status === 'ACTIVE' ? (
                      <button
                        onClick={() => handleCancelSubscription(sub.id)}
                        disabled={cancellingId === sub.id}
                        className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                          cancellingId === sub.id
                            ? 'bg-gray-700 text-gray-400 cursor-not-allowed'
                            : 'bg-red-600 hover:bg-red-700 text-white'
                        }`}
                      >
                        {cancellingId === sub.id ? 'Cancelling...' : 'Cancel'}
                      </button>
                    ) : (
                      <span className="text-gray-500 text-xs">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {subscriptions?.subscriptions.length === 0 && (
          <div className="text-center py-12 text-gray-400">
            No subscriptions found
          </div>
        )}
      </div>

      {/* Pagination */}
      {subscriptions && subscriptions.pagination.total_items > 0 && (
        <div className="flex items-center justify-between px-4 py-4">
          <div className="text-sm text-gray-400">
            Showing{' '}
            <span className="font-semibold text-white">
              {((currentPage - 1) * itemsPerPage) + 1}
            </span>{' '}
            to{' '}
            <span className="font-semibold text-white">
              {Math.min(currentPage * itemsPerPage, subscriptions.pagination.total_items)}
            </span>{' '}
            of{' '}
            <span className="font-semibold text-white">
              {subscriptions.pagination.total_items}
            </span>{' '}
            subscriptions
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value))
                setCurrentPage(1)
              }}
              className="bg-gray-700 text-white text-sm rounded px-3 py-1.5 border border-gray-600 focus:outline-none focus:border-purple-500"
            >
              <option value={10}>10 per page</option>
              <option value={20}>20 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>

            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={!subscriptions.pagination.has_prev}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                subscriptions.pagination.has_prev
                  ? 'bg-gray-700 text-white hover:bg-gray-600'
                  : 'bg-gray-800 text-gray-500 cursor-not-allowed'
              }`}
            >
              Previous
            </button>

            <div className="flex items-center space-x-1">
              {Array.from({ length: Math.min(5, subscriptions.pagination.total_pages) }, (_, i) => {
                let pageNum
                if (subscriptions.pagination.total_pages <= 5) {
                  pageNum = i + 1
                } else if (currentPage <= 3) {
                  pageNum = i + 1
                } else if (currentPage >= subscriptions.pagination.total_pages - 2) {
                  pageNum = subscriptions.pagination.total_pages - 4 + i
                } else {
                  pageNum = currentPage - 2 + i
                }

                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`min-w-[2.5rem] px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                      currentPage === pageNum
                        ? 'bg-purple-600 text-white'
                        : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                    }`}
                  >
                    {pageNum}
                  </button>
                )
              })}
            </div>

            <button
              onClick={() => setCurrentPage(Math.min(subscriptions.pagination.total_pages, currentPage + 1))}
              disabled={!subscriptions.pagination.has_next}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                subscriptions.pagination.has_next
                  ? 'bg-gray-700 text-white hover:bg-gray-600'
                  : 'bg-gray-800 text-gray-500 cursor-not-allowed'
              }`}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

