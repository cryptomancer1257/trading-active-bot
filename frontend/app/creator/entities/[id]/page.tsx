'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { 
  ArrowLeftIcon,
  PencilIcon,
  Cog6ToothIcon,
  SparklesIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon, ClockIcon, XCircleIcon, ArchiveBoxIcon } from '@heroicons/react/24/solid'
import Link from 'next/link'
import BotPromptsTab from '@/components/BotPromptsTab'
import RiskManagementTab from '@/components/RiskManagementTab'
import toast from 'react-hot-toast'
import config from '@/lib/config'
import { useAuth } from '@/contexts/AuthContext'

type TabType = 'overview' | 'prompts' | 'risk-management' | 'settings' | 'analytics'

export default function BotDetailPage() {
  const router = useRouter()
  const params = useParams()
  const botId = params?.id as string
  const { user } = useAuth()

  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [isStartingTrial, setIsStartingTrial] = useState(false)
  const [trialConfig, setTrialConfig] = useState({
    tradingPair: 'BTC/USDT',
    networkType: 'TESTNET'
  })
  const [botLogs, setBotLogs] = useState<any[]>([])
  const [isLoadingLogs, setIsLoadingLogs] = useState(false)

  // Mock bot data for testing
  const bot = {
    id: parseInt(botId || '48'),
    name: '🚀 Futures Quantum Entity',
    description: 'Advanced futures trading with LLM AI analysis, leverage, and quantum risk management',
    bot_type: 'FUTURES',
    version: '1.0.0',
    status: 'APPROVED',
    exchange_type: 'BINANCE',
    trading_pair: 'BTC/USDT',
    timeframe: '1h',
    leverage: 10,
    created_at: '2025-09-27T08:39:45'
  }

  const handleStartFreeTrial = async () => {
    if (isStartingTrial) return
    
    setIsStartingTrial(true)
    
    try {
      // Calculate start and end dates for 24h free trial
      const startDate = new Date()
      const endDate = new Date(startDate.getTime() + 24 * 60 * 60 * 1000) // 24 hours later
      
      // Get current user ID from auth context
      const currentUserId = user?.id || 1 // Fallback to admin user if not authenticated
      
      const subscriptionData = {
        user_principal_id: `trial_user_${Date.now()}`, // Generate unique principal ID for trial
        user_id: currentUserId, // Add developer user_id
        bot_id: bot.id,
        subscription_start: startDate.toISOString(),
        subscription_end: endDate.toISOString(),
        is_testnet: trialConfig.networkType === 'TESTNET',
        trading_pair: trialConfig.tradingPair,
        trading_network: trialConfig.networkType,
        payment_method: 'TRIAL'
      }
      
      // Call marketplace subscription API
      const response = await fetch(`${config.studioBaseUrl}${config.endpoints.marketplaceSubscription}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': config.marketplaceApiKey
        },
        body: JSON.stringify(subscriptionData)
      })
      
      if (response.ok) {
        const result = await response.json()
        toast.success('🎉 24h Free Trial Started! Your bot is now active.')
        
                // Show success modal with trial details
                setTimeout(() => {
                  alert(`🚀 Free Trial Activated!\n\nBot: ${bot.name}\nSubscription ID: ${result.subscription_id}\nDuration: 24 hours\nExpires: ${endDate.toLocaleString()}\nStatus: ${result.status}\n\nConfiguration:\n• Network: ${trialConfig.networkType}\n• Trading Pair: ${trialConfig.tradingPair}\n• Environment: ${trialConfig.networkType === 'TESTNET' ? 'Testnet' : 'Mainnet'}\n\nNeed help? Contact us on Telegram or Discord!`)
                }, 1000)
        
      } else {
        const error = await response.json()
        toast.error(`Failed to start trial: ${error.detail || 'Unknown error'}`)
      }
      
    } catch (error) {
      console.error('Error starting free trial:', error)
      toast.error('Failed to start free trial. Please try again.')
    } finally {
      setIsStartingTrial(false)
    }
  }

  const fetchBotLogs = async () => {
    setIsLoadingLogs(true)
    try {
      const response = await fetch(`${config.studioBaseUrl}/api/futures-bot/logs/${bot.id}`)
      if (response.ok) {
        const data = await response.json()
        setBotLogs(data.logs || [])
      } else {
        console.error('Failed to fetch bot logs')
      }
    } catch (error) {
      console.error('Error fetching bot logs:', error)
    } finally {
      setIsLoadingLogs(false)
    }
  }

  // Fetch logs on component mount
  useEffect(() => {
    fetchBotLogs()
    // Auto-refresh logs every 5 seconds
    const interval = setInterval(fetchBotLogs, 5000)
    return () => clearInterval(interval)
  }, [bot.id])

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">{bot.name}</h2>
            <p className="text-gray-300">{bot.description}</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700">
                <h3 className="text-lg font-semibold text-purple-400 mb-2">Basic Info</h3>
                <p className="text-gray-300"><strong>Type:</strong> {bot.bot_type}</p>
                <p className="text-gray-300"><strong>Version:</strong> {bot.version}</p>
                <p className="text-gray-300"><strong>Status:</strong> {bot.status}</p>
                <p className="text-gray-300"><strong>Created:</strong> {new Date(bot.created_at).toLocaleDateString()}</p>
              </div>

              <div className="bg-gray-800 p-4 rounded-lg shadow-md border border-gray-700">
                <h3 className="text-lg font-semibold text-purple-400 mb-2">Trading Parameters</h3>
                <p className="text-gray-300"><strong>Exchange:</strong> {bot.exchange_type}</p>
                <p className="text-gray-300"><strong>Pair:</strong> {bot.trading_pair}</p>
                <p className="text-gray-300"><strong>Timeframe:</strong> {bot.timeframe}</p>
                <p className="text-gray-300"><strong>Leverage:</strong> {bot.leverage}x</p>
              </div>
            </div>

            {/* Backtest Section */}
            <div className="bg-gradient-to-r from-purple-900/30 to-blue-900/30 p-6 rounded-lg shadow-lg border border-purple-700">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-xl font-bold text-white mb-2">🧪 Backtest Your Bot</h3>
                  <p className="text-gray-300">Test your bot's performance with 24h free trial</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-green-400">FREE</div>
                  <div className="text-sm text-gray-400">24 hours</div>
                </div>
              </div>

          {/* Trial Configuration */}
          <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700 mb-6">
            <h4 className="text-lg font-semibold text-white mb-4">⚙️ Trial Configuration</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Network Type
                </label>
                <select
                  value={trialConfig.networkType}
                  onChange={(e) => setTrialConfig(prev => ({ ...prev, networkType: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="TESTNET">TESTNET (Safe Testing)</option>
                  <option value="MAINNET">MAINNET (Real Trading)</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  {trialConfig.networkType === 'TESTNET' 
                    ? '🔒 Safe testing environment with virtual funds' 
                    : '⚠️ Real trading environment with actual funds'
                  }
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Trading Pair
                </label>
                <select
                  value={trialConfig.tradingPair}
                  onChange={(e) => setTrialConfig(prev => ({ ...prev, tradingPair: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="BTC/USDT">BTC/USDT</option>
                  <option value="ETH/USDT">ETH/USDT</option>
                  <option value="BNB/USDT">BNB/USDT</option>
                  <option value="ADA/USDT">ADA/USDT</option>
                  <option value="SOL/USDT">SOL/USDT</option>
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  Choose the trading pair for your bot trial
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-white mb-2">📊 What You Get</h4>
              <ul className="text-gray-300 space-y-1">
                <li>• Real-time market analysis</li>
                <li>• Historical performance data</li>
                <li>• Risk management insights</li>
                <li>• Trading signal validation</li>
              </ul>
            </div>

            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-700">
              <h4 className="text-lg font-semibold text-white mb-2">🚀 Quick Start</h4>
              <ul className="text-gray-300 space-y-1">
                <li>• No setup required</li>
                <li>• Instant activation</li>
                <li>• Full bot capabilities</li>
                <li>• 24/7 monitoring</li>
              </ul>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => handleStartFreeTrial()}
                disabled={isStartingTrial}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed shadow-lg"
              >
                {isStartingTrial ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Starting Trial...
                  </span>
                ) : (
                  '🚀 Start 24h Free Trial'
                )}
              </button>
              
              <div className="text-center">
                <div className="text-sm text-gray-400 mb-1">Need help?</div>
                <div className="flex space-x-2">
                  <a
                    href="https://t.me/cryptomancer_ai_bot"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 text-sm font-medium"
                  >
                    📱 Telegram
                  </a>
                  <span className="text-gray-500">|</span>
                  <a
                    href="https://discord.gg/cryptomancer_ai_bot"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-indigo-400 hover:text-indigo-300 text-sm font-medium"
                  >
                    💬 Discord
                  </a>
                </div>
              </div>
            </div>

            <div className="text-right">
              <div className="text-xs text-gray-500">
                Trial starts immediately • No credit card required
              </div>
            </div>
          </div>

          {/* Monitor Logs Section */}
          <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700 mt-6">
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-semibold text-white flex items-center">
                📊 Monitor Execution Logs
                <span className="ml-2 px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">LIVE</span>
              </h4>
              <div className="flex items-center space-x-2">
                <button
                  onClick={fetchBotLogs}
                  disabled={isLoadingLogs}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white text-sm rounded-md transition-colors"
                >
                  {isLoadingLogs ? '⏳ Loading...' : '🔄 Refresh'}
                </button>
                <button
                  onClick={() => {/* TODO: Implement clear logs */}}
                  className="px-3 py-1 bg-red-600 hover:bg-red-700 text-white text-sm rounded-md transition-colors"
                >
                  🗑️ Clear
                </button>
              </div>
            </div>

            <div className="bg-black/50 rounded-lg p-4 h-64 overflow-y-auto">
              {isLoadingLogs ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
                  <span className="ml-2 text-gray-400">Loading logs...</span>
                </div>
              ) : (
                <div className="font-mono text-sm space-y-2">
                  {botLogs.length > 0 ? (
                    botLogs.map((log, index) => {
                      const timestamp = new Date(log.timestamp).toLocaleTimeString()
                      const getLogColor = (type: string) => {
                        switch (type) {
                          case 'transaction': return 'text-green-400'
                          case 'system': return 'text-blue-400'
                          case 'analysis': return 'text-yellow-400'
                          case 'llm': return 'text-purple-400'
                          case 'position': return 'text-cyan-400'
                          case 'order': return 'text-orange-400'
                          case 'error': return 'text-red-400'
                          default: return 'text-gray-400'
                        }
                      }
                      const getLogIcon = (type: string) => {
                        switch (type) {
                          case 'transaction': return '💰'
                          case 'system': return '✅'
                          case 'analysis': return '🔍'
                          case 'llm': return '📊'
                          case 'position': return '📈'
                          case 'order': return '🎯'
                          case 'error': return '❌'
                          default: return '📝'
                        }
                      }
                      
                      return (
                        <div key={index} className={getLogColor(log.type)}>
                          <span className="text-gray-500">[{timestamp}]</span> {getLogIcon(log.type)} {
                            log.type === 'transaction' 
                              ? `${log.action} ${log.quantity} ${log.symbol} at $${log.entry_price} (${log.leverage}x)`
                              : log.message || `${log.action} ${log.symbol}`
                          }
                          {log.confidence && (
                            <span className="text-gray-500 ml-2">(Confidence: {(log.confidence * 100).toFixed(1)}%)</span>
                          )}
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-gray-500 text-center py-8">
                      No logs available for this bot yet.
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="mt-4 flex items-center justify-between text-sm text-gray-400">
              <div className="flex items-center space-x-4">
                <span className="flex items-center">
                  <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                  Bot Status: Active
                </span>
                <span className="flex items-center">
                  <div className="w-2 h-2 bg-blue-400 rounded-full mr-2"></div>
                  Last Update: 2 seconds ago
                </span>
              </div>
              <div className="text-xs">
                Auto-refresh every 5 seconds
              </div>
            </div>
          </div>
            </div>
          </div>
        )
      case 'settings':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Bot Settings</h2>
            <p className="text-gray-300">Manage advanced configurations for your bot.</p>
            <Link href={`/creator/entities/${bot.id}/edit`} className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500">
              <Cog6ToothIcon className="-ml-1 mr-2 h-5 w-5" />
              Edit Bot Configuration
            </Link>
          </div>
        )
      case 'prompts':
        return <BotPromptsTab botId={bot.id} />
      case 'risk-management':
        return <RiskManagementTab botId={bot.id} />
      case 'analytics':
        return (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Analytics</h2>
            <p className="text-gray-300">Bot performance metrics and analytics.</p>
            <div className="bg-gray-800 p-6 rounded-lg">
              <p className="text-gray-400">Analytics coming soon...</p>
            </div>
          </div>
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/creator/entities" className="inline-flex items-center text-purple-400 hover:text-purple-300">
            <ArrowLeftIcon className="h-5 w-5 mr-2" />
            Back to My Entities
          </Link>
          <h1 className="text-3xl font-extrabold text-white">{bot.name}</h1>
          <div className="w-10"></div> {/* Spacer */}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700 mb-6">
          <nav className="-mb-px flex space-x-8" aria-label="Tabs">
            <button
              onClick={() => setActiveTab('overview')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'overview'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <SparklesIcon className="h-5 w-5 inline-block mr-2" />
              Overview
            </button>
            <button
              onClick={() => setActiveTab('prompts')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'prompts'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <DocumentTextIcon className="h-5 w-5 inline-block mr-2" />
              Prompts
            </button>
            <button
              onClick={() => setActiveTab('risk-management')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'risk-management'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <ExclamationTriangleIcon className="h-5 w-5 inline-block mr-2" />
              Risk Management
            </button>
            <button
              onClick={() => setActiveTab('settings')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'settings'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <Cog6ToothIcon className="h-5 w-5 inline-block mr-2" />
              Settings
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'analytics'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <ChartBarIcon className="h-5 w-5 inline-block mr-2" />
              Analytics
            </button>
          </nav>
        </div>

        {/* Content based on active tab */}
        {renderContent()}
      </div>
    </div>
  )
}