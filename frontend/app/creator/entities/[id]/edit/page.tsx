'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAuthGuard } from '@/hooks/useAuthGuard'
import { UserRole } from '@/lib/types'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { useGetBot, useUpdateBot } from '@/hooks/useBots'
import { 
  CpuChipIcon, 
  ArrowLeftIcon,
  Cog6ToothIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'

// Bot edit schema (similar to create but without template)
const botEditSchema = z.object({
  name: z.string().min(1, 'Entity name is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  exchange_type: z.enum(['BINANCE', 'COINBASE', 'KRAKEN', 'BYBIT', 'HUOBI']),
  trading_pair: z.string().default('BTC/USDT'),
  timeframe: z.string().default('1h'),
  timeframes: z.array(z.string()).default(['1h']).optional(),
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

type BotEditFormData = z.infer<typeof botEditSchema>

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

export default function EditBotPage() {
  const { user, loading: authLoading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.DEVELOPER 
  })
  
  const router = useRouter()
  const params = useParams()
  const botId = params?.id as string
  
  const { data: bot, isLoading: botLoading, error } = useGetBot(botId)
  const updateBotMutation = useUpdateBot()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid }
  } = useForm<BotEditFormData>({
    resolver: zodResolver(botEditSchema),
  })
  
  // Debug form errors
  console.log('🔍 Form errors:', errors)
  console.log('🔍 Form is valid:', isValid)

  // Populate form when bot data loads
  useEffect(() => {
    if (bot) {
      console.log('🔄 Populating form with bot data:', bot)
      console.log('🔄 Bot exchange_type:', bot.exchange_type)
      console.log('🔄 Bot timeframe:', bot.timeframe)
      console.log('🔄 Bot llm_provider:', (bot as any).llm_provider)
      
      setValue('name', bot.name)
      setValue('description', bot.description)
      setValue('exchange_type', (bot.exchange_type as any) || 'BINANCE')
      setValue('trading_pair', bot.trading_pair || 'BTC/USDT')
      setValue('timeframe', bot.timeframe || '1h')
      
      // Ensure timeframes is always an array
      const timeframesArray = Array.isArray((bot as any).timeframes) ? (bot as any).timeframes : [bot.timeframe || '1h']
      setValue('timeframes', timeframesArray)
      console.log('🔄 Setting timeframes to:', timeframesArray)
      
      setValue('leverage', (bot as any).leverage || 10)
      setValue('risk_percentage', (bot as any).risk_percentage || 2)
      setValue('stop_loss_percentage', (bot as any).stop_loss_percentage || 5)
      setValue('take_profit_percentage', (bot as any).take_profit_percentage || 10)
      setValue('llm_provider', (bot as any).llm_provider || '')
      console.log('🔄 Setting llm_provider to:', (bot as any).llm_provider)
      console.log('🔄 Current watch llm_provider:', watch('llm_provider'))
      setValue('enable_image_analysis', (bot as any).enable_image_analysis || false)
      setValue('enable_sentiment_analysis', (bot as any).enable_sentiment_analysis || false)
      
      console.log('✅ Form populated successfully')
    }
  }, [bot, setValue, watch])

  // Handle error
  useEffect(() => {
    if (error) {
      toast.error('Failed to load bot data')
      router.push('/creator/entities')
    }
  }, [error, router])

  const onSubmit = async (data: BotEditFormData) => {
    console.log('🔄 Form submitted with data:', data)
    console.log('🔄 Bot ID:', botId)
    console.log('🔄 Is submitting:', isSubmitting)
    
    // Ensure timeframes is always an array
    const cleanedData = {
      ...data,
      timeframes: Array.isArray(data.timeframes) ? data.timeframes : [data.timeframe]
    }
    console.log('🔄 Cleaned data:', cleanedData)
    
    setIsSubmitting(true)
    try {
      toast.success('🔄 Updating Neural Entity...')
      
      console.log('🔄 Calling updateBotMutation with:', { botId: parseInt(botId), data: cleanedData })
      
      const result = await updateBotMutation.mutateAsync({
        botId: parseInt(botId),
        data: cleanedData
      })
      
      console.log('✅ Update successful:', result)
      toast.success('⚡ Neural Entity successfully updated!')
      router.push('/creator/entities')
      
    } catch (error: any) {
      console.error('🚨 Bot update error:', error)
      const message = error.response?.data?.detail || error.message || 'Failed to update entity'
      toast.error(`🚨 Update failed: ${message}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  if (authLoading || botLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-quantum-500 mx-auto mb-4"></div>
          <p className="text-gray-300">Loading Neural Entity...</p>
        </div>
      </div>
    )
  }

  if (!bot) {
    return (
      <div className="min-h-screen flex items-center justify-center neural-grid">
        <div className="card-quantum p-8 text-center">
          <CpuChipIcon className="h-16 w-16 text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-gray-300 mb-2">Entity Not Found</h3>
          <p className="text-gray-400 mb-4">The requested neural entity could not be found.</p>
          <Link href="/creator/entities" className="btn btn-primary">
            Return to Arsenal
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen neural-grid py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-4">
            <Link 
              href="/creator/entities"
              className="btn btn-secondary p-2"
            >
              <ArrowLeftIcon className="h-5 w-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold cyber-text">
                Edit Neural Entity
              </h1>
              <p className="text-gray-400 mt-1">
                Modify your AI entity's configuration
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
              bot.status === 'APPROVED' ? 'bg-neural-500/20 text-neural-400' :
              bot.status === 'PENDING' ? 'bg-yellow-500/20 text-yellow-400' :
              'bg-gray-500/20 text-gray-400'
            }`}>
              {bot.status}
            </span>
            <span className="text-sm text-gray-500">v{bot.version}</span>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit, (errors) => {
          console.log('🚨 Form validation errors:', errors)
          toast.error('Please fix form validation errors')
        })} className="space-y-8">
          {/* Basic Information */}
          <div className="card-cyber p-6">
            <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
              <CpuChipIcon className="h-5 w-5 mr-2" />
              Basic Information
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="form-label">Entity Name</label>
                <input
                  {...register('name')}
                  className={`form-input ${errors.name ? 'border-red-500 ring-red-500' : ''}`}
                  placeholder="Enter entity name..."
                />
                {errors.name && <p className="form-error">❌ {errors.name.message}</p>}
              </div>
              
              <div>
                <label className="form-label">Trading Pair</label>
                <input
                  {...register('trading_pair')}
                  className={`form-input ${errors.trading_pair ? 'border-red-500 ring-red-500' : ''}`}
                  placeholder="BTC/USDT"
                />
                {errors.trading_pair && <p className="form-error">❌ {errors.trading_pair.message}</p>}
              </div>
            </div>
            
            <div className="mt-4">
              <label className="form-label">Description</label>
              <textarea
                {...register('description')}
                rows={3}
                className={`form-input ${errors.description ? 'border-red-500 ring-red-500' : ''}`}
                placeholder="Describe your AI entity's capabilities..."
              />
              {errors.description && <p className="form-error">❌ {errors.description.message}</p>}
            </div>
          </div>

          {/* Exchange Configuration */}
          <div className="card-cyber p-6">
            <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
              <Cog6ToothIcon className="h-5 w-5 mr-2" />
              Exchange Settings
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="form-label">Exchange</label>
                <select 
                  {...register('exchange_type')} 
                  className="form-input"
                  value={watch('exchange_type') || 'BINANCE'}
                >
                  {exchangeTypes.map(exchange => (
                    <option key={exchange.value} value={exchange.value}>
                      {exchange.label} - {exchange.description}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="form-label">Timeframe</label>
                <select 
                  {...register('timeframe')} 
                  className={`form-input ${errors.timeframe || errors.timeframes ? 'border-red-500 ring-red-500' : ''}`}
                  value={watch('timeframe') || '1h'}
                  onChange={(e) => {
                    const newTimeframe = e.target.value
                    setValue('timeframe', newTimeframe)
                    setValue('timeframes', [newTimeframe]) // Sync timeframes array
                    console.log('🔄 Updated timeframe to:', newTimeframe)
                  }}
                >
                  {timeframeOptions.map(tf => (
                    <option key={tf} value={tf}>{tf}</option>
                  ))}
                </select>
                {(errors.timeframe || errors.timeframes) && (
                  <p className="form-error">
                    ❌ {errors.timeframe?.message || errors.timeframes?.message || 'Timeframe is required'}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Advanced Configuration */}
          <div className="card-cyber p-6">
            <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
              <SparklesIcon className="h-5 w-5 mr-2" />
              Neural Configuration
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="form-label">Leverage (1x - 125x)</label>
                <input
                  type="number"
                  {...register('leverage', { valueAsNumber: true })}
                  min={1}
                  max={125}
                  className="form-input"
                />
              </div>
              
              <div>
                <label className="form-label">Risk Percentage (0.1% - 10%)</label>
                <input
                  type="number"
                  step="0.1"
                  {...register('risk_percentage', { valueAsNumber: true })}
                  min={0.1}
                  max={10}
                  className="form-input"
                />
              </div>
              
              <div>
                <label className="form-label">Stop Loss (%)</label>
                <input
                  type="number"
                  step="0.1"
                  {...register('stop_loss_percentage', { valueAsNumber: true })}
                  min={0.1}
                  max={20}
                  className="form-input"
                />
              </div>
              
              <div>
                <label className="form-label">Take Profit (%)</label>
                <input
                  type="number"
                  step="0.1"
                  {...register('take_profit_percentage', { valueAsNumber: true })}
                  min={0.5}
                  max={50}
                  className="form-input"
                />
              </div>
            </div>
            
            {/* LLM Configuration */}
            <div className="mt-6 border-t border-gray-700 pt-6">
              <h4 className="text-md font-semibold text-gray-300 mb-4">AI Enhancement</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <label className="form-label">LLM Provider</label>
                  <select 
                    {...register('llm_provider')} 
                    className="form-input"
                    value={watch('llm_provider') || ''}
                    key={`llm-${watch('llm_provider')}`}
                  >
                    <option value="">None</option>
                    <option value="openai">OpenAI GPT</option>
                    <option value="anthropic">Claude</option>
                    <option value="gemini">Google Gemini</option>
                  </select>
                </div>
                
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    {...register('enable_image_analysis')}
                    className="rounded border-gray-600 text-quantum-500 focus:ring-quantum-500"
                  />
                  <label className="form-label">Image Analysis</label>
                </div>
                
                <div className="flex items-center space-x-3">
                  <input
                    type="checkbox"
                    {...register('enable_sentiment_analysis')}
                    className="rounded border-gray-600 text-quantum-500 focus:ring-quantum-500"
                  />
                  <label className="form-label">Sentiment Analysis</label>
                </div>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-4">
            <Link
              href="/creator/entities"
              className="btn btn-secondary px-8 py-3"
            >
              Cancel
            </Link>
            
            {/* Debug button */}
            <button
              type="button"
              onClick={async () => {
                console.log('🧪 Direct API test')
                try {
                  const result = await updateBotMutation.mutateAsync({
                    botId: parseInt(botId),
                    data: { name: "Direct Test Update", description: "Testing direct API call" }
                  })
                  console.log('✅ Direct test successful:', result)
                  toast.success('Direct test successful!')
                } catch (error) {
                  console.error('❌ Direct test failed:', error)
                  toast.error('Direct test failed!')
                }
              }}
              className="btn btn-secondary px-4 py-3"
            >
              🧪 Test API
            </button>
            
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary px-8 py-3 disabled:opacity-50"
              onClick={() => console.log('🔘 Update button clicked!')}
            >
              {isSubmitting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Updating...
                </>
              ) : (
                '⚡ Update Entity'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
