'use client'

import { useState, useEffect } from 'react'
import { ShieldCheckIcon, BeakerIcon, ChartBarIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

interface RiskConfigurationFormProps {
  botId?: number
  subscriptionId?: number
  initialConfig?: any
  onSave?: (config: any) => void
}

export default function RiskConfigurationForm({
  botId,
  subscriptionId,
  initialConfig,
  onSave
}: RiskConfigurationFormProps) {
  // Mode selection
  const [mode, setMode] = useState<'DEFAULT' | 'AI_PROMPT'>('DEFAULT')
  
  // DEFAULT mode settings
  const [stopLossPercent, setStopLossPercent] = useState<number>(2.0)
  const [takeProfitPercent, setTakeProfitPercent] = useState<number>(4.0)
  const [maxPositionSize, setMaxPositionSize] = useState<number>(10.0)
  const [minRiskRewardRatio, setMinRiskRewardRatio] = useState<number>(2.0)
  const [riskPerTradePercent, setRiskPerTradePercent] = useState<number>(2.0)
  const [maxLeverage, setMaxLeverage] = useState<number>(10)
  const [maxPortfolioExposure, setMaxPortfolioExposure] = useState<number>(30.0)
  const [dailyLossLimitPercent, setDailyLossLimitPercent] = useState<number>(5.0)
  
  // Trailing stop
  const [trailingStopEnabled, setTrailingStopEnabled] = useState<boolean>(false)
  const [trailingActivationPercent, setTrailingActivationPercent] = useState<number>(2.0)
  const [trailingPercent, setTrailingPercent] = useState<number>(1.0)
  
  // Trading window
  const [tradingWindowEnabled, setTradingWindowEnabled] = useState<boolean>(false)
  const [startHour, setStartHour] = useState<number>(9)
  const [endHour, setEndHour] = useState<number>(17)
  const [daysOfWeek, setDaysOfWeek] = useState<number[]>([0, 1, 2, 3, 4])
  
  // Cooldown
  const [cooldownEnabled, setCooldownEnabled] = useState<boolean>(false)
  const [cooldownMinutes, setCooldownMinutes] = useState<number>(30)
  const [triggerLossCount, setTriggerLossCount] = useState<number>(3)
  
  // AI mode settings
  const [aiPromptId, setAiPromptId] = useState<number | null>(null)
  const [aiPromptCustom, setAiPromptCustom] = useState<string>('')
  const [aiUpdateFrequency, setAiUpdateFrequency] = useState<number>(15)
  const [aiAllowOverride, setAiAllowOverride] = useState<boolean>(false)
  const [aiMinStopLoss, setAiMinStopLoss] = useState<number>(1.0)
  const [aiMaxStopLoss, setAiMaxStopLoss] = useState<number>(5.0)
  const [aiMinTakeProfit, setAiMinTakeProfit] = useState<number>(2.0)
  const [aiMaxTakeProfit, setAiMaxTakeProfit] = useState<number>(10.0)
  
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)

  // Load risk config from API
  useEffect(() => {
    const loadConfig = async () => {
      if (initialConfig) {
        // Use provided initialConfig
        loadConfigData(initialConfig)
      } else if (botId) {
        // Load bot-level config from API
        try {
          const token = localStorage.getItem('access_token')
          console.log('🔑 Token being sent:', token ? `${token.substring(0, 20)}...` : 'NO TOKEN')
          
          const response = await fetch(`/api/v1/risk-management/bots/${botId}/risk-config`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const config = await response.json()
            loadConfigData(config)
          }
        } catch (error) {
          console.error('Error loading bot risk config:', error)
        }
      } else if (subscriptionId) {
        // Load subscription-level config from API
        try {
          const response = await fetch(`/api/v1/risk-management/subscriptions/${subscriptionId}/risk-config`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('access_token')}`
            }
          })
          
          if (response.ok) {
            const config = await response.json()
            loadConfigData(config)
          }
        } catch (error) {
          console.error('Error loading subscription risk config:', error)
        }
      }
    }
    
    loadConfig()
  }, [botId, subscriptionId, initialConfig])
  
  const loadConfigData = (config: any) => {
    if (!config) return
    
    setMode(config.mode || 'DEFAULT')
    setStopLossPercent(config.stop_loss_percent || 2.0)
    setTakeProfitPercent(config.take_profit_percent || 4.0)
    setMaxPositionSize(config.max_position_size || 10.0)
    setMinRiskRewardRatio(config.min_risk_reward_ratio || 2.0)
    setRiskPerTradePercent(config.risk_per_trade_percent || 2.0)
    setMaxLeverage(config.max_leverage || 10)
    setMaxPortfolioExposure(config.max_portfolio_exposure || 30.0)
    setDailyLossLimitPercent(config.daily_loss_limit_percent || 5.0)
    
    if (config.trailing_stop) {
      setTrailingStopEnabled(config.trailing_stop.enabled || false)
      setTrailingActivationPercent(config.trailing_stop.activation_percent || 2.0)
      setTrailingPercent(config.trailing_stop.trailing_percent || 1.0)
    }
    
    if (config.trading_window) {
      setTradingWindowEnabled(config.trading_window.enabled || false)
      setStartHour(config.trading_window.start_hour || 9)
      setEndHour(config.trading_window.end_hour || 17)
      setDaysOfWeek(config.trading_window.days_of_week || [0, 1, 2, 3, 4])
    }
    
    if (config.cooldown) {
      setCooldownEnabled(config.cooldown.enabled || false)
      setCooldownMinutes(config.cooldown.cooldown_minutes || 30)
      setTriggerLossCount(config.cooldown.trigger_loss_count || 3)
    }
    
    setAiPromptId(config.ai_prompt_id || null)
    setAiPromptCustom(config.ai_prompt_custom || '')
    setAiUpdateFrequency(config.ai_update_frequency_minutes || 15)
    setAiAllowOverride(config.ai_allow_override || false)
    setAiMinStopLoss(config.ai_min_stop_loss || 1.0)
    setAiMaxStopLoss(config.ai_max_stop_loss || 5.0)
    setAiMinTakeProfit(config.ai_min_take_profit || 2.0)
    setAiMaxTakeProfit(config.ai_max_take_profit || 10.0)
  }

  const buildConfig = () => {
    return {
      mode,
      
      // Basic parameters
      stop_loss_percent: stopLossPercent,
      take_profit_percent: takeProfitPercent,
      max_position_size: maxPositionSize,
      
      // Advanced parameters
      min_risk_reward_ratio: minRiskRewardRatio,
      risk_per_trade_percent: riskPerTradePercent,
      max_leverage: maxLeverage,
      max_portfolio_exposure: maxPortfolioExposure,
      daily_loss_limit_percent: dailyLossLimitPercent,
      
      // Trailing stop
      trailing_stop: trailingStopEnabled ? {
        enabled: true,
        activation_percent: trailingActivationPercent,
        trailing_percent: trailingPercent
      } : { enabled: false },
      
      // Trading window
      trading_window: tradingWindowEnabled ? {
        enabled: true,
        start_hour: startHour,
        end_hour: endHour,
        days_of_week: daysOfWeek
      } : { enabled: false },
      
      // Cooldown
      cooldown: cooldownEnabled ? {
        enabled: true,
        cooldown_minutes: cooldownMinutes,
        trigger_loss_count: triggerLossCount
      } : { enabled: false },
      
      // AI mode
      ai_prompt_id: aiPromptId,
      ai_prompt_custom: aiPromptCustom,
      ai_update_frequency_minutes: aiUpdateFrequency,
      ai_allow_override: aiAllowOverride,
      ai_min_stop_loss: aiMinStopLoss,
      ai_max_stop_loss: aiMaxStopLoss,
      ai_min_take_profit: aiMinTakeProfit,
      ai_max_take_profit: aiMaxTakeProfit
    }
  }

  const handleSave = async () => {
    // Validation: must have either onSave callback, botId, or subscriptionId
    if (!onSave && !botId && !subscriptionId) {
      toast.error('⚠️ Unable to save: No bot or subscription specified')
      return
    }
    
    setLoading(true)
    try {
      const config = buildConfig()
      
      if (onSave) {
        // Custom save handler
        await onSave(config)
      } else if (botId) {
        // Save bot-level default configuration
        const response = await fetch(`/api/v1/risk-management/bots/${botId}/risk-config`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify(config)
        })
        
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to save bot risk configuration')
        }
        
        toast.success('✅ Bot default risk configuration saved successfully!')
      } else if (subscriptionId) {
        // Save subscription-specific configuration (overrides bot defaults)
        const response = await fetch(`/api/v1/risk-management/subscriptions/${subscriptionId}/risk-config`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
          },
          body: JSON.stringify(config)
        })
        
        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || 'Failed to save subscription risk configuration')
        }
        
        toast.success('✅ Subscription risk configuration saved successfully!')
      }
    } catch (error: any) {
      console.error('Error saving risk configuration:', error)
      toast.error(`❌ ${error.message || 'Failed to save risk configuration'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleTest = async () => {
    setTesting(true)
    try {
      if (!subscriptionId) {
        toast.error('Subscription ID required for testing')
        return
      }
      
      const config = buildConfig()
      
      // Test scenario
      const testScenario = {
        signal: {
          action: 'BUY',
          entry_price: 50000,
          stop_loss: 49000,
          take_profit: 52000,
          confidence: 0.75
        },
        market: {
          current_price: 50000,
          volatility: 0.05
        },
        account: {
          totalWalletBalance: 10000,
          availableBalance: 8000,
          positions: []
        }
      }
      
      const response = await fetch(`/api/v1/risk-management/subscriptions/${subscriptionId}/risk-config/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(testScenario)
      })
      
      if (!response.ok) {
        throw new Error('Test failed')
      }
      
      const result = await response.json()
      
      if (result.approved) {
        toast.success(`✅ Test passed! ${result.reason}`)
      } else {
        toast.error(`❌ Test failed: ${result.reason}`)
      }
      
      if (result.warnings && result.warnings.length > 0) {
        result.warnings.forEach((warning: string) => {
          toast(warning, { icon: '⚠️' })
        })
      }
    } catch (error) {
      console.error('Error testing configuration:', error)
      toast.error('Failed to test configuration')
    } finally {
      setTesting(false)
    }
  }

  const dayNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

  return (
    <div className="space-y-6">
      {/* Configuration Level Info Banner */}
      {botId && !subscriptionId && (
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <ShieldCheckIcon className="h-5 w-5 text-blue-400 mt-0.5" />
            <div>
              <h4 className="text-blue-300 font-medium">Bot-Level Configuration</h4>
              <p className="text-sm text-gray-400 mt-1">
                You are configuring the <strong>default risk management</strong> for this bot. 
                All subscriptions will use these settings unless individually overridden.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {subscriptionId && (
        <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <ShieldCheckIcon className="h-5 w-5 text-purple-400 mt-0.5" />
            <div>
              <h4 className="text-purple-300 font-medium">Subscription-Level Configuration</h4>
              <p className="text-sm text-gray-400 mt-1">
                You are configuring risk management for <strong>this specific subscription</strong>. 
                These settings override the bot's default configuration.
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <ShieldCheckIcon className="h-8 w-8 text-blue-500" />
            Risk Management Configuration
          </h2>
          <p className="text-gray-400 mt-1">Configure risk rules and limits for trading</p>
        </div>
        <div className="flex gap-2">
          {subscriptionId && (
            <button
              onClick={handleTest}
              disabled={testing}
              className="px-4 py-2 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              <BeakerIcon className="h-5 w-5" />
              {testing ? 'Testing...' : 'Test Config'}
            </button>
          )}
          <button
            onClick={handleSave}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Save Configuration'}
          </button>
        </div>
      </div>

      {/* Mode Selector */}
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Risk Management Mode</h3>
        <div className="grid grid-cols-1 gap-4">
          <button
            onClick={() => setMode('DEFAULT')}
            className={`p-4 rounded-lg border-2 transition-all ${
              mode === 'DEFAULT'
                ? 'border-blue-500 bg-blue-900/30'
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="text-left">
              <h4 className="text-white font-semibold mb-2">DEFAULT Mode</h4>
              <p className="text-sm text-gray-400">
                Rule-based risk management with manual configuration
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-1 rounded">Predictable</span>
                <span className="text-xs bg-blue-900/50 text-blue-300 px-2 py-1 rounded">Simple</span>
              </div>
            </div>
          </button>
          
          {/* AI_PROMPT Mode - Temporarily hidden until fully implemented */}
          {/* <button
            onClick={() => setMode('AI_PROMPT')}
            className={`p-4 rounded-lg border-2 transition-all ${
              mode === 'AI_PROMPT'
                ? 'border-purple-500 bg-purple-900/30'
                : 'border-gray-600 hover:border-gray-500'
            }`}
          >
            <div className="text-left">
              <h4 className="text-white font-semibold mb-2">AI_PROMPT Mode</h4>
              <p className="text-sm text-gray-400">
                Dynamic risk analysis powered by AI/LLM
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                <span className="text-xs bg-purple-900/50 text-purple-300 px-2 py-1 rounded">Adaptive</span>
                <span className="text-xs bg-purple-900/50 text-purple-300 px-2 py-1 rounded">Advanced</span>
              </div>
            </div>
          </button> */}
        </div>
      </div>

      {/* DEFAULT Mode Configuration */}
      {mode === 'DEFAULT' && (
        <div className="space-y-6">
          {/* Basic Risk Parameters */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Basic Risk Parameters</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Stop Loss (%)
                </label>
                <input
                  type="number"
                  value={stopLossPercent}
                  onChange={(e) => setStopLossPercent(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  max="100"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Take Profit (%)
                </label>
                <input
                  type="number"
                  value={takeProfitPercent}
                  onChange={(e) => setTakeProfitPercent(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Position Size (%)
                </label>
                <input
                  type="number"
                  value={maxPositionSize}
                  onChange={(e) => setMaxPositionSize(parseFloat(e.target.value))}
                  step="1"
                  min="1"
                  max="100"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Advanced Risk Parameters */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Advanced Risk Control</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Min Risk/Reward Ratio (e.g., 2 = 2:1)
                </label>
                <input
                  type="number"
                  value={minRiskRewardRatio}
                  onChange={(e) => setMinRiskRewardRatio(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.5"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Risk Per Trade (%)
                </label>
                <input
                  type="number"
                  value={riskPerTradePercent}
                  onChange={(e) => setRiskPerTradePercent(parseFloat(e.target.value))}
                  step="0.5"
                  min="0.1"
                  max="20"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Leverage (x)
                </label>
                <input
                  type="number"
                  value={maxLeverage}
                  onChange={(e) => setMaxLeverage(parseInt(e.target.value))}
                  step="1"
                  min="1"
                  max="125"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Portfolio Exposure (%)
                </label>
                <input
                  type="number"
                  value={maxPortfolioExposure}
                  onChange={(e) => setMaxPortfolioExposure(parseFloat(e.target.value))}
                  step="5"
                  min="10"
                  max="100"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Daily Loss Limit (%)
                </label>
                <input
                  type="number"
                  value={dailyLossLimitPercent}
                  onChange={(e) => setDailyLossLimitPercent(parseFloat(e.target.value))}
                  step="1"
                  min="1"
                  max="50"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Trading will stop when daily loss reaches this limit</p>
              </div>
            </div>
          </div>

          {/* Trailing Stop */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Trailing Stop Loss</h3>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={trailingStopEnabled}
                  onChange={(e) => setTrailingStopEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            
            {trailingStopEnabled && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Activation Profit (%)
                  </label>
                  <input
                    type="number"
                    value={trailingActivationPercent}
                    onChange={(e) => setTrailingActivationPercent(parseFloat(e.target.value))}
                    step="0.5"
                    min="0.5"
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Profit % to activate trailing</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Trailing Distance (%)
                  </label>
                  <input
                    type="number"
                    value={trailingPercent}
                    onChange={(e) => setTrailingPercent(parseFloat(e.target.value))}
                    step="0.5"
                    min="0.1"
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Distance from peak to trail</p>
                </div>
              </div>
            )}
          </div>

          {/* Trading Window */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Trading Window</h3>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={tradingWindowEnabled}
                  onChange={(e) => setTradingWindowEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            
            {tradingWindowEnabled && (
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Start Hour (UTC)
                    </label>
                    <input
                      type="number"
                      value={startHour}
                      onChange={(e) => setStartHour(parseInt(e.target.value))}
                      min="0"
                      max="23"
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      End Hour (UTC)
                    </label>
                    <input
                      type="number"
                      value={endHour}
                      onChange={(e) => setEndHour(parseInt(e.target.value))}
                      min="0"
                      max="23"
                      className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Trading Days
                  </label>
                  <div className="flex gap-2">
                    {dayNames.map((day, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          if (daysOfWeek.includes(index)) {
                            setDaysOfWeek(daysOfWeek.filter(d => d !== index))
                          } else {
                            setDaysOfWeek([...daysOfWeek, index])
                          }
                        }}
                        className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                          daysOfWeek.includes(index)
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                        }`}
                      >
                        {day}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Cooldown */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Cooldown After Losses</h3>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={cooldownEnabled}
                  onChange={(e) => setCooldownEnabled(e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
            
            {cooldownEnabled && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Cooldown Duration (minutes)
                  </label>
                  <input
                    type="number"
                    value={cooldownMinutes}
                    onChange={(e) => setCooldownMinutes(parseInt(e.target.value))}
                    step="5"
                    min="5"
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Trigger After N Losses
                  </label>
                  <input
                    type="number"
                    value={triggerLossCount}
                    onChange={(e) => setTriggerLossCount(parseInt(e.target.value))}
                    step="1"
                    min="1"
                    max="10"
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Mode Configuration */}
      {mode === 'AI_PROMPT' && (
        <div className="space-y-6">
          <div className="bg-purple-900/20 border border-purple-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-2">AI-Powered Risk Management</h3>
            <p className="text-gray-400 mb-4">
              Use AI/LLM to dynamically analyze market conditions and adjust risk parameters in real-time.
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  AI Prompt (Custom)
                </label>
                <textarea
                  value={aiPromptCustom}
                  onChange={(e) => setAiPromptCustom(e.target.value)}
                  placeholder="Enter custom AI prompt for risk analysis..."
                  className="w-full p-3 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500 h-32 resize-none"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Or select a prompt template from the Risk Management Prompts tab below
                </p>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Update Frequency (minutes)
                  </label>
                  <input
                    type="number"
                    value={aiUpdateFrequency}
                    onChange={(e) => setAiUpdateFrequency(parseInt(e.target.value))}
                    step="5"
                    min="5"
                    max="60"
                    className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                  />
                </div>
                
                <div className="flex items-center">
                  <label className="flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={aiAllowOverride}
                      onChange={(e) => setAiAllowOverride(e.target.checked)}
                      className="w-4 h-4 text-purple-600 bg-gray-700 border-gray-600 rounded focus:ring-purple-500"
                    />
                    <span className="ml-2 text-sm text-gray-300">Allow AI to override defaults</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* AI Safety Bounds */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">AI Safety Bounds</h3>
            <p className="text-sm text-gray-400 mb-4">
              Set limits that AI cannot exceed for safety
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Min Stop Loss (%)
                </label>
                <input
                  type="number"
                  value={aiMinStopLoss}
                  onChange={(e) => setAiMinStopLoss(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Stop Loss (%)
                </label>
                <input
                  type="number"
                  value={aiMaxStopLoss}
                  onChange={(e) => setAiMaxStopLoss(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Min Take Profit (%)
                </label>
                <input
                  type="number"
                  value={aiMinTakeProfit}
                  onChange={(e) => setAiMinTakeProfit(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Max Take Profit (%)
                </label>
                <input
                  type="number"
                  value={aiMaxTakeProfit}
                  onChange={(e) => setAiMaxTakeProfit(parseFloat(e.target.value))}
                  step="0.1"
                  min="0.1"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
            </div>
          </div>

          {/* Fallback Settings - Also show DEFAULT mode basics for AI mode */}
          <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Fallback Settings</h3>
            <p className="text-sm text-gray-400 mb-4">
              These settings will be used if AI is unavailable
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Fallback Risk Per Trade (%)
                </label>
                <input
                  type="number"
                  value={riskPerTradePercent}
                  onChange={(e) => setRiskPerTradePercent(parseFloat(e.target.value))}
                  step="0.5"
                  min="0.1"
                  max="20"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Fallback Max Leverage (x)
                </label>
                <input
                  type="number"
                  value={maxLeverage}
                  onChange={(e) => setMaxLeverage(parseInt(e.target.value))}
                  step="1"
                  min="1"
                  max="125"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Daily Loss Limit (%)
                </label>
                <input
                  type="number"
                  value={dailyLossLimitPercent}
                  onChange={(e) => setDailyLossLimitPercent(parseFloat(e.target.value))}
                  step="1"
                  min="1"
                  max="50"
                  className="w-full p-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:ring-purple-500 focus:border-purple-500"
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

