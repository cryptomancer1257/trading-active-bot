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
import { usePlan } from '@/hooks/usePlan'
import { useFeatureFlag, FEATURE_FLAGS } from '@/hooks/useFeatureFlag'
import { api } from '@/lib/api'
import { 
  CpuChipIcon, 
  ArrowLeftIcon,
  Cog6ToothIcon,
  SparklesIcon,
  CloudArrowUpIcon,
  DocumentTextIcon,
  LinkIcon
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
  // Pricing
  price_per_month: z.number().min(0, 'Price must be 0 or higher').default(0),
  is_free: z.boolean().default(false),
  // Image upload
  image_url: z.string().optional().nullable(),
  // Advanced configuration
  leverage: z.number().min(1).max(125).default(10),
  risk_percentage: z.number().min(0.1).max(10).default(2),
  stop_loss_percentage: z.number().min(0.1).max(20).default(5),
  take_profit_percentage: z.number().min(0.5).max(50).default(10),
  // LLM Configuration
  llm_provider: z.enum(['openai', 'anthropic', 'claude', 'gemini']).optional(),
  llm_model: z.string().optional(),  // Specific model to use
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
  
  // Feature flags
  const canRePublishToMarketplace = useFeatureFlag(FEATURE_FLAGS.MARKETPLACE_REPUBLISH_BOT)
  const botId = params?.id as string
  
  const { data: bot, isLoading: botLoading, error } = useGetBot(botId)
  const updateBotMutation = useUpdateBot()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRepublishing, setIsRepublishing] = useState(false)
  const [justUpdated, setJustUpdated] = useState(false)
  
  // Plan limits
  const { currentPlan } = usePlan()
  const isPro = currentPlan?.plan_name === 'pro'

  // Image upload state
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string>('')
  const [isUploadingImage, setIsUploadingImage] = useState(false)

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isValid }
  } = useForm<BotEditFormData>({
    resolver: zodResolver(botEditSchema),
  })
  
  // Debug form errors and values
  const formValues = watch()
  console.log('🔍 Form errors:', errors)
  console.log('🔍 Form is valid:', isValid)
  console.log('🔍 Current form values:', formValues)
  console.log('🔍 price_per_month value:', formValues.price_per_month, 'type:', typeof formValues.price_per_month)

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
      
      // Pricing fields - Ensure price_per_month is a number
      const priceValue = (bot as any).price_per_month
      const priceNumber = typeof priceValue === 'string' ? parseFloat(priceValue) : (priceValue || 0)
      console.log('🔄 Setting price_per_month from bot:', priceValue, '→', priceNumber)
      console.log('🔄 Setting is_free from bot:', (bot as any).is_free)
      setValue('price_per_month', priceNumber)
      setValue('is_free', (bot as any).is_free || false)
      setValue('image_url', (bot as any).image_url || null)
      
      // Set image preview if exists
      if ((bot as any).image_url) {
        setImagePreview((bot as any).image_url)
      }
      
      // Load risk fields from risk_config (stored as JSON)
      const riskConfig = (bot as any).risk_config || {}
      
      console.log('🔍 DEBUG - Full bot object:', bot)
      console.log('🔍 DEBUG - risk_config from bot:', riskConfig)
      console.log('🔍 DEBUG - risk_config keys:', Object.keys(riskConfig))
      console.log('🔍 DEBUG - max_leverage:', riskConfig.max_leverage)
      console.log('🔍 DEBUG - risk_per_trade_percent:', riskConfig.risk_per_trade_percent)
      console.log('🔍 DEBUG - stop_loss_percent:', riskConfig.stop_loss_percent)
      console.log('🔍 DEBUG - take_profit_percent:', riskConfig.take_profit_percent)
      
      setValue('leverage', riskConfig.max_leverage || (bot as any).leverage || 10)
      setValue('risk_percentage', riskConfig.risk_per_trade_percent || riskConfig.max_position_size || (bot as any).risk_percentage || 2)
      setValue('stop_loss_percentage', riskConfig.stop_loss_percent || (bot as any).stop_loss_percentage || 5)
      setValue('take_profit_percentage', riskConfig.take_profit_percent || (bot as any).take_profit_percentage || 10)
      
      console.log('✅ After setValue:')
      console.log('   leverage:', watch('leverage'))
      console.log('   risk_percentage:', watch('risk_percentage'))
      console.log('   stop_loss_percentage:', watch('stop_loss_percentage'))
      console.log('   take_profit_percentage:', watch('take_profit_percentage'))
      
      // Load LLM config from strategy_config (stored as JSON)
      const strategyConfig = (bot as any).strategy_config || {}
      const llmProvider = strategyConfig.llm_provider || (bot as any).llm_provider || ''
      const llmModel = strategyConfig.llm_model || (bot as any).llm_model || ''
      
      setValue('llm_provider', llmProvider)
      setValue('llm_model', llmModel)
      console.log('🔄 Setting llm_provider to:', llmProvider)
      console.log('🔄 Setting llm_model to:', llmModel)
      
      setValue('enable_image_analysis', strategyConfig.enable_image_analysis || (bot as any).enable_image_analysis || false)
      setValue('enable_sentiment_analysis', strategyConfig.enable_sentiment_analysis || (bot as any).enable_sentiment_analysis || false)
      
      console.log('✅ Form populated successfully')
    }
  }, [bot, setValue])  // ❌ Removed 'watch' - it causes form to reset on every change!

  // Handle error
  useEffect(() => {
    if (error) {
      toast.error('Failed to load bot data')
      router.push('/creator/entities')
    }
  }, [error, router])

  // Image upload functions
  const handleImageSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        toast.error('Image must be smaller than 5MB')
        return
      }
      
      if (!file.type.startsWith('image/')) {
        toast.error('Please select an image file')
        return
      }
      
      setSelectedImage(file)
      
      // Create preview
      const reader = new FileReader()
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string)
      }
      reader.readAsDataURL(file)
    }
  }

  const uploadImage = async (): Promise<string | null> => {
    if (!selectedImage) return null

    setIsUploadingImage(true)
    try {
      console.log('📤 Uploading image to GCS...', selectedImage.name)
      const formData = new FormData()
      formData.append('file', selectedImage)

      const response = await api.post('/bots/upload-image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      console.log('📥 Upload response:', response.data)

      if (response.data && response.data.success && response.data.url) {
        console.log('✅ Avatar uploaded to GCS:', response.data.url)
        toast.success('✅ Avatar uploaded successfully!')
        return response.data.url
      } else {
        console.error('❌ Invalid upload response:', response.data)
        throw new Error('Upload failed - invalid response')
      }
    } catch (error: any) {
      console.error('❌ Upload error:', error)
      console.error('❌ Error response:', error.response?.data)
      toast.error(`❌ Upload failed: ${error.response?.data?.detail || error.message}`)
      return null
    } finally {
      setIsUploadingImage(false)
    }
  }

  // Re-publish bot function
  const handleRepublishBot = async () => {
    if (!botId) return

    setIsRepublishing(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/marketplace/publish-token?bot_id=${botId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) throw new Error('Failed to re-publish bot')

      const data = await response.json()
      console.log('📡 Re-publish response:', data)

      toast.success('🚀 Bot successfully re-published! Opening marketplace...')
      setJustUpdated(false) // Reset the updated state
      
      // Redirect to marketplace publish URL
      setTimeout(() => {
        if (data.publish_url) {
          window.open(data.publish_url, '_blank')
        }
      }, 1500)

    } catch (error: any) {
      toast.error(`❌ Re-publish failed: ${error.message}`)
    } finally {
      setIsRepublishing(false)
    }
  }

  const onSubmit = async (data: BotEditFormData) => {
    console.log('✅✅✅ SUBMIT HANDLER CALLED!')
    console.log('🔄 Form submitted with data:', data)
    console.log('🔄 PRICING DEBUG - price_per_month:', data.price_per_month)
    console.log('🔄 PRICING DEBUG - is_free:', data.is_free)
    console.log('🔄 IMAGE DEBUG - image_url:', data.image_url)
    console.log('🔄 IMAGE DEBUG - selectedImage:', selectedImage?.name)
    console.log('🔄 LLM DEBUG - llm_provider:', data.llm_provider)
    console.log('🔄 LLM DEBUG - llm_model:', data.llm_model)
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
      
      // Upload image if selected
      let imageUrl = data.image_url
      if (selectedImage) {
        const uploadedUrl = await uploadImage()
        if (uploadedUrl) {
          imageUrl = uploadedUrl
        }
      }

      // Include image URL in update data
      const finalData = {
        ...cleanedData,
        image_url: imageUrl
      }
      
      console.log('🔄 FINAL DATA - price_per_month:', finalData.price_per_month, typeof finalData.price_per_month)
      console.log('🔄 FINAL DATA - is_free:', finalData.is_free, typeof finalData.is_free)
      
      // Ensure price_per_month is a number
      if (finalData.price_per_month !== undefined) {
        finalData.price_per_month = Number(finalData.price_per_month)
        console.log('🔄 CONVERTED price_per_month:', finalData.price_per_month, typeof finalData.price_per_month)
      }
      
      console.log('🔄 Calling updateBotMutation with:', { botId: parseInt(botId), data: finalData })
      
      const result = await updateBotMutation.mutateAsync({
        botId: parseInt(botId),
        data: finalData
      })
      
      console.log('✅ Update successful:', result)
      toast.success('⚡ Neural Entity successfully updated! You can now re-publish to marketplace.')
      setJustUpdated(true)
      
      // Don't redirect - stay on edit page to allow re-publishing
      // router.push('/creator/entities')
      
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

        {/* Update Success Banner */}
        {justUpdated && (
          <div className="bg-gradient-to-r from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-lg p-4 mb-6">
            <div className="flex items-center space-x-3">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-green-400 font-medium">Entity Updated Successfully!</h3>
                <p className="text-green-300 text-sm">
                  Your changes have been saved.
                  {canRePublishToMarketplace && ' You can now re-publish to update the marketplace listing.'}
                </p>
              </div>
              <button
                onClick={() => setJustUpdated(false)}
                className="text-green-400 hover:text-green-300 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
              </button>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit, (errors) => {
          console.log('❌❌❌ VALIDATION FAILED!')
          console.log('🚨 Form validation errors:', errors)
          console.log('🚨 Current form values:', watch())
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

          {/* Entity Avatar & Pricing */}
          <div className="card-cyber p-6">
            <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
              <CloudArrowUpIcon className="h-5 w-5 mr-2" />
              Avatar & Marketplace Pricing
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Entity Avatar */}
              <div>
                <label className="form-label">Entity Avatar</label>
                <div className="space-y-4">
                  {/* Current/Preview Image */}
                  {imagePreview && (
                    <div className="relative w-24 h-24 rounded-lg overflow-hidden border-2 border-quantum-500/30">
                      <img 
                        src={imagePreview} 
                        alt="Avatar preview" 
                        className="w-full h-full object-cover"
                      />
                    </div>
                  )}
                  
                  {/* Upload Button */}
                  <div className="flex items-center space-x-3">
                    <label className="btn-secondary cursor-pointer">
                      {isUploadingImage ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-quantum-400"></div>
                          Uploading...
                        </>
                      ) : (
                        <>
                          <CloudArrowUpIcon className="h-4 w-4 mr-2" />
                          {imagePreview ? 'Change Avatar' : 'Upload Avatar'}
                        </>
                      )}
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleImageSelect}
                        className="hidden"
                        disabled={isUploadingImage}
                      />
                    </label>
                  </div>
                  <p className="text-xs text-gray-500">
                    🎨 Upload PNG, JPG or GIF (max 5MB)
                  </p>
                </div>
              </div>

              {/* Marketplace Pricing - Always show, feature flag only controls publish button */}
              <div>
                <label className="form-label">Marketplace Pricing</label>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <input
                          {...register('is_free')}
                          type="checkbox"
                          className="w-4 h-4 text-quantum-500 bg-dark-700 border-quantum-500/30 rounded focus:ring-quantum-500 focus:ring-2"
                          onChange={(e) => {
                            if (e.target.checked) {
                              setValue('price_per_month', 0)
                            }
                          }}
                        />
                        <label className="form-label !mb-0">Free to use</label>
                      </div>
                      {watch('is_free') ? (
                        <span className="text-xs text-gray-500">
                          💡 Uncheck to set price
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">
                          💰 Check to make free
                        </span>
                      )}
                    </div>
                    
                    {!watch('is_free') && (
                      <div className="animate-fade-in">
                        <label className="form-label">Price per Month (ICP)</label>
                        <div className="relative">
                          <input
                            {...register('price_per_month', { 
                              valueAsNumber: true,
                              onChange: (e) => {
                                console.log('💰 Price input changed:', e.target.value, typeof e.target.value)
                                console.log('💰 Current watch value:', watch('price_per_month'))
                              }
                            })}
                            type="number"
                            step="0.01"
                            min="0"
                            className="form-input pl-12"
                            placeholder="0.00"
                          />
                          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                            <span className="text-quantum-400 text-sm font-medium">ICP</span>
                          </div>
                        </div>
                        {errors.price_per_month && <p className="form-error">{errors.price_per_month.message}</p>}
                        <p className="text-xs text-gray-500 mt-1">
                          💡 Users will pay in Internet Computer Protocol (ICP) tokens
                        </p>
                      </div>
                    )}

                    {/* Pricing Preview */}
                    <div className="bg-dark-800/50 rounded-lg p-3 border border-quantum-500/20">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-400">Marketplace Price:</span>
                        <span className="text-quantum-400 font-medium">
                          {watch('is_free') ? 'FREE' : `${watch('price_per_month') || 0} ICP/month`}
                        </span>
                      </div>
                    </div>
                  </div>
              </div>
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
                <label className="form-label">Primary Timeframe</label>
                <select 
                  {...register('timeframe')} 
                  className={`form-input ${errors.timeframe || errors.timeframes ? 'border-red-500 ring-red-500' : ''}`}
                  value={watch('timeframe') || '1h'}
                  onChange={(e) => {
                    const newPrimary = e.target.value
                    setValue('timeframe', newPrimary)
                    
                    // Auto-remove new primary from extra timeframes if it exists
                    const currentExtras = watch('timeframes') || []
                    const cleanedExtras = currentExtras.filter(tf => tf !== newPrimary)
                    if (cleanedExtras.length !== currentExtras.length) {
                      setValue('timeframes', cleanedExtras)
                    }
                    
                    console.log('🔄 Updated timeframe to:', newPrimary, 'Cleaned extras:', cleanedExtras)
                  }}
                >
                  {timeframeOptions.map(tf => (
                    <option key={tf} value={tf}>{tf}</option>
                  ))}
                </select>
                <p className="mt-2 text-sm text-orange-400 flex items-start">
                  <svg className="w-4 h-4 mr-1.5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <span>
                    <strong>Trading Interval:</strong> Your bot will execute trades based on this timeframe. For example, if Primary Timeframe = 1h, the bot will analyze and trade once per hour. More frequent trades will consume more LLM Quota.
                  </span>
                </p>
                {(errors.timeframe || errors.timeframes) && (
                  <p className="form-error">
                    ❌ {errors.timeframe?.message || errors.timeframes?.message || 'Timeframe is required'}
                  </p>
                )}
              </div>
            </div>
            
            {/* Extra Timeframes */}
            <div className="mt-6">
              <label className="form-label">Extra Timeframes</label>
              <p className="mt-1 text-sm text-gray-400 mb-3">
                Reference timeframes for better decision making
              </p>
              <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                {timeframeOptions.map((tf) => {
                  const currentTimeframes = watch('timeframes') || []
                  const primaryTimeframe = watch('timeframe') || '1h'
                  const isPrimary = tf === primaryTimeframe
                  const isSelected = currentTimeframes.includes(tf) && !isPrimary
                  // Count only extra timeframes (exclude primary)
                  const extraCount = currentTimeframes.filter(t => t !== primaryTimeframe).length
                  const maxReached = extraCount >= 2 && !isSelected && !isPrimary
                  const isDisabled = isPrimary || maxReached
                  
                  return (
                    <button
                      key={tf}
                      type="button"
                      onClick={() => {
                        if (isDisabled) return
                        const newTimeframes = isSelected
                          ? currentTimeframes.filter(t => t !== tf)
                          : [...currentTimeframes, tf]
                        setValue('timeframes', newTimeframes)
                      }}
                      disabled={isDisabled}
                      className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                        isPrimary
                          ? 'bg-purple-900/30 border-purple-700 text-purple-400 cursor-not-allowed opacity-50'
                          : isSelected
                          ? 'bg-quantum-500/20 border-quantum-500 text-quantum-400'
                          : maxReached
                          ? 'bg-dark-700/30 border-gray-700 text-gray-500 cursor-not-allowed opacity-50'
                          : 'bg-dark-700/50 border-gray-600 text-gray-300 hover:bg-dark-600/50'
                      }`}
                    >
                      {tf} {isPrimary && '(Primary)'}
                    </button>
                  )
                })}
              </div>
              {(() => {
                const timeframes = watch('timeframes') || []
                const primary = watch('timeframe') || '1h'
                const extras = timeframes.filter(tf => tf !== primary)
                return extras.length > 0 && (
                  <div className="mt-2 text-sm text-gray-500">
                    <span className="font-medium">Selected:</span> {extras.join(', ')}
                  </div>
                )
              })()}
              
              {/* Combined Timeframes Preview */}
              <div className="mt-3 p-3 bg-blue-900/20 border border-blue-700/50 rounded-lg">
                <p className="text-sm text-blue-300">
                  <svg className="w-4 h-4 inline-block mr-1.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                  </svg>
                  <strong>Your bot will trade based on timeframes:</strong>{' '}
                  {(() => {
                    const primary = watch('timeframe') || '1h'
                    const extras = watch('timeframes') || []
                    const combined = [...extras, primary]
                    const allTimeframes = Array.from(new Set(combined)).sort((a, b) => {
                      const order = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
                      return order.indexOf(a) - order.indexOf(b)
                    })
                    return allTimeframes.join(', ')
                  })()}
                </p>
                <p className="text-xs text-blue-400 mt-1">
                  Example: If Extra Timeframes = 15m, 4h and Primary = 1h, your bot analyzes 15m, 1h, and 4h for better market insight.
                </p>
              </div>
              
              <p className="mt-3 text-sm text-orange-400 flex items-start">
                <svg className="w-4 h-4 mr-1.5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
                <span>
                  <strong>Limit:</strong> You can select up to 2 additional timeframes for reference analysis. Cannot select the same as Primary Timeframe.
                </span>
              </p>
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
              
              {/* Free Plan Warning */}
              {!isPro && (
                <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4 mb-6">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <svg className="h-5 w-5 text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h4 className="text-sm font-semibold text-orange-400 mb-1">Free Plan - Limited AI Performance</h4>
                      <p className="text-xs text-orange-300/80 leading-relaxed">
                        Your entity uses <strong>Gemini 2.0 Flash (Free)</strong> - a basic AI model with slower response times and lower analysis accuracy. 
                        To unlock faster speeds, advanced models (GPT-4o, Claude 3.7 Sonnet), and higher accuracy, upgrade to Pro Plan.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Pro Plan - LLM Provider Selection */}
              {isPro && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <div>
                    <label className="form-label">LLM Provider</label>
                    <select 
                      {...register('llm_provider')} 
                      className="form-input"
                    >
                      <option value="">None</option>
                      <option value="openai">OpenAI GPT</option>
                      <option value="anthropic">Claude</option>
                      <option value="gemini">Google Gemini</option>
                    </select>
                    <p className="text-xs text-gray-400 mt-1">
                      Platform-managed LLM providers
                    </p>
                  </div>
                  
                  <div>
                    <label className="form-label">Specific Model (Optional)</label>
                    <select 
                      {...register('llm_model')} 
                      className="form-input"
                      disabled={!watch('llm_provider')}
                    >
                      <option value="">Default (Auto-select)</option>
                      
                      {/* OpenAI Models */}
                      {watch('llm_provider') === 'openai' && (
                        <>
                          <option value="gpt-4o">GPT-4o (Best, Multimodal) ⭐</option>
                          <option value="gpt-4o-mini">GPT-4o Mini (Fast, Cheap) 💰</option>
                          <option value="o1">O1 (Advanced Reasoning) 🧠</option>
                          <option value="o1-mini">O1 Mini (Fast Reasoning) ⚡</option>
                          <option value="o1-preview">O1 Preview (Beta)</option>
                          <option value="gpt-4-turbo">GPT-4 Turbo</option>
                          <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Budget)</option>
                        </>
                      )}
                      
                      {/* Claude Models */}
                      {(watch('llm_provider') === 'anthropic' || watch('llm_provider') === 'claude') && (
                        <>
                          <option value="claude-3-7-sonnet-latest">Claude 3.7 Sonnet (Newest) ⭐</option>
                          <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet Oct 2024</option>
                          <option value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet Jun 2024</option>
                          <option value="claude-3-5-haiku-20241022">Claude 3.5 Haiku (Fast) ⚡</option>
                          <option value="claude-3-opus-20240229">Claude 3 Opus (Most Capable)</option>
                          <option value="claude-3-haiku-20240307">Claude 3 Haiku (Cheapest) 💰</option>
                        </>
                      )}
                      
                      {/* Gemini Models */}
                      {watch('llm_provider') === 'gemini' && (
                        <>
                          <option value="gemini-2.5-pro">Gemini 2.5 Pro (Best Reasoning) 🧠</option>
                          <option value="gemini-2.5-flash">Gemini 2.5 Flash (Balanced) ⭐</option>
                          <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash Lite (Fastest) ⚡</option>
                          <option value="gemini-2.0-flash-001">Gemini 2.0 Flash (Realtime/Vision) 👁️</option>
                          <option value="gemini-1.5-flash-002">Gemini 1.5 Flash (Legacy)</option>
                        </>
                      )}
                    </select>
                    {watch('llm_provider') && (
                      <p className="text-xs text-gray-400 mt-1">
                        {watch('llm_provider') === 'openai' && 'OpenAI models for different use cases'}
                        {(watch('llm_provider') === 'anthropic' || watch('llm_provider') === 'claude') && 'Claude models optimized for reasoning'}
                        {watch('llm_provider') === 'gemini' && 'Google\'s Gemini models with long context'}
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Free Plan - Show auto-selected provider */}
              {!isPro && (
                <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4 mb-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <label className="form-label mb-1">LLM Provider (Auto-selected)</label>
                      <p className="text-sm text-gray-300">💎 Google Gemini 2.0 Flash (Free)</p>
                      <p className="text-xs text-gray-500 mt-1">Platform automatically selects free AI model for Free Plan users</p>
                    </div>
                    <div className="flex-shrink-0">
                      <span className="px-3 py-1 bg-orange-500/20 text-orange-400 text-xs font-semibold rounded-full border border-orange-500/30">
                        FREE TIER
                      </span>
                    </div>
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
            
            {/* Re-publish Button - Feature Flag Controlled */}
            {canRePublishToMarketplace && (
              <button
                type="button"
                onClick={handleRepublishBot}
                disabled={isRepublishing}
                className={`btn px-6 py-3 disabled:opacity-50 transition-all duration-300 ${
                  justUpdated 
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white animate-pulse shadow-lg shadow-green-500/25' 
                    : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white'
                }`}
              >
                {isRepublishing ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Publishing...
                  </>
                ) : (
                  <>
                    <LinkIcon className="h-4 w-4 mr-2" />
                    {justUpdated ? '✨ Ready to Re-publish!' : '🚀 Re-publish to Marketplace'}
                  </>
                )}
              </button>
            )}
            
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
