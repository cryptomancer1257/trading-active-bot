'use client'

import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { 
  BoltIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  FireIcon,
  ChartBarIcon 
} from '@heroicons/react/24/outline'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'

// Top trading pairs to monitor
const WATCH_LIST = [
  'BTCUSDT',
  'ETHUSDT',
  'BNBUSDT',
  'SOLUSDT',
  'XRPUSDT',
  'ADAUSDT',
  'DOGEUSDT',
  'MATICUSDT'
]

interface MarketData {
  symbol: string
  price: string
  priceChangePercent: string
  volume: string
  high: string
  low: string
}

export default function IntelligencePage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.DEVELOPER 
  })

  const [sortBy, setSortBy] = useState<'change' | 'volume'>('change')

  // Fetch market data for all symbols
  const { data: marketData, isLoading } = useQuery({
    queryKey: ['market-intelligence'],
    queryFn: async () => {
      // Fetch 24hr ticker data for all symbols
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr')
      const allTickers = await response.json()
      
      // Filter for our watchlist
      const watchlistData = allTickers.filter((ticker: any) => 
        WATCH_LIST.includes(ticker.symbol)
      )
      
      return watchlistData.map((ticker: any) => ({
        symbol: ticker.symbol,
        price: parseFloat(ticker.lastPrice).toFixed(2),
        priceChangePercent: parseFloat(ticker.priceChangePercent).toFixed(2),
        volume: parseFloat(ticker.volume).toFixed(0),
        high: parseFloat(ticker.highPrice).toFixed(2),
        low: parseFloat(ticker.lowPrice).toFixed(2),
        quoteVolume: parseFloat(ticker.quoteVolume)
      }))
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Accessing Market Intelligence...</p>
        </div>
      </div>
    )
  }

  // Calculate market stats
  const gainers = marketData?.filter((m: any) => parseFloat(m.priceChangePercent) > 0) || []
  const losers = marketData?.filter((m: any) => parseFloat(m.priceChangePercent) < 0) || []
  const avgChange = marketData?.reduce((acc: number, m: any) => acc + parseFloat(m.priceChangePercent), 0) / (marketData?.length || 1) || 0

  // Sort market data
  const sortedData = [...(marketData || [])].sort((a: any, b: any) => {
    if (sortBy === 'change') {
      return parseFloat(b.priceChangePercent) - parseFloat(a.priceChangePercent)
    } else {
      return b.quoteVolume - a.quoteVolume
    }
  })

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-4xl font-extrabold cyber-text mb-2">
          🧠 Market Intelligence
        </h1>
        <p className="text-xl text-gray-400">
          Real-time market insights powered by quantum neural networks
        </p>
      </div>

      {/* Market Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="card-quantum p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-gradient-to-r from-green-500 to-emerald-600">
              <ArrowTrendingUpIcon className="h-6 w-6 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-green-400 mb-1">
            {gainers.length}
          </div>
          <div className="text-sm text-gray-400">Gainers (24h)</div>
        </div>

        <div className="card-quantum p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-gradient-to-r from-red-500 to-rose-600">
              <ArrowTrendingDownIcon className="h-6 w-6 text-white" />
            </div>
          </div>
          <div className="text-3xl font-bold text-red-400 mb-1">
            {losers.length}
          </div>
          <div className="text-sm text-gray-400">Losers (24h)</div>
        </div>

        <div className="card-quantum p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 rounded-lg bg-gradient-to-r from-cyber-500 to-blue-600">
              <ChartBarIcon className="h-6 w-6 text-white" />
            </div>
          </div>
          <div className={`text-3xl font-bold mb-1 ${avgChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {avgChange >= 0 ? '+' : ''}{avgChange.toFixed(2)}%
          </div>
          <div className="text-sm text-gray-400">Avg Change (24h)</div>
        </div>
      </div>

      {/* Market Data Table */}
      <div className="card-cyber p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold cyber-text">📊 Live Market Data</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setSortBy('change')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                sortBy === 'change'
                  ? 'bg-quantum-500 text-white'
                  : 'bg-dark-700 text-gray-400 hover:bg-dark-600'
              }`}
            >
              Sort by Change
            </button>
            <button
              onClick={() => setSortBy('volume')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                sortBy === 'volume'
                  ? 'bg-quantum-500 text-white'
                  : 'bg-dark-700 text-gray-400 hover:bg-dark-600'
              }`}
            >
              Sort by Volume
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-quantum-500 mx-auto mb-4"></div>
            <p className="text-gray-400">Loading market data...</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-dark-600">
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Symbol</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Price</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">24h Change</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">24h High</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">24h Low</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Volume</th>
                </tr>
              </thead>
              <tbody>
                {sortedData.map((market: any) => {
                  const change = parseFloat(market.priceChangePercent)
                  const isPositive = change >= 0
                  
                  return (
                    <tr 
                      key={market.symbol}
                      className="border-b border-dark-700/50 hover:bg-dark-800/50 transition-colors"
                    >
                      <td className="py-4 px-4">
                        <div className="flex items-center space-x-2">
                          {Math.abs(change) > 5 && (
                            <FireIcon className={`h-4 w-4 ${isPositive ? 'text-green-400' : 'text-red-400'}`} />
                          )}
                          <span className="font-semibold text-gray-200">
                            {market.symbol.replace('USDT', '/USDT')}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-gray-200">
                        ${parseFloat(market.price).toLocaleString()}
                      </td>
                      <td className="py-4 px-4 text-right">
                        <span className={`font-bold ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                          {isPositive ? '+' : ''}{change}%
                        </span>
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-gray-400">
                        ${parseFloat(market.high).toLocaleString()}
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-gray-400">
                        ${parseFloat(market.low).toLocaleString()}
                      </td>
                      <td className="py-4 px-4 text-right font-mono text-gray-400">
                        {parseFloat(market.volume).toLocaleString()}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        <div className="mt-4 text-xs text-gray-500 text-center">
          🔄 Auto-refreshing every 10 seconds • Data from Binance
        </div>
      </div>
    </div>
  )
}
