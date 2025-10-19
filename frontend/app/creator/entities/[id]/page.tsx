'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { 
  ArrowLeftIcon,
  PencilIcon,
  Cog6ToothIcon,
  SparklesIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ExclamationTriangleIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline'
import { CheckCircleIcon, ClockIcon, XCircleIcon, ArchiveBoxIcon } from '@heroicons/react/24/solid'
import Link from 'next/link'
import BotPromptsTab from '@/components/BotPromptsTab'
import RiskManagementTab from '@/components/RiskManagementTab'
import BotAnalytics from '@/components/BotAnalytics'
import BotSubscriptions from '@/components/BotSubscriptions'
import toast from 'react-hot-toast'
import config from '@/lib/config'
import { useAuth } from '@/contexts/AuthContext'
import { useGetBot } from '@/hooks/useBots'
import PreTrialValidationModal from '@/components/PreTrialValidationModal'
import UpgradeModal from '@/components/UpgradeModal'
import { usePlan } from '@/hooks/usePlan'

// Bot Log Interface
interface BotLog {
  timestamp: string
  execution_time: string
  type: string
  message: string
  level: string
  action?: string
  symbol?: string
  quantity?: number
  entry_price?: number
  entry_time?: string | null
  leverage?: number
  status?: string
  order_id?: string
  position_side?: string
  subscription_id?: number
  
  // Risk Management
  stop_loss?: number | null
  take_profit?: number | null
  
  // P&L (synced from exchange by Celery every 10s)
  unrealized_pnl?: number | null
  realized_pnl?: number | null
  pnl_usd?: number | null
  pnl_percentage?: number | null
  is_winning?: boolean | null
  
  // Price & Exit Info
  last_updated_price?: number | null
  exit_price?: number | null
  exit_time?: string | null
  exit_reason?: string | null
  
  // Additional Metrics
  fees_paid?: number | null
  trade_duration_minutes?: number | null
  risk_reward_ratio?: number | null
  actual_rr_ratio?: number | null
  strategy_used?: string | null
  
  // Legacy fields (deprecated)
  unrealized_pnl_pct?: number | null
  funding_fees?: number
  needs_price_update?: boolean
  
  confidence?: number
  reason?: string
  details?: string
  signal_data?: any
}

type TabType = 'overview' | 'strategies' | 'risk-management' | 'settings' | 'analytics' | 'subscriptions'

export default function BotDetailPage() {
  const router = useRouter()
  const params = useParams()
  const botId = params?.id as string
  const { user } = useAuth()

  // Check localStorage for initial tab
  const getInitialTab = (): TabType => {
    if (typeof window !== 'undefined') {
      const savedTab = localStorage.getItem('bot-detail-tab')
      if (savedTab) {
        localStorage.removeItem('bot-detail-tab') // Clear after reading
        return savedTab as TabType
      }
    }
    return 'overview'
  }

  const [activeTab, setActiveTab] = useState<TabType>(getInitialTab())
  const [isStartingTrial, setIsStartingTrial] = useState(false)
  const [trialConfig, setTrialConfig] = useState({
    tradingPair: 'BTC/USDT',
    secondaryTradingPairs: [] as string[],
    networkType: 'TESTNET',
    subscriptionStart: '', // For Pro users
    subscriptionEnd: ''    // For Pro users
  })
  const [botLogs, setBotLogs] = useState<BotLog[]>([])
  const [isLoadingLogs, setIsLoadingLogs] = useState(false)
  
  // Pre-trial validation state
  const [showValidationModal, setShowValidationModal] = useState(false)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  
  // Get user plan
  const { currentPlan, isLoadingPlan } = usePlan()
  const isPro = currentPlan?.plan_name === 'pro'

  // Set default dates when Pro plan loads
  useEffect(() => {
    if (isPro && currentPlan && !trialConfig.subscriptionStart) {
      const now = new Date()
      const planExpiry = currentPlan.expiry_date ? new Date(currentPlan.expiry_date) : new Date(now.getTime() + 30 * 24 * 60 * 60 * 1000)
      
      // Format for datetime-local input (YYYY-MM-DDTHH:mm)
      const formatDateTime = (date: Date) => {
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        const hours = String(date.getHours()).padStart(2, '0')
        const minutes = String(date.getMinutes()).padStart(2, '0')
        return `${year}-${month}-${day}T${hours}:${minutes}`
      }
      
      setTrialConfig(prev => ({
        ...prev,
        subscriptionStart: formatDateTime(now),
        subscriptionEnd: formatDateTime(planExpiry)
      }))
    }
  }, [isPro, currentPlan])

  // Fetch real bot data from API
  const { data: bot, isLoading: isBotLoading, error: botError } = useGetBot(botId)

  // Set default tab to analytics for non-developers after bot loads
  useEffect(() => {
    if (bot && user && bot.developer_id !== user.id) {
      // Check if coming from localStorage (already handled)
      const savedTab = typeof window !== 'undefined' ? localStorage.getItem('bot-detail-tab') : null
      if (!savedTab) {
        // Default to analytics for non-developers
        setActiveTab('analytics')
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bot?.id, user?.id])

  // Define fetchBotLogs with useCallback to prevent infinite loop
  const fetchBotLogs = useCallback(async () => {
    if (!bot?.id) return
    
    setIsLoadingLogs(true)
    try {
      const response = await fetch(`${config.studioBaseUrl}/api/futures-bot/logs/${bot.id}`)
      if (response.ok) {
        const data = await response.json()
        console.log('🔍 Bot Logs Data:', data.logs?.slice(0, 2)) // Debug: show first 2 logs
        setBotLogs(data.logs || [])
      } else {
        console.error('Failed to fetch bot logs')
      }
    } catch (error) {
      console.error('Error fetching bot logs:', error)
    } finally {
      setIsLoadingLogs(false)
    }
  }, [bot?.id])

  // Fetch logs on component mount - MUST be called before early returns
  useEffect(() => {
    if (bot?.id) {
      fetchBotLogs()
      // Auto-refresh logs every 5 seconds
      const interval = setInterval(fetchBotLogs, 5000)
      return () => clearInterval(interval)
    }
  }, [bot?.id, fetchBotLogs])

  // Show loading state AFTER all hooks
  if (isBotLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading bot details...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (botError || !bot) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto" />
          <p className="mt-4 text-gray-400">Failed to load bot details</p>
          <button 
            onClick={() => router.push('/creator/entities')}
            className="mt-4 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Back to Entities
          </button>
        </div>
      </div>
    )
  }

  const handleStartFreeTrial = async () => {
    if (isStartingTrial) return
    
    // Show validation modal first
    setShowValidationModal(true)
  }

  // Actual trial start after validation passes
  const startTrialAfterValidation = async () => {
    if (isStartingTrial) return
    
    setIsStartingTrial(true)
    setShowValidationModal(false)
    
    try {
      // ✅ Check for trading pair conflicts with existing active subscriptions
      const token = localStorage.getItem('access_token')
      if (token && user?.id) {
        try {
          // Fetch all subscriptions for this bot by this developer
          const checkResponse = await fetch(`${config.studioBaseUrl}/subscriptions?bot_id=${bot.id}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })

          if (checkResponse.ok) {
            const allSubscriptions = await checkResponse.json()
            console.log(`🔍 Found ${allSubscriptions.length} total subscriptions for bot ${bot.id}`)
            
            // Filter: only active subscriptions that haven't expired yet
            const now = new Date()
            const activeSubscriptions = allSubscriptions.filter((sub: any) => {
              // Check both expires_at and marketplace_subscription_end
              const endDate = sub.expires_at || sub.marketplace_subscription_end
              if (!endDate) return false
              const expireDate = new Date(endDate)
              const isActive = sub.status === 'ACTIVE' && expireDate > now
              if (isActive) {
                console.log(`✅ Active subscription ${sub.id}: ${sub.trading_pair} on ${sub.network_type}, expires: ${endDate}`)
              }
              return isActive
            })
            
            console.log(`🎯 Found ${activeSubscriptions.length} active non-expired subscriptions`)
            
            // Collect all trading pairs from current config
            const requestedPairs = [trialConfig.tradingPair, ...trialConfig.secondaryTradingPairs]
            
            // Check if any requested pair is already in use (same exchange + network)
            const conflictingPairs: string[] = []
            for (const sub of activeSubscriptions) {
              // Check if same network type
              const sameNetwork = sub.network_type === trialConfig.networkType || 
                                 (sub.network_type === 'TESTNET' && trialConfig.networkType === 'TESTNET') ||
                                 (sub.network_type === 'MAINNET' && trialConfig.networkType === 'MAINNET')
              
              if (sameNetwork) {
                const existingPairs = [sub.trading_pair, ...(sub.secondary_trading_pairs || [])]
                for (const pair of requestedPairs) {
                  if (existingPairs.includes(pair)) {
                    conflictingPairs.push(`${pair} (${sub.network_type})`)
                  }
                }
              }
            }

            if (conflictingPairs.length > 0) {
              const uniqueConflicts = Array.from(new Set(conflictingPairs))
              toast.error(
                `⚠️ Trading pair conflict!\n\n` +
                `The following trading pair(s) are already in active subscriptions:\n` +
                `${uniqueConflicts.join(', ')}\n\n` +
                `Please choose different trading pairs or stop the existing subscription first.`
              )
              setIsStartingTrial(false)
              return
            }
          }
        } catch (error) {
          console.error('Error checking trading pair conflicts:', error)
          // Continue anyway if check fails
        }
      }

      // Calculate start and end dates
      let startDate: Date
      let endDate: Date
      
      if (isPro && trialConfig.subscriptionStart && trialConfig.subscriptionEnd) {
        // Pro users: use custom dates
        startDate = new Date(trialConfig.subscriptionStart)
        endDate = new Date(trialConfig.subscriptionEnd)
      } else {
        // Free users: 24h free trial
        startDate = new Date()
        endDate = new Date(startDate.getTime() + 24 * 60 * 60 * 1000) // 24 hours later
      }
      
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
        secondary_trading_pairs: trialConfig.secondaryTradingPairs, // Multi-pair trading
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
        const successMessage = isPro 
          ? '🎉 Trading Started! Your bot is now active.'
          : '🎉 24h Free Trial Started! Your bot is now active.'
        toast.success(successMessage)
        
      } else {
        const error = await response.json()
        
        // ✅ Check if subscription limit reached (403 Forbidden)
        if (response.status === 403 && (error.detail?.includes('Subscription limit reached') || error.detail?.includes('subscription'))) {
          // Extract limit info from error message (e.g., "5/5")
          const limitMatch = error.detail?.match(/\((\d+)\/(\d+)\)/)
          const limitInfo = limitMatch ? ` (${limitMatch[1]}/${limitMatch[2]})` : ''
          toast.error(`🚫 Trial subscription limit reached${limitInfo}!`)
          setShowUpgradeModal(true)
        } else {
          toast.error(`Failed to start trial: ${error.detail || 'Unknown error'}`)
        }
      }
      
    } catch (error) {
      console.error('Error starting free trial:', error)
      toast.error('Failed to start free trial. Please try again.')
    } finally {
      setIsStartingTrial(false)
    }
  }

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
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={currentPlan?.plan_name === 'free' && trialConfig.networkType === 'TESTNET'}
                >
                  <option value="TESTNET">TESTNET (Safe Testing)</option>
                  <option value="MAINNET" disabled={currentPlan?.plan_name === 'free'}>
                    MAINNET (Real Trading) {currentPlan?.plan_name === 'free' ? '🔒 Pro Only' : ''}
                  </option>
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  {trialConfig.networkType === 'TESTNET' 
                    ? '🔒 Safe testing environment with virtual funds' 
                    : '⚠️ Real trading environment with actual funds'
                  }
                </p>
                
                {/* Free Plan Warning for Mainnet */}
                {currentPlan?.plan_name === 'free' && (
                  <div className="mt-2 bg-orange-500/10 border border-orange-500/30 rounded-md p-2">
                    <p className="text-xs text-orange-300 leading-relaxed">
                      <span className="font-semibold">Free Plan:</span> Testnet only. 
                      <button 
                        type="button"
                        onClick={() => setShowUpgradeModal(true)}
                        className="underline hover:text-orange-200 font-semibold ml-1"
                      >
                        Upgrade to Pro
                      </button> for Mainnet trading with real funds.
                    </p>
                  </div>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Primary Trading Pair
                </label>
                <select
                  value={trialConfig.tradingPair}
                  onChange={(e) => setTrialConfig(prev => ({ ...prev, tradingPair: e.target.value }))}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  {bot.trading_pairs && bot.trading_pairs.length > 0 ? (
                    bot.trading_pairs.map((pair: string) => (
                      <option key={pair} value={pair}>{pair}</option>
                    ))
                  ) : (
                    <option value="BTC/USDT">BTC/USDT</option>
                  )}
                </select>
                <p className="text-xs text-gray-400 mt-1">
                  🎯 Select from pairs configured by developer
                </p>
              </div>
            </div>
            
            {/* Secondary Trading Pairs */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Secondary Trading Pairs (Optional)
              </label>
              <p className="text-xs text-gray-400 mb-3">
                📊 Bot will trade these pairs when primary is busy (priority order)
              </p>
              
              {/* Add New Pair Dropdown */}
              <div className="flex gap-2 mb-3">
                <select
                  className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  onChange={(e) => {
                    const value = e.target.value
                    if (value && !trialConfig.secondaryTradingPairs.includes(value) && value !== trialConfig.tradingPair) {
                      setTrialConfig(prev => ({
                        ...prev,
                        secondaryTradingPairs: [...prev.secondaryTradingPairs, value]
                      }))
                      e.target.value = '' // Reset select
                    }
                  }}
                  defaultValue=""
                >
                  <option value="" disabled>Select pair to add...</option>
                  {bot.trading_pairs && bot.trading_pairs.length > 0 ? (
                    bot.trading_pairs
                      .filter((pair: string) => pair !== trialConfig.tradingPair && !trialConfig.secondaryTradingPairs.includes(pair))
                      .map((pair: string) => (
                        <option key={pair} value={pair}>{pair}</option>
                      ))
                  ) : null}
                </select>
              </div>
              
              {/* List of Secondary Pairs */}
              {trialConfig.secondaryTradingPairs.length > 0 && (
                <div className="space-y-2">
                  {trialConfig.secondaryTradingPairs.map((pair, index) => (
                    <div
                      key={index}
                      className="flex items-center gap-2 bg-gray-700/50 border border-gray-600 rounded-md p-2"
                    >
                      {/* Priority Badge */}
                      <div className="flex items-center justify-center w-7 h-7 rounded-full bg-purple-500/20 text-purple-400 text-sm font-bold">
                        {index + 2}
                      </div>
                      
                      {/* Pair Name */}
                      <div className="flex-1 text-white font-medium text-sm">
                        {pair}
                      </div>
                      
                      {/* Reorder Buttons */}
                      <button
                        type="button"
                        onClick={() => {
                          if (index > 0) {
                            const pairs = [...trialConfig.secondaryTradingPairs]
                            ;[pairs[index - 1], pairs[index]] = [pairs[index], pairs[index - 1]]
                            setTrialConfig(prev => ({ ...prev, secondaryTradingPairs: pairs }))
                          }
                        }}
                        disabled={index === 0}
                        className={`p-1 rounded ${
                          index === 0
                            ? 'text-gray-600 cursor-not-allowed'
                            : 'text-gray-400 hover:text-purple-400'
                        }`}
                        title="Move up"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                        </svg>
                      </button>
                      
                      <button
                        type="button"
                        onClick={() => {
                          if (index < trialConfig.secondaryTradingPairs.length - 1) {
                            const pairs = [...trialConfig.secondaryTradingPairs]
                            ;[pairs[index], pairs[index + 1]] = [pairs[index + 1], pairs[index]]
                            setTrialConfig(prev => ({ ...prev, secondaryTradingPairs: pairs }))
                          }
                        }}
                        disabled={index === trialConfig.secondaryTradingPairs.length - 1}
                        className={`p-1 rounded ${
                          index === trialConfig.secondaryTradingPairs.length - 1
                            ? 'text-gray-600 cursor-not-allowed'
                            : 'text-gray-400 hover:text-purple-400'
                        }`}
                        title="Move down"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                      
                      {/* Remove Button */}
                      <button
                        type="button"
                        onClick={() => {
                          const pairs = trialConfig.secondaryTradingPairs.filter((_, i) => i !== index)
                          setTrialConfig(prev => ({ ...prev, secondaryTradingPairs: pairs }))
                        }}
                        className="p-1 text-red-400 hover:text-red-300 rounded"
                        title="Remove"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  ))}
                  
                  {/* Summary */}
                  <div className="mt-2 text-xs text-gray-500 bg-gray-800/50 rounded p-2 border border-purple-500/20">
                    <div className="font-medium text-purple-400 mb-1">Trading Priority Order:</div>
                    <div className="space-y-0.5">
                      <div>1️⃣ {trialConfig.tradingPair} <span className="text-gray-600">(Primary)</span></div>
                      {trialConfig.secondaryTradingPairs.map((pair, idx) => (
                        <div key={idx}>{idx + 2}️⃣ {pair}</div>
                      ))}
                    </div>
                    <div className="mt-1 text-gray-600">
                      💡 Bot trades first available pair without open position
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Strategy Setup Section */}
          <div className="mb-6">
            <div className="bg-gradient-to-br from-indigo-900/30 to-purple-800/30 p-5 rounded-lg border border-indigo-500/30">
              <h4 className="text-lg font-semibold text-white mb-3 flex items-center">
                <span className="mr-2">💬</span>
                Bot Strategy Setup
                <span className="ml-2 px-2 py-0.5 text-xs bg-red-500 text-white rounded-full">REQUIRED</span>
              </h4>
              <div className="text-gray-300 space-y-2 text-sm">
                <p className="text-yellow-400 font-medium mb-2">⚠️ Bot requires a prompt to analyze market and make decisions!</p>
                <div className="space-y-1.5">
                  <div className="flex items-start">
                    <span className="mr-2">1️⃣</span>
                    <span>Click on <strong className="text-indigo-400">"Strategy Management"</strong> tab above</span>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">2️⃣</span>
                    <span>Attach at least one prompt to your bot</span>
                  </div>
                  <div className="flex items-start">
                    <span className="mr-2">3️⃣</span>
                    <span>Configure prompt settings (market analysis, risk level, etc.)</span>
                  </div>
                </div>
                <div className="mt-3 p-2 bg-indigo-900/30 border border-indigo-500/20 rounded text-xs flex items-start">
                  <span className="mr-2">💡</span>
                  <span>The prompt guides your bot's trading strategy and decision-making process. Without a prompt, the bot cannot operate.</span>
                </div>
              </div>
            </div>
          </div>

          {/* Pro Plan: Custom subscription dates */}
          {isPro && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Subscription Start Date
                </label>
                <input
                  type="datetime-local"
                  value={trialConfig.subscriptionStart}
                  onChange={(e) => setTrialConfig({ ...trialConfig, subscriptionStart: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Subscription End Date
                </label>
                <input
                  type="datetime-local"
                  value={trialConfig.subscriptionEnd}
                  onChange={(e) => setTrialConfig({ ...trialConfig, subscriptionEnd: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => handleStartFreeTrial()}
                disabled={isStartingTrial || (isPro && (!trialConfig.subscriptionStart || !trialConfig.subscriptionEnd))}
                className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-600 disabled:to-gray-700 text-white px-6 py-3 rounded-lg font-semibold transition-all duration-200 transform hover:scale-105 disabled:scale-100 disabled:cursor-not-allowed shadow-lg"
              >
                {isStartingTrial ? (
                  <span className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    {isPro ? 'Starting...' : 'Starting Trial...'}
                  </span>
                ) : (
                  isPro ? '🚀 Start Trade' : '🚀 Start 24h Free Trial'
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
                {isPro 
                  ? 'Set custom subscription period • Mainnet supported' 
                  : 'Trial starts immediately • No credit card required'
                }
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
                      
                      // Extract detailed trade info - API returns fields directly on log object
                      const confidence = log.confidence
                      const stopLoss = log.stop_loss
                      const takeProfit = log.take_profit
                      const leverage = log.leverage
                      const quantity = log.quantity
                      const entryPrice = log.entry_price
                      const tradingPair = log.symbol
                      const status = log.status
                      
                      // P&L fields (synced from exchange every 10s by Celery)
                      const unrealizedPnl = log.unrealized_pnl
                      const realizedPnl = log.realized_pnl
                      const pnlUsd = log.pnl_usd
                      const pnlPercentage = log.pnl_percentage
                      const isWinning = log.is_winning
                      
                      // Price & Exit info
                      const lastUpdatedPrice = log.last_updated_price
                      const exitPrice = log.exit_price
                      const exitTime = log.exit_time
                      const exitReason = log.exit_reason
                      
                      // Additional metrics
                      const feesPaid = log.fees_paid
                      const tradeDuration = log.trade_duration_minutes
                      const strategyUsed = log.strategy_used
                      
                      // Status badge color
                      const getStatusBadge = (status: string) => {
                        if (status === 'OPEN') return <span className="px-2 py-0.5 text-xs bg-green-900/50 text-green-400 rounded ml-2">OPEN</span>
                        if (status === 'CLOSED') return <span className="px-2 py-0.5 text-xs bg-gray-700 text-gray-400 rounded ml-2">CLOSED</span>
                        return null
                      }
                      
                      // P&L color
                      const getPnlColor = (pnl: number | null) => {
                        if (!pnl) return 'text-gray-400'
                        return pnl >= 0 ? 'text-green-400' : 'text-red-400'
                      }
                      
                      return (
                        <div key={index} className={getLogColor(log.type)}>
                          <span className="text-gray-500">[{timestamp}]</span> {getLogIcon(log.type)} {
                            log.type === 'transaction' || log.action === 'BUY' || log.action === 'SELL'
                              ? (
                                  <>
                                    <span className="font-semibold">{log.action}</span> {quantity} {tradingPair} at ${typeof entryPrice === 'number' ? entryPrice.toFixed(2) : entryPrice} 
                                    {leverage && <span className="text-purple-400"> ({leverage}x)</span>}
                                    {status && getStatusBadge(status)}
                                    {log.subscription_id && (
                                      <span className="text-gray-500 ml-2 text-xs">Sub#{log.subscription_id}</span>
                                    )}
                                    {confidence && (
                                      <span className="text-gray-500 ml-2">(Confidence: {(confidence * 100).toFixed(1)}%)</span>
                                    )}
                                    
                                    {/* Risk Management + P&L Info */}
                                    <div className="ml-8 mt-1 text-sm space-y-1">
                                      {/* Risk Management */}
                                      {(stopLoss || takeProfit) && (
                                        <div className="text-gray-400">
                                          {stopLoss && <span className="mr-4">🛡️ SL: ${typeof stopLoss === 'number' ? stopLoss.toFixed(2) : stopLoss}</span>}
                                          {takeProfit && <span>💚 TP: ${typeof takeProfit === 'number' ? takeProfit.toFixed(2) : takeProfit}</span>}
                                        </div>
                                      )}
                                      
                                      {/* OPEN Position - Show Unrealized P&L */}
                                      {status === 'OPEN' && (
                                        <>
                                          {lastUpdatedPrice && (
                                            <div className="text-gray-400">
                                              💰 Current: ${lastUpdatedPrice.toFixed(2)}
                                            </div>
                                          )}
                                          <div className={getPnlColor(unrealizedPnl ?? null)}>
                                            {unrealizedPnl !== null && unrealizedPnl !== undefined && pnlPercentage !== null && pnlPercentage !== undefined ? (
                                              <>
                                                💵 P&L: ${unrealizedPnl >= 0 ? '+' : ''}{unrealizedPnl.toFixed(2)} ({pnlPercentage >= 0 ? '+' : ''}{pnlPercentage.toFixed(2)}%)
                                                {feesPaid !== undefined && feesPaid !== null && feesPaid !== 0 && (
                                                  <span className="ml-4 text-yellow-400">💸 Fees: -${feesPaid.toFixed(2)}</span>
                                                )}
                                              </>
                                            ) : (
                                              <span className="text-gray-500">💵 P&L: Syncing...</span>
                                            )}
                                          </div>
                                        </>
                                      )}
                                      
                                      {/* CLOSED Position - Show Realized P&L */}
                                      {status === 'CLOSED' && (
                                        <>
                                          {exitPrice && (
                                            <div className="text-gray-400">
                                              🚪 Exit: ${exitPrice.toFixed(2)}
                                              {exitReason && (
                                                <span className="ml-2 px-1.5 py-0.5 text-xs bg-gray-800 rounded">
                                                  {exitReason === 'TP_HIT' && '✅ TP'}
                                                  {exitReason === 'SL_HIT' && '❌ SL'}
                                                  {exitReason === 'MANUAL' && '👤 Manual'}
                                                  {exitReason === 'LIQUIDATION' && '⚠️ Liq'}
                                                  {!['TP_HIT', 'SL_HIT', 'MANUAL', 'LIQUIDATION'].includes(exitReason) && exitReason}
                                                </span>
                                              )}
                                            </div>
                                          )}
                                          {realizedPnl !== null && realizedPnl !== undefined && pnlPercentage !== null && pnlPercentage !== undefined && (
                                            <div className={getPnlColor(realizedPnl ?? null)}>
                                              {isWinning ? '✅' : '❌'} Realized: ${realizedPnl >= 0 ? '+' : ''}{realizedPnl.toFixed(2)} ({pnlPercentage >= 0 ? '+' : ''}{pnlPercentage.toFixed(2)}%)
                                              {tradeDuration && (
                                                <span className="ml-4 text-gray-500">⏱️ {tradeDuration < 60 ? `${tradeDuration}m` : `${(tradeDuration / 60).toFixed(1)}h`}</span>
                                              )}
                                            </div>
                                          )}
                                          {exitTime && (
                                            <div className="text-xs text-gray-500">
                                              Closed: {new Date(exitTime).toLocaleString()}
                                            </div>
                                          )}
                                        </>
                                      )}
                                    </div>
                                  </>
                                )
                              : (log.details || log.message || `${log.action} ${log.symbol}`)
                          }
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
      case 'strategies':
        return <BotPromptsTab botId={bot.id} />
      case 'risk-management':
        return <RiskManagementTab botId={bot.id} />
      case 'analytics':
        return <BotAnalytics botId={bot.id} />
      case 'subscriptions':
        return <BotSubscriptions botId={bot.id} />
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
            {/* Show Overview tab only for bot developer */}
            {bot.developer_id === user?.id && (
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
            )}
            
            {/* Show Strategies tab only for bot developer */}
            {bot.developer_id === user?.id && (
              <button
                onClick={() => setActiveTab('strategies')}
                className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'strategies'
                    ? 'border-purple-500 text-purple-400'
                    : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
                }`}
              >
                <DocumentTextIcon className="h-5 w-5 inline-block mr-2" />
                Strategies
              </button>
            )}
            
            {/* Show Risk Management tab only for bot developer */}
            {bot.developer_id === user?.id && (
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
            )}
            
            {/* Show Settings tab only for bot developer */}
            {bot.developer_id === user?.id && (
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
            )}
            
            {/* Show Analytics tab for everyone */}
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
            
            {/* Show Subscriptions tab for everyone */}
            <button
              onClick={() => setActiveTab('subscriptions')}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'subscriptions'
                  ? 'border-purple-500 text-purple-400'
                  : 'border-transparent text-gray-400 hover:text-gray-200 hover:border-gray-300'
              }`}
            >
              <UserGroupIcon className="h-5 w-5 inline-block mr-2" />
              Subscriptions
            </button>
          </nav>
        </div>

        {/* Content based on active tab */}
        {renderContent()}
      </div>

      {/* Pre-Trial Validation Modal */}
      {bot && (
        <PreTrialValidationModal
          isOpen={showValidationModal}
          onClose={() => setShowValidationModal(false)}
          onProceed={startTrialAfterValidation}
          bot={bot as any}
          networkType={trialConfig.networkType as 'TESTNET' | 'MAINNET'}
        />
      )}

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
      />
    </div>
  )
}