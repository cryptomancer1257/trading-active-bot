'use client'

import { useState } from 'react'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { 
  CpuChipIcon, 
  BoltIcon, 
  ShieldCheckIcon, 
  ChartBarIcon,
  CloudArrowUpIcon,
  Cog6ToothIcon,
  SparklesIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { useCreateBot } from '@/hooks/useBots'

// Bot creation schema
const botSchema = z.object({
  name: z.string().min(1, 'Entity name is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  bot_type: z.enum(['TECHNICAL', 'ML', 'DL', 'LLM', 'FUTURES', 'FUTURES_RPA', 'SPOT']),
  // bot_mode is auto-set based on template type
  exchange_type: z.enum(['BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI']),
  trading_pair: z.string().default('BTC/USDT'),
  timeframe: z.string().default('1h'),
  timeframes: z.array(z.string()).default(['1h']),
  version: z.string().default('1.0.0'),
  template: z.enum(['binance_futures_bot', 'binance_futures_rpa_bot', 'binance_signals_bot', 'custom']),
  // Advanced configuration
  leverage: z.number().min(1).max(125).default(10),
  risk_percentage: z.number().min(0.1).max(10).default(2),
  stop_loss_percentage: z.number().min(0.1).max(20).default(5),
  take_profit_percentage: z.number().min(0.5).max(50).default(10),
  // LLM Configuration
  llm_provider: z.enum(['openai', 'anthropic', 'gemini']).optional(),
  enable_image_analysis: z.boolean().default(false),
  enable_sentiment_analysis: z.boolean().default(false),
})

type BotFormData = z.infer<typeof botSchema>

const botTemplates = [
  {
    id: 'binance_futures_bot',
    name: '🚀 Futures Quantum Entity',
    description: 'Advanced futures trading with LLM AI analysis, leverage, and quantum risk management',
    type: 'FUTURES',
    features: ['LLM Integration', 'Leverage Trading', 'Stop Loss/Take Profit', 'Real-time Analysis'],
    gradient: 'from-quantum-500 to-purple-600',
    complexity: 'Advanced',
    templateFile: 'binance_futures_bot.py'
  },
  {
    id: 'binance_futures_rpa_bot',
    name: '👁️ Visual Analysis Entity',
    description: 'RPA-powered chart capture with AI image analysis for visual trading decisions',
    type: 'FUTURES_RPA',
    features: ['Chart Analysis', 'Image Recognition', 'RPA Automation', 'Visual AI'],
    gradient: 'from-cyber-500 to-blue-600',
    complexity: 'Expert',
    templateFile: 'binance_futures_rpa_bot.py'
  },
  {
    id: 'binance_spot_bot',
    name: '💎 Spot Trading Entity',
    description: 'Professional spot trading with risk management for BTC, ETH, and major altcoins',
    type: 'SPOT',
    features: ['Spot Trading', 'Risk Management', 'Multi-Pair Support', 'Portfolio Balance'],
    gradient: 'from-green-500 to-emerald-600',
    complexity: 'Intermediate',
    templateFile: 'binance_spot_bot.py'
  },
  {
    id: 'binance_signals_bot',
    name: '📡 Signal Intelligence Entity',
    description: 'Pure signal generation with LLM analysis - no trading, only intelligent signals',
    type: 'LLM',
    features: ['Signal Generation', 'Market Analysis', 'No API Keys', 'Pure Intelligence'],
    gradient: 'from-neural-500 to-green-600',
    complexity: 'Intermediate',
    templateFile: 'binance_signals_bot.py'
  },
  {
    id: 'custom',
    name: '⚡ Custom Neural Entity',
    description: 'Build your own AI entity from scratch with custom neural architecture',
    type: 'TECHNICAL',
    features: ['Custom Logic', 'Full Control', 'Advanced Config', 'Neural Framework'],
    gradient: 'from-yellow-500 to-orange-600',
    complexity: 'Expert',
    templateFile: null // No template file for custom
  }
]

const exchangeTypes = [
  { value: 'BINANCE', label: '🟡 Binance', description: 'World\'s largest crypto exchange' },
  { value: 'BYBIT', label: '🟠 Bybit', description: 'Advanced derivatives platform' },
  { value: 'COINBASE', label: '🔵 Coinbase', description: 'US-based secure exchange' },
  { value: 'KRAKEN', label: '🟣 Kraken', description: 'European regulated exchange' },
  { value: 'HUOBI', label: '🔴 Huobi', description: 'Global digital asset exchange' }
]

const timeframeOptions = [
  '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
]

export default function ForgePage() {
  const { user, loading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.DEVELOPER 
  })
  const router = useRouter()
  const [step, setStep] = useState(1)
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const createBotMutation = useCreateBot()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors }
  } = useForm<BotFormData>({
    resolver: zodResolver(botSchema),
    defaultValues: {
      // bot_mode is auto-set based on template
      exchange_type: 'BINANCE',
      trading_pair: 'BTC/USDT',
      timeframe: '1h',
      timeframes: ['1h'],
      version: '1.0.0',
      leverage: 10,
      risk_percentage: 2,
      stop_loss_percentage: 5,
      take_profit_percentage: 10,
      enable_image_analysis: false,
      enable_sentiment_analysis: false
    }
  })

  const watchedTemplate = watch('template')
  const watchedBotType = watch('bot_type')

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Initializing Neural Forge...</p>
        </div>
      </div>
    )
  }

  const handleTemplateSelect = (template: typeof botTemplates[0]) => {
    setSelectedTemplate(template.id)
    setValue('template', template.id as any)
    setValue('bot_type', template.type as any)
    setValue('name', template.name)
    setValue('description', template.description)
    setStep(2)
  }

  const onSubmit = async (data: BotFormData) => {
    setIsSubmitting(true)
    try {
      console.log('Creating bot with data:', data)
      
      toast.success('🧠 Neural Entity creation initiated! Processing quantum architecture...')
      
      // Get selected template info
      const selectedTemplateInfo = botTemplates.find(t => t.id === data.template)
      
      // Auto-set bot_type and bot_mode based on template
      const templateType = selectedTemplateInfo?.type || 'TECHNICAL'
      const activeBotTypes = ['FUTURES', 'FUTURES_RPA', 'SPOT']
      const autoBotMode = activeBotTypes.includes(templateType) ? 'ACTIVE' : 'PASSIVE'
      
      // Call the actual API
      await createBotMutation.mutateAsync({
        name: data.name,
        description: data.description,
        bot_type: templateType, // Use template type
        bot_mode: autoBotMode, // Auto-set based on template type
        exchange_type: data.exchange_type,
        trading_pair: data.trading_pair,
        timeframe: data.timeframe,
        timeframes: data.timeframes,
        version: data.version,
        template: data.template,
        templateFile: selectedTemplateInfo?.templateFile, // Add template file
        leverage: data.leverage,
        risk_percentage: data.risk_percentage,
        stop_loss_percentage: data.stop_loss_percentage,
        take_profit_percentage: data.take_profit_percentage,
        llm_provider: data.llm_provider,
        enable_image_analysis: data.enable_image_analysis,
        enable_sentiment_analysis: data.enable_sentiment_analysis,
      })
      
      toast.success('⚡ Neural Entity successfully forged! Deploying to quantum matrix...')
      
      // Small delay to ensure cache is refreshed before redirect
      setTimeout(() => {
        router.push('/creator/entities')
      }, 1000)
      
    } catch (error: any) {
      console.error('Bot creation error:', error)
      let message = 'Failed to forge neural entity'
      
      if (error.response?.data?.detail) {
        message = error.response.data.detail
      } else if (error.response?.status === 500) {
        message = 'Backend server error - database may not be initialized'
      } else if (error.message === 'Network Error') {
        message = 'Cannot connect to backend server'
      } else if (error.message) {
        message = error.message
      }
      
      toast.error(`🚨 Quantum Matrix Disruption: ${message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-extrabold cyber-text mb-4">
          🧠 Neural Entity Forge
        </h1>
        <p className="text-xl text-gray-400 max-w-3xl mx-auto">
          Architect an autonomous AI entity with quantum-enhanced trading capabilities. 
          Select a neural template or design your own custom architecture.
        </p>
        
        {/* Progress Indicator */}
        <div className="flex justify-center mt-8">
          <div className="flex items-center space-x-4">
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
              step >= 1 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
            }`}>
              1
            </div>
            <div className={`w-16 h-1 ${step >= 2 ? 'bg-quantum-500' : 'bg-gray-600'}`}></div>
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
              step >= 2 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
            }`}>
              2
            </div>
            <div className={`w-16 h-1 ${step >= 3 ? 'bg-quantum-500' : 'bg-gray-600'}`}></div>
            <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
              step >= 3 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
            }`}>
              3
            </div>
          </div>
        </div>
        
        <div className="flex justify-center mt-4 text-sm text-gray-400">
          <span className={step === 1 ? 'text-quantum-400 font-medium' : ''}>Template Selection</span>
          <span className="mx-4">→</span>
          <span className={step === 2 ? 'text-quantum-400 font-medium' : ''}>Configuration</span>
          <span className="mx-4">→</span>
          <span className={step === 3 ? 'text-quantum-400 font-medium' : ''}>Neural Architecture</span>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Step 1: Template Selection */}
        {step === 1 && (
          <div className="animate-fade-in">
            <h2 className="text-2xl font-bold cyber-text text-center mb-8">
              Select Neural Template
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {botTemplates.map((template, index) => (
                <div
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  className="card-quantum p-6 cursor-pointer hover:shadow-2xl hover:shadow-quantum-500/20 transition-all duration-300 transform hover:-translate-y-2 animate-fade-in"
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className={`p-3 rounded-lg bg-gradient-to-r ${template.gradient} shadow-lg`}>
                      <CpuChipIcon className="h-8 w-8 text-white" />
                    </div>
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      template.complexity === 'Expert' ? 'bg-danger-500/20 text-danger-400' :
                      template.complexity === 'Advanced' ? 'bg-quantum-500/20 text-quantum-400' :
                      'bg-neural-500/20 text-neural-400'
                    }`}>
                      {template.complexity}
                    </span>
                  </div>
                  
                  <h3 className="text-xl font-bold text-gray-200 mb-3">{template.name}</h3>
                  <p className="text-gray-400 mb-4 leading-relaxed">{template.description}</p>
                  
                  <div className="flex flex-wrap gap-2 mb-4">
                    {template.features.map((feature) => (
                      <span
                        key={feature}
                        className="px-2 py-1 bg-dark-700/50 text-gray-300 text-xs rounded-full"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="text-sm text-gray-500">Type: {template.type}</span>
                      <span className="text-xs text-gray-600">
                        Mode: {['FUTURES', 'FUTURES_RPA', 'SPOT'].includes(template.type) ? '⚡ Active' : '🛡️ Passive'}
                      </span>
                    </div>
                    <button
                      type="button"
                      className="btn btn-primary px-4 py-2 text-sm"
                    >
                      Select Template
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Basic Configuration */}
        {step === 2 && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold cyber-text">
                Configure Neural Entity
              </h2>
              <button
                type="button"
                onClick={() => setStep(1)}
                className="btn btn-secondary px-4 py-2"
              >
                ← Back to Templates
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Basic Information */}
              <div className="card-quantum p-6">
                <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
                  <DocumentTextIcon className="h-5 w-5 mr-2" />
                  Basic Information
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="form-label">Entity Name</label>
                    <input
                      {...register('name')}
                      className="form-input"
                      placeholder="Enter neural entity name..."
                    />
                    {errors.name && <p className="form-error">{errors.name.message}</p>}
                  </div>
                  
                  <div>
                    <label className="form-label">Description</label>
                    <textarea
                      {...register('description')}
                      rows={3}
                      className="form-input"
                      placeholder="Describe your AI entity's capabilities..."
                    />
                    {errors.description && <p className="form-error">{errors.description.message}</p>}
                  </div>
                  
                  {/* Entity Mode is auto-set based on template type */}
                </div>
              </div>

              {/* Exchange Configuration */}
              <div className="card-cyber p-6">
                <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
                  <Cog6ToothIcon className="h-5 w-5 mr-2" />
                  Exchange Settings
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="form-label">Exchange Platform</label>
                    <select {...register('exchange_type')} className="form-input">
                      {exchangeTypes.map((exchange) => (
                        <option key={exchange.value} value={exchange.value}>
                          {exchange.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div>
                    <label className="form-label">Trading Pair</label>
                    <input
                      {...register('trading_pair')}
                      className="form-input"
                      placeholder="BTC/USDT"
                    />
                  </div>
                  
                  <div>
                    <label className="form-label">Primary Timeframe</label>
                    <select {...register('timeframe')} className="form-input">
                      {timeframeOptions.map((tf) => (
                        <option key={tf} value={tf}>{tf}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="flex justify-center mt-8">
              <button
                type="button"
                onClick={() => setStep(3)}
                className="btn btn-primary px-8 py-3"
              >
                Continue to Neural Architecture →
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Advanced Configuration */}
        {step === 3 && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-8">
              <h2 className="text-2xl font-bold cyber-text">
                Neural Architecture
              </h2>
              <button
                type="button"
                onClick={() => setStep(2)}
                className="btn btn-secondary px-4 py-2"
              >
                ← Back to Configuration
              </button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Risk Management */}
              <div className="card-quantum p-6">
                <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
                  <ShieldCheckIcon className="h-5 w-5 mr-2" />
                  Risk Management Matrix
                </h3>
                
                <div className="space-y-4">
                  {watchedBotType === 'FUTURES' && (
                    <div>
                      <label className="form-label">Leverage (1-125x)</label>
                      <input
                        type="number"
                        {...register('leverage', { valueAsNumber: true })}
                        className="form-input"
                        min="1"
                        max="125"
                      />
                    </div>
                  )}
                  
                  <div>
                    <label className="form-label">Risk Percentage per Trade</label>
                    <input
                      type="number"
                      step="0.1"
                      {...register('risk_percentage', { valueAsNumber: true })}
                      className="form-input"
                      min="0.1"
                      max="10"
                    />
                  </div>
                  
                  <div>
                    <label className="form-label">Stop Loss Percentage</label>
                    <input
                      type="number"
                      step="0.1"
                      {...register('stop_loss_percentage', { valueAsNumber: true })}
                      className="form-input"
                      min="0.1"
                      max="20"
                    />
                  </div>
                  
                  <div>
                    <label className="form-label">Take Profit Percentage</label>
                    <input
                      type="number"
                      step="0.1"
                      {...register('take_profit_percentage', { valueAsNumber: true })}
                      className="form-input"
                      min="0.5"
                      max="50"
                    />
                  </div>
                </div>
              </div>

              {/* AI Configuration */}
              <div className="card-cyber p-6">
                <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
                  <SparklesIcon className="h-5 w-5 mr-2" />
                  AI Enhancement Matrix
                </h3>
                
                <div className="space-y-4">
                  {(watchedBotType === 'LLM' || watchedBotType === 'FUTURES' || watchedBotType === 'FUTURES_RPA') && (
                    <div>
                      <label className="form-label">LLM Provider</label>
                      <select {...register('llm_provider')} className="form-input">
                        <option value="">Select AI Provider</option>
                        <option value="openai">🤖 OpenAI (GPT-4)</option>
                        <option value="anthropic">🧠 Anthropic (Claude)</option>
                        <option value="gemini">💎 Google (Gemini)</option>
                      </select>
                    </div>
                  )}
                  
                  {watchedBotType === 'FUTURES_RPA' && (
                    <div className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        {...register('enable_image_analysis')}
                        className="w-4 h-4 text-quantum-600 rounded"
                      />
                      <label className="text-sm text-gray-300">
                        Enable Visual Chart Analysis
                      </label>
                    </div>
                  )}
                  
                  <div className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      {...register('enable_sentiment_analysis')}
                      className="w-4 h-4 text-quantum-600 rounded"
                    />
                    <label className="text-sm text-gray-300">
                      Enable Market Sentiment Analysis
                    </label>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Submit Button */}
            <div className="card-quantum p-8 mt-8 text-center">
              <h3 className="text-xl font-bold cyber-text mb-4">
                Ready to Forge Neural Entity?
              </h3>
              <p className="text-gray-400 mb-6">
                Your AI entity will be deployed to the quantum matrix and begin learning immediately.
              </p>
              
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn btn-cyber px-12 py-4 text-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Forging Neural Entity...
                  </>
                ) : (
                  <>
                    🧠 Forge Neural Entity
                  </>
                )}
              </button>
              
              <p className="text-xs text-gray-500 mt-4">
                ⚡ Quantum processing • 🧬 Neural architecture • 🔐 Encrypted deployment
              </p>
            </div>
          </div>
        )}
      </form>

      {/* Floating Neural Particles */}
      <div className="fixed top-20 left-20 w-1 h-1 bg-quantum-500 rounded-full animate-neural-pulse opacity-60"></div>
      <div className="fixed top-40 right-32 w-1.5 h-1.5 bg-cyber-400 rounded-full animate-neural-pulse opacity-40" style={{ animationDelay: '1s' }}></div>
      <div className="fixed bottom-40 left-32 w-2 h-2 bg-neural-500 rounded-full animate-neural-pulse opacity-50" style={{ animationDelay: '2s' }}></div>
      <div className="fixed bottom-20 right-20 w-1 h-1 bg-quantum-400 rounded-full animate-neural-pulse opacity-30" style={{ animationDelay: '3s' }}></div>
    </div>
  )
}
