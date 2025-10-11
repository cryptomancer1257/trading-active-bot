'use client'

import { useState, useEffect } from 'react'
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
  DocumentTextIcon,
  LinkIcon
} from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import toast from 'react-hot-toast'
import { useCreateBot } from '@/hooks/useBots'
import { useDefaultCredentials, useCredentials } from '@/hooks/useCredentials'

// Bot creation schema
const botSchema = z.object({
  name: z.string().min(1, 'Entity name is required'),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  bot_type: z.enum(['TECHNICAL', 'ML', 'DL', 'LLM', 'FUTURES', 'FUTURES_RPA', 'SPOT']),
  // bot_mode is auto-set based on template type
  exchange_type: z.enum(['BINANCE', 'KRAKEN', 'BYBIT', 'HUOBI', 'MULTI', 'OKX', 'BITGET']),
  trading_pairs: z.array(z.string()).min(1, 'At least one trading pair is required').default(['BTC/USDT']),
  timeframe: z.string().default('1h'),
  timeframes: z.array(z.string()).default(['1h']),
  version: z.string().default('1.0.0'),
  template: z.enum(['universal_futures_bot', 'universal_spot_bot', 'binance_futures_bot', 'binance_futures_rpa_bot', 'binance_signals_bot', 'custom']),
  // Pricing
  price_per_month: z.number().min(0, 'Price must be 0 or higher').default(0),
  is_free: z.boolean().default(false),
  // Image upload
  image_url: z.string().url().optional().or(z.literal('')),
  // Advanced configuration
  leverage: z.number().min(1).max(125).default(10),
  risk_percentage: z.number().min(0.1).max(10).default(2),
  stop_loss_percentage: z.number().min(0.1).max(20).default(5),
  take_profit_percentage: z.number().min(0.5).max(50).default(10),
  // LLM Configuration
  llm_provider: z.enum(['openai', 'anthropic', 'gemini']).optional(),
  llm_model: z.string().optional(),
  enable_image_analysis: z.boolean().default(false),
  enable_sentiment_analysis: z.boolean().default(false),
})

type BotFormData = z.infer<typeof botSchema>

const botTemplates = [
  {
    id: 'universal_futures_bot',
    name: '🌐 Universal Futures Entity',
    description: 'Multi-exchange futures trading across 6 major platforms (Binance, Bybit, OKX, Bitget, Huobi, Kraken) with unified LLM AI analysis',
    type: 'FUTURES',
    exchange: 'MULTI',
    features: ['6 Exchanges Support', 'Multi-Exchange Portfolio', 'LLM Integration', 'Unified Interface', 'Capital Management', 'Stop Loss/Take Profit'],
    gradient: 'from-blue-500 via-purple-500 to-pink-500',
    complexity: 'Advanced',
    templateFile: 'universal_futures_bot.py',
    highlighted: true,
    new: true
  },
  {
    id: 'universal_spot_bot',
    name: '🌟 Universal Spot Entity',
    description: 'Multi-exchange spot trading across 6 major platforms (Binance, Bybit, OKX, Bitget, Huobi, Kraken) with OCO orders and no leverage',
    type: 'SPOT',
    exchange: 'MULTI',
    features: ['6 Exchanges Support', 'No Leverage (1x)', 'OCO Orders (SL/TP)', 'LLM Integration', 'Safer than Futures', 'Multi-Timeframe Analysis'],
    gradient: 'from-emerald-500 via-teal-500 to-cyan-500',
    complexity: 'Intermediate',
    templateFile: 'universal_spot_bot.py',
    highlighted: true,
    new: true
  },
  {
    id: 'binance_futures_bot',
    name: '🚀 Futures Quantum Entity',
    description: 'Advanced futures trading with LLM AI analysis, leverage, and quantum risk management',
    type: 'FUTURES',
    exchange: 'BINANCE',
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
    exchange: 'BINANCE',
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
    exchange: 'BINANCE',
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
    exchange: 'BINANCE',
    features: ['Signal Generation', 'Market Analysis', 'No API Keys', 'Pure Intelligence'],
    gradient: 'from-neural-500 to-green-600',
    complexity: 'Intermediate',
    templateFile: 'binance_signals_bot.py'
  },
  {
    id: 'kraken_futures_bot',
    name: '🐙 Kraken Futures Entity',
    description: 'Derivatives trading on Kraken with risk management and leverage control',
    type: 'FUTURES',
    exchange: 'KRAKEN',
    features: ['Derivatives', 'Risk Control', 'EUR/USD Pairs', 'Regulated Exchange'],
    gradient: 'from-purple-500 to-pink-600',
    complexity: 'Advanced',
    templateFile: 'kraken_futures_bot.py'
  },
  {
    id: 'bybit_perpetual_bot',
    name: '⚡ Bybit Perpetual Entity',
    description: 'High-leverage perpetual contracts with advanced risk management',
    type: 'FUTURES',
    exchange: 'BYBIT',
    features: ['Perpetual Contracts', 'High Leverage', 'Fast Execution', 'Crypto-Native'],
    gradient: 'from-orange-500 to-red-600',
    complexity: 'Expert',
    templateFile: 'bybit_perpetual_bot.py'
  },
  {
    id: 'custom',
    name: '⚡ Custom Neural Entity',
    description: 'Build your own AI entity from scratch with custom neural architecture',
    type: 'TECHNICAL',
    exchange: 'BINANCE',
    features: ['Custom Logic', 'Full Control', 'Advanced Config', 'Neural Framework'],
    gradient: 'from-yellow-500 to-orange-600',
    complexity: 'Expert',
    templateFile: null // No template file for custom
  }
]

const exchangeTypes = [
  { value: 'MULTI', label: '🌐 Multi-Exchange', description: 'Trade across 6 major exchanges with unified interface' },
  { value: 'BINANCE', label: '🟡 Binance', description: 'World\'s largest crypto exchange' },
  { value: 'BYBIT', label: '🟠 Bybit', description: 'Advanced derivatives platform' },
  { value: 'OKX', label: '⚫ OKX', description: 'Unified trading account' },
  { value: 'BITGET', label: '🟢 Bitget', description: 'Copy trading leader' },
  { value: 'KRAKEN', label: '🟣 Kraken', description: 'European regulated exchange' },
  { value: 'HUOBI', label: '🔴 Huobi/HTX', description: 'Global digital asset exchange' }
]

const timeframeOptions = [
  '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
]

// Top 20 trading pairs from CoinMarketCap (against USDT)
const topTradingPairs = [
  { symbol: 'BTC/USDT', name: 'Bitcoin', rank: 1 },
  { symbol: 'ETH/USDT', name: 'Ethereum', rank: 2 },
  { symbol: 'BNB/USDT', name: 'BNB', rank: 3 },
  { symbol: 'SOL/USDT', name: 'Solana', rank: 4 },
  { symbol: 'XRP/USDT', name: 'Ripple', rank: 5 },
  { symbol: 'DOGE/USDT', name: 'Dogecoin', rank: 6 },
  { symbol: 'ADA/USDT', name: 'Cardano', rank: 7 },
  { symbol: 'TRX/USDT', name: 'TRON', rank: 8 },
  { symbol: 'AVAX/USDT', name: 'Avalanche', rank: 9 },
  { symbol: 'SHIB/USDT', name: 'Shiba Inu', rank: 10 },
  { symbol: 'DOT/USDT', name: 'Polkadot', rank: 11 },
  { symbol: 'LINK/USDT', name: 'Chainlink', rank: 12 },
  { symbol: 'MATIC/USDT', name: 'Polygon', rank: 13 },
  { symbol: 'BCH/USDT', name: 'Bitcoin Cash', rank: 14 },
  { symbol: 'LTC/USDT', name: 'Litecoin', rank: 15 },
  { symbol: 'UNI/USDT', name: 'Uniswap', rank: 16 },
  { symbol: 'ATOM/USDT', name: 'Cosmos', rank: 17 },
  { symbol: 'ETC/USDT', name: 'Ethereum Classic', rank: 18 },
  { symbol: 'XLM/USDT', name: 'Stellar', rank: 19 },
  { symbol: 'FIL/USDT', name: 'Filecoin', rank: 20 }
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
  
  // Bot creation flow state
  const [createdBotId, setCreatedBotId] = useState<number | null>(null)
  const [exchangeApiKey, setExchangeApiKey] = useState('')
  const [exchangeSecret, setExchangeSecret] = useState('')
  const [useTestnet, setUseTestnet] = useState(true)
  const [balanceData, setBalanceData] = useState<any>(null)
  const [isTestingExchange, setIsTestingExchange] = useState(false)
  const [testOrderId, setTestOrderId] = useState<string | number | null>(null)
  const [isTestingOrder, setIsTestingOrder] = useState(false)
  const [isCancellingOrder, setIsCancellingOrder] = useState(false)
  const [isClosingPosition, setIsClosingPosition] = useState(false)
  
  // Credentials management
  const [selectedCredentialsId, setSelectedCredentialsId] = useState<number | null>(null)
  const [showCredentialsModal, setShowCredentialsModal] = useState(false)

  // Image upload state
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string>('')
  const [isUploadingImage, setIsUploadingImage] = useState(false)

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
      trading_pairs: ['BTC/USDT'],
      timeframe: '1h',
      timeframes: ['1h'],
      version: '1.0.0',
      price_per_month: 0,
      is_free: false,
      image_url: '',
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
  
  // Get credentials for auto-selection
  const currentTemplate = botTemplates.find(t => t.id === watchedTemplate)
  const exchangeType = watch('exchange_type')
  const credentialType = currentTemplate?.type === 'FUTURES' || currentTemplate?.type === 'FUTURES_RPA' ? 'FUTURES' : 'SPOT'
  const networkType = useTestnet ? 'TESTNET' : 'MAINNET'
  
  const { data: allCredentials } = useCredentials()
  const { data: defaultCredentials } = useDefaultCredentials(
    exchangeType,
    credentialType, 
    networkType,
    !!exchangeType && !!credentialType && !!networkType
  )

  // Auto-populate credentials when default is found or network changes
  useEffect(() => {
    console.log('🔄 Credentials useEffect triggered:', { 
      step, 
      defaultCredentials: defaultCredentials ? defaultCredentials.name : 'NONE',
      exchangeType, 
      credentialType, 
      networkType,
      hasDefault: !!defaultCredentials
    })
    
    if (defaultCredentials && step === 4) {
      console.log('🔐 Auto-selecting default credentials:', defaultCredentials.name)
      console.log('🔑 Setting API key:', defaultCredentials.api_key ? `${defaultCredentials.api_key.substring(0, 8)}...` : 'EMPTY')
      console.log('🔒 Setting API secret:', defaultCredentials.api_secret ? `${defaultCredentials.api_secret.substring(0, 8)}...` : 'EMPTY')
      
      setExchangeApiKey(defaultCredentials.api_key)
      setExchangeSecret(defaultCredentials.api_secret)
      setSelectedCredentialsId(defaultCredentials.id)
      
      toast.success(`✅ Auto-loaded: ${defaultCredentials.name}`)
    } else if (step === 4 && !defaultCredentials) {
      // Clear credentials if no default found for current network
      console.log('🔍 No default credentials found for:', { exchangeType, credentialType, networkType })
      console.log('🧹 Clearing existing credentials')
      setExchangeApiKey('')
      setExchangeSecret('')
      setSelectedCredentialsId(null)
      setBalanceData(null)
    }
  }, [defaultCredentials, step, exchangeType, credentialType, networkType])

  // Handle image file selection
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

  // Upload image to server
  const uploadImage = async (file: File): Promise<string> => {
    const formData = new FormData()
    formData.append('image', file)
    
    const response = await fetch('/api/upload/image', {
      method: 'POST',
      body: formData,
    })
    
    if (!response.ok) {
      throw new Error('Failed to upload image')
    }
    
    const data = await response.json()
    return data.url
  }

  // Clear balance data when network changes (but keep credentials loading)
  useEffect(() => {
    if (step === 4) {
      setBalanceData(null)
    }
  }, [useTestnet, step])

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
    setValue('exchange_type', template.exchange as any) // Auto-set exchange based on template
    setValue('name', template.name)
    setValue('description', template.description)
    console.log('🎯 Template selected:', template.name, 'Exchange:', template.exchange)
    setStep(2)
  }

  const onSubmit = async (data: BotFormData) => {
    if (step === 3) {
      // Step 3: Create bot and move to Binance testing
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
        
        // Handle image upload if selected
        let imageUrl = data.image_url || ''
        if (selectedImage) {
          setIsUploadingImage(true)
          try {
            imageUrl = await uploadImage(selectedImage)
            toast.success('🖼️ Bot avatar uploaded successfully!')
          } catch (error) {
            toast.error('Failed to upload image. Bot will be created without avatar.')
            console.error('Image upload error:', error)
          } finally {
            setIsUploadingImage(false)
          }
        }
        
        // Call the actual API
        const createdBot = await createBotMutation.mutateAsync({
          name: data.name,
          description: data.description,
          bot_type: templateType, // Use template type
          bot_mode: autoBotMode, // Auto-set based on template type
          exchange_type: data.exchange_type,
          trading_pairs: data.trading_pairs, // Multiple trading pairs
          timeframe: data.timeframe,
          timeframes: data.timeframes,
          version: data.version,
          template: data.template,
          templateFile: selectedTemplateInfo?.templateFile || undefined, // Add template file
          // Pricing
          price_per_month: data.price_per_month,
          is_free: data.is_free,
          // Image
          image_url: imageUrl,
          // Advanced config
          leverage: data.leverage,
          risk_percentage: data.risk_percentage,
          stop_loss_percentage: data.stop_loss_percentage,
          take_profit_percentage: data.take_profit_percentage,
          llm_provider: data.llm_provider,
          llm_model: data.llm_model,
          enable_image_analysis: data.enable_image_analysis,
          enable_sentiment_analysis: data.enable_sentiment_analysis,
        })
        
        // Save bot ID and move to appropriate step
        setCreatedBotId(createdBot.id)
        
        // Skip Step 4 for PASSIVE bots (they don't need exchange integration)
        if (autoBotMode === 'PASSIVE') {
          toast.success('⚡ Neural Entity successfully forged! Ready for marketplace publishing...')
          setStep(5) // Skip to Step 5 (Publish)
        } else {
          toast.success('⚡ Neural Entity successfully forged! Ready for exchange integration testing...')
          setStep(4) // Go to Step 4 (Exchange Testing)
        }
      
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
    } else if (step === 5) {
      // Step 5: Publish to marketplace
      handlePublishBot()
    }
  }

  // Exchange API testing functions
  const testExchangeConnection = async () => {
    console.log('🔍 Testing connection with:', { 
      exchangeApiKey: exchangeApiKey ? `${exchangeApiKey.substring(0, 8)}...` : 'EMPTY',
      exchangeSecret: exchangeSecret ? `${exchangeSecret.substring(0, 8)}...` : 'EMPTY',
      selectedCredentialsId,
      networkType,
      credentialType 
    })
    
    if (!exchangeApiKey || !exchangeSecret) {
      console.error('❌ Missing credentials:', { exchangeApiKey: !!exchangeApiKey, exchangeSecret: !!exchangeSecret })
      toast.error('Please enter both API Key and Secret')
      return
    }

    const exchangeType = watch('exchange_type')
    const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
    const botType = selectedTemplate?.type || 'SPOT' // Get bot type from template
    
    setIsTestingExchange(true)
    
    try {
      console.log(`🔗 Testing ${exchangeType} connection...`, { botType, template: selectedTemplate?.name })
      
      // Route to appropriate exchange API endpoint
      const apiEndpoint = `/api/${exchangeType.toLowerCase()}/balance`
      
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey: exchangeApiKey,
          secret: exchangeSecret,
          testnet: useTestnet,
          exchange: exchangeType,
          botType: botType // Use template type for API routing
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        
        // Handle API key permission errors with detailed instructions
        if (errorData.code === '-2015' && errorData.instructions) {
          console.error(`❌ ${exchangeType} API Key Permission Error:`)
          errorData.instructions.forEach((instruction: string, index: number) => {
            console.error(`${index + 1}. ${instruction}`)
          })
          
          toast.error(`❌ API Key Permission Error - Check Console for Instructions`, {
            duration: 8000
          })
          
          // Show detailed error in UI (you can enhance this further)
          alert(`API Key Permission Error:\n\n${errorData.instructions.join('\n')}`)
          return
        }
        
        throw new Error(errorData.error || `Failed to connect to ${exchangeType}`)
      }

      const data = await response.json()
      setBalanceData(data)
      
      if (data.demoMode) {
        toast.success(`🔗 ${exchangeType} connection successful! (Demo Mode)`)
        console.log(`✅ ${exchangeType} API connection successful (Demo Mode):`, data)
      } else if (data.needsRealApiKey) {
        toast.error(`⚠️ Using demo data - Please fix API key permissions for real data`)
        console.log(`⚠️ ${exchangeType} API connection using demo data:`, data)
      } else {
        toast.success(`🔗 ${exchangeType} connection successful! (Real Data)`)
        console.log(`✅ ${exchangeType} API connection successful (Real Data):`, data)
      }
      
    } catch (error: any) {
      console.error(`❌ ${exchangeType} connection failed:`, error)
      toast.error(`❌ ${exchangeType} connection failed: ${error.message}`)
    } finally {
      setIsTestingExchange(false)
    }
  }

  // Test Order function
  const testOrder = async () => {
    if (!exchangeApiKey || !exchangeSecret) {
      toast.error('Please enter both API Key and Secret')
      return
    }

    const exchangeType = watch('exchange_type')
    const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
    const botType = selectedTemplate?.type || 'SPOT' // Get bot type from template
    
    setIsTestingOrder(true)
    
    try {
      console.log(`📊 Creating test order on ${exchangeType}...`, { botType, template: selectedTemplate?.name })
      
      // First, get current market price
      console.log('💰 Getting current market price...')
      const priceResponse = await fetch(`/api/${exchangeType.toLowerCase()}/price`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: 'BTCUSDT',
          testnet: useTestnet,
          botType: botType
        })
      })
      
      if (!priceResponse.ok) {
        throw new Error('Failed to get current price')
      }
      
      const priceData = await priceResponse.json()
      const currentPrice = parseFloat(priceData.price)
      const orderPrice = Math.round(currentPrice * 1.01) // 1% above market for quick fill
      
      console.log(`💰 Current price: $${currentPrice}, Order price: $${orderPrice}`)
      
      const response = await fetch(`/api/${exchangeType.toLowerCase()}/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey: exchangeApiKey,
          secret: exchangeSecret,
          testnet: useTestnet,
          exchange: exchangeType,
          botType: botType, // Use template type for API routing
          action: 'CREATE',
          symbol: 'BTCUSDT',
          side: 'BUY',
          type: 'LIMIT',
          quantity: '0.003',  // 0.003 * current price = well above $100 minimum
          price: orderPrice.toString()    // Dynamic market price + 1%
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to create test order on ${exchangeType}`)
      }

      const data = await response.json()
      setTestOrderId(data.orderId || data.clientOrderId)
      
      toast.success(`📊 Test order created successfully on ${exchangeType}!`)
      console.log(`✅ ${exchangeType} test order created:`, data)
      
    } catch (error: any) {
      console.error(`❌ ${exchangeType} test order failed:`, error)
      toast.error(`❌ Test order failed: ${error.message}`)
    } finally {
      setIsTestingOrder(false)
    }
  }

  // Cancel Order function
  const cancelOrder = async () => {
    if (!exchangeApiKey || !exchangeSecret || !testOrderId) {
      toast.error('No active test order to cancel')
      return
    }

    const exchangeType = watch('exchange_type')
    const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
    const botType = selectedTemplate?.type || 'SPOT' // Get bot type from template
    
    setIsCancellingOrder(true)
    
    try {
      console.log(`❌ Cancelling order ${testOrderId} on ${exchangeType}...`, { botType })
      
      const response = await fetch(`/api/${exchangeType.toLowerCase()}/order`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey: exchangeApiKey,
          secret: exchangeSecret,
          testnet: useTestnet,
          exchange: exchangeType,
          botType: botType, // Use template type for API routing
          action: 'CANCEL',
          symbol: 'BTCUSDT',
          orderId: testOrderId
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to cancel order on ${exchangeType}`)
      }

      const data = await response.json()
      setTestOrderId(null)
      
      toast.success(`❌ Order cancelled successfully on ${exchangeType}!`)
      console.log(`✅ ${exchangeType} order cancelled:`, data)
      
    } catch (error: any) {
      console.error(`❌ ${exchangeType} cancel order failed:`, error)
      toast.error(`❌ Cancel order failed: ${error.message}`)
    } finally {
      setIsCancellingOrder(false)
    }
  }

  // Close Position function
  const closePosition = async () => {
    if (!exchangeApiKey || !exchangeSecret) {
      toast.error('Please enter both API Key and Secret')
      return
    }

    const exchangeType = watch('exchange_type')
    const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
    const botType = selectedTemplate?.type || 'SPOT' // Get bot type from template
    
    setIsClosingPosition(true)
    
    try {
      console.log(`🔒 Closing position on ${exchangeType}...`, { botType })
      
      const response = await fetch(`/api/${exchangeType.toLowerCase()}/position`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          apiKey: exchangeApiKey,
          secret: exchangeSecret,
          testnet: useTestnet,
          exchange: exchangeType,
          botType: botType, // Use template type for API routing
          action: 'CLOSE',
          symbol: 'BTCUSDT'
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Failed to close position on ${exchangeType}`)
      }

      const data = await response.json()
      
      toast.success(`🔒 Position closed successfully on ${exchangeType}!`)
      console.log(`✅ ${exchangeType} position closed:`, data)
      
    } catch (error: any) {
      console.error(`❌ ${exchangeType} close position failed:`, error)
      toast.error(`❌ Close position failed: ${error.message}`)
    } finally {
      setIsClosingPosition(false)
    }
  }

  const handlePublishBot = async () => {
    if (!createdBotId) return

    setIsSubmitting(true)
    try {
      const token = localStorage.getItem('access_token')
      const response = await fetch(`http://localhost:8000/marketplace/publish-token?bot_id=${createdBotId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) throw new Error('Failed to publish bot')

      const data = await response.json()
      console.log('📡 Publish response:', data)

      toast.success('🚀 Bot successfully published! Redirecting to marketplace...')
      
      // Redirect to marketplace publish URL
      setTimeout(() => {
        if (data.publish_url) {
          window.open(data.publish_url, '_blank')
          // Also redirect back to entities page
          router.push('/creator/entities')
        } else {
          router.push('/creator/entities')
        }
      }, 1500)

    } catch (error: any) {
      toast.error(`❌ Publish failed: ${error.message}`)
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
          <div className="flex items-center space-x-2">
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs ${
              step >= 1 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
            }`}>
              1
            </div>
            <div className={`w-12 h-1 ${step >= 2 ? 'bg-quantum-500' : 'bg-gray-600'}`}></div>
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs ${
              step >= 2 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
            }`}>
              2
            </div>
            <div className={`w-12 h-1 ${step >= 3 ? 'bg-quantum-500' : 'bg-gray-600'}`}></div>
            <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs ${
              step >= 3 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
            }`}>
              3
            </div>
            
            {/* Show Step 4 & 5 only for ACTIVE bots */}
            {(() => {
              const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
              const templateType = selectedTemplate?.type || 'TECHNICAL'
              const activeBotTypes = ['FUTURES', 'FUTURES_RPA', 'SPOT']
              const isActiveBotMode = activeBotTypes.includes(templateType)
              
              return isActiveBotMode ? (
                <>
                  <div className={`w-12 h-1 ${step >= 4 ? 'bg-quantum-500' : 'bg-gray-600'}`}></div>
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs ${
                    step >= 4 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
                  }`}>
                    4
                  </div>
                  <div className={`w-12 h-1 ${step >= 5 ? 'bg-quantum-500' : 'bg-gray-600'}`}></div>
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs ${
                    step >= 5 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
                  }`}>
                    5
                  </div>
                </>
              ) : (
                <>
                  <div className={`w-12 h-1 ${step >= 5 ? 'bg-quantum-500' : 'bg-gray-600'}`}></div>
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 text-xs ${
                    step >= 5 ? 'bg-quantum-500 border-quantum-500 text-white' : 'border-gray-600 text-gray-400'
                  }`}>
                    4
                  </div>
                </>
              )
            })()}
          </div>
        </div>
        
        <div className="flex justify-center mt-4 text-xs text-gray-400 max-w-4xl mx-auto">
          <span className={step === 1 ? 'text-quantum-400 font-medium' : ''}>Template</span>
          <span className="mx-2">→</span>
          <span className={step === 2 ? 'text-quantum-400 font-medium' : ''}>Config</span>
          <span className="mx-2">→</span>
          <span className={step === 3 ? 'text-quantum-400 font-medium' : ''}>Neural</span>
          
          {/* Show Step 4 only for ACTIVE bots */}
          {(() => {
            const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
            const templateType = selectedTemplate?.type || 'TECHNICAL'
            const activeBotTypes = ['FUTURES', 'FUTURES_RPA', 'SPOT']
            const isActiveBotMode = activeBotTypes.includes(templateType)
            
            return isActiveBotMode ? (
              <>
                <span className="mx-2">→</span>
                <span className={step === 4 ? 'text-quantum-400 font-medium' : ''}>{watch('exchange_type')} Test</span>
                <span className="mx-2">→</span>
                <span className={step === 5 ? 'text-quantum-400 font-medium' : ''}>Publish</span>
              </>
            ) : (
              <>
                <span className="mx-2">→</span>
                <span className={step === 5 ? 'text-quantum-400 font-medium' : ''}>Publish</span>
              </>
            )
          })()}
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
                  className={`card-quantum p-6 cursor-pointer hover:shadow-2xl hover:shadow-quantum-500/20 transition-all duration-300 transform hover:-translate-y-2 animate-fade-in ${
                    template.highlighted ? 'ring-2 ring-gradient-to-r ring-blue-500/50 ring-offset-2 ring-offset-dark-900' : ''
                  } ${template.new ? 'relative' : ''}`}
                  style={{ animationDelay: `${index * 0.1}s` }}
                >
                  {template.new && (
                    <div className="absolute -top-2 -right-2 px-3 py-1 bg-gradient-to-r from-blue-500 to-purple-500 text-white text-xs font-bold rounded-full shadow-lg animate-pulse">
                      NEW
                    </div>
                  )}
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

                  {/* Bot Avatar Upload */}
                  <div>
                    <label className="form-label">Entity Avatar (Optional)</label>
                    <div className="space-y-3">
                      {/* Image Preview */}
                      {(imagePreview || watch('image_url')) && (
                        <div className="flex items-center space-x-3">
                          <img
                            src={imagePreview || watch('image_url')}
                            alt="Bot avatar preview"
                            className="w-16 h-16 rounded-lg object-cover border-2 border-quantum-500/30"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              setImagePreview('')
                              setSelectedImage(null)
                              setValue('image_url', '')
                            }}
                            className="text-danger-400 hover:text-danger-300 text-sm"
                          >
                            Remove
                          </button>
                        </div>
                      )}
                      
                      {/* File Input */}
                      <div className="relative">
                        <input
                          type="file"
                          accept="image/*"
                          onChange={handleImageSelect}
                          className="hidden"
                          id="avatar-upload"
                        />
                        <label
                          htmlFor="avatar-upload"
                          className="flex items-center justify-center w-full px-4 py-3 border-2 border-dashed border-quantum-500/30 rounded-lg cursor-pointer hover:border-quantum-400/50 transition-colors"
                        >
                          <CloudArrowUpIcon className="h-5 w-5 mr-2 text-quantum-400" />
                          <span className="text-sm text-gray-300">
                            {selectedImage ? selectedImage.name : 'Upload avatar image (Max 5MB)'}
                          </span>
                        </label>
                      </div>
                      
                      {/* Or URL Input */}
                      <div className="text-center text-sm text-gray-500">or</div>
                      <input
                        {...register('image_url')}
                        className="form-input"
                        placeholder="Or paste image URL..."
                        onChange={(e) => {
                          if (e.target.value) {
                            setImagePreview('')
                            setSelectedImage(null)
                          }
                        }}
                      />
                    </div>
                  </div>
                  
                  {/* Entity Mode is auto-set based on template type */}
                </div>
              </div>

              {/* Exchange Configuration & Pricing */}
              <div className="space-y-6">
                {/* Exchange Settings */}
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
                    
                    {/* Trading Pairs */}
                    <div>
                      <label className="form-label">Trading Pairs</label>
                      <p className="mt-1 text-sm text-gray-400 mb-3">
                        📊 Select from top 20 CoinMarketCap coins. Users will choose from your selection when subscribing.
                      </p>
                      
                      {/* Quick Add Top Coins */}
                      <div className="mb-3">
                        <button
                          type="button"
                          onClick={() => {
                            const top5 = topTradingPairs.slice(0, 5).map(p => p.symbol)
                            const currentPairs = watch('trading_pairs') || []
                            // Deduplicate using Set
                            const uniquePairs = Array.from(new Set([...currentPairs, ...top5]))
                            setValue('trading_pairs', uniquePairs)
                          }}
                          className="w-full px-4 py-2 bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-500/50 text-blue-400 rounded-md hover:from-blue-500/30 hover:to-purple-500/30 transition-all text-sm font-medium"
                        >
                          ⚡ Quick Add Top 5 Coins (BTC, ETH, BNB, SOL, XRP)
                        </button>
                      </div>
                      
                      {/* Add New Pair Dropdown */}
                      <div className="flex gap-2 mb-3">
                        <select
                          className="form-input flex-1"
                          onChange={(e) => {
                            const value = e.target.value
                            if (value && !watch('trading_pairs')?.includes(value)) {
                              setValue('trading_pairs', [...(watch('trading_pairs') || []), value])
                              e.target.value = '' // Reset select
                            }
                          }}
                          defaultValue=""
                        >
                          <option value="" disabled>Select a trading pair...</option>
                          {topTradingPairs
                            .filter(pair => !watch('trading_pairs')?.includes(pair.symbol))
                            .map((pair) => (
                              <option key={pair.symbol} value={pair.symbol}>
                                #{pair.rank} {pair.symbol} - {pair.name}
                              </option>
                            ))}
                        </select>
                        <button
                          type="button"
                          onClick={() => {
                            const select = document.querySelector('select[class*="form-input"]') as HTMLSelectElement
                            if (select && select.value && !watch('trading_pairs')?.includes(select.value)) {
                              setValue('trading_pairs', [...(watch('trading_pairs') || []), select.value])
                              select.value = ''
                            }
                          }}
                          className="px-4 py-2 bg-quantum-500/20 border border-quantum-500 text-quantum-400 rounded-md hover:bg-quantum-500/30 transition-colors text-sm font-medium whitespace-nowrap"
                        >
                          ➕ Add
                        </button>
                      </div>
                      
                      {/* List of Trading Pairs */}
                      {watch('trading_pairs') && watch('trading_pairs').length > 0 && (
                        <div className="space-y-2">
                          {watch('trading_pairs').map((pair, index) => {
                            const pairInfo = topTradingPairs.find(p => p.symbol === pair)
                            return (
                              <div
                                key={index}
                                className="flex items-center gap-3 bg-dark-700/50 border border-gray-600 rounded-md p-3"
                              >
                                {/* Rank Badge */}
                                {pairInfo && (
                                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-quantum-500/20 text-quantum-400 text-xs font-bold">
                                    #{pairInfo.rank}
                                  </div>
                                )}
                                
                                {/* Pair Info */}
                                <div className="flex-1">
                                  <div className="text-white font-bold">{pair}</div>
                                  {pairInfo && (
                                    <div className="text-xs text-gray-400">{pairInfo.name}</div>
                                  )}
                                </div>
                                
                                {/* Remove Button */}
                                <button
                                  type="button"
                                  onClick={() => {
                                    const pairs = watch('trading_pairs').filter((_, i) => i !== index)
                                    setValue('trading_pairs', pairs.length > 0 ? pairs : ['BTC/USDT'])
                                  }}
                                  disabled={watch('trading_pairs').length === 1}
                                  className={`p-1 rounded ${
                                    watch('trading_pairs').length === 1
                                      ? 'text-gray-600 cursor-not-allowed'
                                      : 'text-red-400 hover:text-red-300 hover:bg-red-500/10'
                                  }`}
                                  title={watch('trading_pairs').length === 1 ? 'At least one pair required' : 'Remove'}
                                >
                                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                </button>
                              </div>
                            )
                          })}
                          
                          {/* Summary */}
                          <div className="mt-2 text-sm text-gray-500 bg-dark-800/50 rounded p-3 border border-quantum-500/20">
                            <div className="font-medium text-quantum-400 mb-1">📋 Supported Trading Pairs: {watch('trading_pairs').length}</div>
                            <div className="text-xs text-gray-600 mt-1">
                              💡 Users will select 1 primary + optional secondary pairs from this list when subscribing
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {errors.trading_pairs && (
                        <p className="mt-1 text-sm text-red-500">{errors.trading_pairs.message}</p>
                      )}
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
                  
                  {/* Extra Timeframes */}
                  <div className="mt-6">
                    <label className="form-label">Extra Timeframes</label>
                    <p className="mt-1 text-sm text-gray-400 mb-3">
                      Reference timeframes for better decision making
                    </p>
                    <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
                      {timeframeOptions.map((tf) => {
                        const currentTimeframes = watch('timeframes') || []
                        const isSelected = currentTimeframes.includes(tf)
                        return (
                          <button
                            key={tf}
                            type="button"
                            onClick={() => {
                              const newTimeframes = isSelected
                                ? currentTimeframes.filter(t => t !== tf)
                                : [...currentTimeframes, tf]
                              setValue('timeframes', newTimeframes)
                            }}
                            className={`px-3 py-2 text-sm rounded-md border transition-colors ${
                              isSelected
                                ? 'bg-quantum-500/20 border-quantum-500 text-quantum-400'
                                : 'bg-dark-700/50 border-gray-600 text-gray-300 hover:bg-dark-600/50'
                            }`}
                          >
                            {tf}
                          </button>
                        )
                      })}
                    </div>
                    {watch('timeframes') && watch('timeframes').length > 0 && (
                      <div className="mt-2 text-sm text-gray-500">
                        <span className="font-medium">Selected:</span> {watch('timeframes').join(', ')}
                      </div>
                    )}
                  </div>
                </div>

                {/* Pricing Configuration */}
                <div className="card-neural p-6">
                  <h3 className="text-lg font-bold cyber-text mb-4 flex items-center">
                    <SparklesIcon className="h-5 w-5 mr-2" />
                    Marketplace Pricing
                  </h3>
                  
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
                            {...register('price_per_month', { valueAsNumber: true })}
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
                  {(watchedBotType === 'LLM' || watchedBotType === 'FUTURES' || watchedBotType === 'FUTURES_RPA' || watchedBotType === 'SPOT') && (
                    <>
                      <div>
                        <label className="form-label">LLM Provider</label>
                        <select {...register('llm_provider')} className="form-input">
                          <option value="">Select AI Provider</option>
                          <option value="openai">🤖 OpenAI (GPT-4)</option>
                          <option value="anthropic">🧠 Anthropic (Claude)</option>
                          <option value="gemini">💎 Google (Gemini)</option>
                        </select>
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
                          {watch('llm_provider') === 'anthropic' && (
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
                            {watch('llm_provider') === 'openai' && 'OpenAI models - balance speed & quality'}
                            {watch('llm_provider') === 'anthropic' && 'Claude models - advanced reasoning'}
                            {watch('llm_provider') === 'gemini' && 'Gemini models - long context window'}
                          </p>
                        )}
                      </div>
                    </>
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

        {/* Step 4: Exchange Integration Testing */}
        {step === 4 && (
          <div className="space-y-8">
            <div className="card-quantum p-8">
              <h2 className="text-2xl font-bold cyber-text mb-6">
                🔗 {watch('exchange_type')} Integration Testing
              </h2>
              <p className="text-gray-400 mb-6">
                Test your bot's connection to {watch('exchange_type')} exchange. Configure your API credentials and perform test operations.
                <br />
                <span className="text-neural-400 text-sm">
                  💡 Testing is optional - you can skip directly to publishing if you prefer to configure API keys later.
                </span>
              </p>

              <div className="grid md:grid-cols-2 gap-8">
                {/* API Configuration */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-quantum-400">API Configuration</h3>
                  
                  {/* Network Selection */}
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={useTestnet}
                      onChange={(e) => setUseTestnet(e.target.checked)}
                      className="mr-3"
                    />
                    <label className="text-gray-300">Use Testnet (Recommended)</label>
                  </div>

                  {/* Credentials Selection */}
                  <div>
                    <label className="form-label">
                      🔑 Saved Credentials 
                      <span className="text-sm text-gray-400 ml-2">
                        ({exchangeType} {credentialType} {networkType})
                      </span>
                    </label>
                    
                    {allCredentials && allCredentials.length > 0 ? (
                      <div className="space-y-3">
                        <select
                          value={selectedCredentialsId || ''}
                          onChange={(e) => {
                            const credId = e.target.value ? parseInt(e.target.value) : null
                            setSelectedCredentialsId(credId)
                            
                            if (credId) {
                              const cred = allCredentials.find(c => c.id === credId)
                              if (cred) {
                                setExchangeApiKey((cred as any).api_key)
                                setExchangeSecret((cred as any).api_secret)
                                toast.success(`✅ Selected: ${cred.name}`)
                              }
                            } else {
                              setExchangeApiKey('')
                              setExchangeSecret('')
                            }
                          }}
                          className="form-input"
                        >
                          <option value="">🔧 Manual Entry</option>
                          {allCredentials
                            .filter(cred => 
                              cred.exchange_type === exchangeType && 
                              cred.credential_type === credentialType &&
                              cred.network_type === networkType
                            )
                            .map((cred) => (
                              <option key={cred.id} value={cred.id}>
                                🔑 {cred.name} {cred.is_default ? '(Default)' : ''}
                              </option>
                            ))}
                        </select>
                        
                        {selectedCredentialsId && (
                          <div className="text-sm text-green-400 flex items-center">
                            ✅ Using saved credentials: {allCredentials.find(c => c.id === selectedCredentialsId)?.name}
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-sm text-yellow-400 bg-yellow-500/10 p-3 rounded border border-yellow-500/20">
                        ⚠️ No saved credentials found for {exchangeType} {credentialType} {networkType}
                        <br />
                        <a 
                          href="/creator/credentials" 
                          target="_blank"
                          className="text-quantum-400 hover:text-quantum-300 underline"
                        >
                          → Manage Credentials
                        </a>
                      </div>
                    )}
                  </div>

                  {/* Manual API Key Entry */}
                  <div>
                    <label className="form-label">{watch('exchange_type')} API Key</label>
                    <input
                      type="text"
                      value={exchangeApiKey}
                      onChange={(e) => {
                        setExchangeApiKey(e.target.value)
                        if (e.target.value && selectedCredentialsId) {
                          setSelectedCredentialsId(null) // Clear selection if manually editing
                        }
                      }}
                      className="form-input"
                      placeholder={exchangeApiKey ? "API Key loaded from credentials" : `Enter your ${watch('exchange_type')} API Key`}
                    />
                  </div>

                  <div>
                    <label className="form-label">{watch('exchange_type')} Secret</label>
                    <input
                      type="password"
                      value={exchangeSecret}
                      onChange={(e) => {
                        setExchangeSecret(e.target.value)
                        if (e.target.value && selectedCredentialsId) {
                          setSelectedCredentialsId(null) // Clear selection if manually editing
                        }
                      }}
                      className="form-input"
                      placeholder={exchangeSecret ? "Secret loaded from credentials" : "Enter your API Secret"}
                    />
                  </div>

                  <button
                    type="button"
                    onClick={testExchangeConnection}
                    disabled={isTestingExchange}
                    className="btn btn-primary w-full"
                  >
                    {isTestingExchange ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Testing {watch('exchange_type')} Connection...
                      </>
                    ) : (
                      <>
                        <LinkIcon className="h-4 w-4 mr-2" />
                        🔗 Test {watch('exchange_type')} Connection
                      </>
                    )}
                  </button>
                </div>

                {/* Balance & Actions */}
                <div className="space-y-6">
                  <h3 className="text-lg font-semibold text-quantum-400">Account Information</h3>
                  
                  {balanceData ? (
                    <div className="card-cyber p-4">
                      <h4 className="font-semibold text-neural-400 mb-3">Account Balance</h4>
                      <div className="space-y-2 text-sm">
                        {balanceData.balances?.slice(0, 5).map((balance: any, index: number) => (
                          <div key={index} className="flex justify-between">
                            <span>{balance.asset}</span>
                            <span>{parseFloat(balance.free).toFixed(6)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="card-cyber p-4 text-center text-gray-400">
                      <div className="mb-2">Connect to {watch('exchange_type')} to view account information</div>
                      <div className="text-xs text-neural-400">
                        Or skip testing and configure API keys later in production
                      </div>
                    </div>
                  )}

                  {balanceData && (
                    <div className="space-y-3">
                      <button 
                        onClick={testOrder}
                        disabled={isTestingOrder}
                        className="btn btn-secondary w-full flex items-center justify-center"
                      >
                        {isTestingOrder ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Creating Test Order...
                          </>
                        ) : (
                          '📊 Test Order (BUY 0.003 BTC @ Market Price)'
                        )}
                      </button>
                      
                      <button 
                        onClick={cancelOrder}
                        disabled={isCancellingOrder || !testOrderId}
                        className="btn btn-danger w-full flex items-center justify-center disabled:opacity-50"
                      >
                        {isCancellingOrder ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Cancelling Order...
                          </>
                        ) : (
                          `❌ Cancel Order ${testOrderId ? `(${String(testOrderId).substring(0, 8)}...)` : '(No Active Order)'}`
                        )}
                      </button>
                      
                      <button 
                        onClick={closePosition}
                        disabled={isClosingPosition}
                        className="btn btn-secondary w-full flex items-center justify-center"
                      >
                        {isClosingPosition ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Closing Position...
                          </>
                        ) : (
                          '🔒 Close Position (BTCUSDT)'
                        )}
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex justify-between mt-8">
                <button
                  type="button"
                  onClick={() => setStep(3)}
                  className="btn btn-secondary"
                >
                  ← Back to Neural Architecture
                </button>
                
                <button
                  type="button"
                  onClick={() => setStep(5)}
                  className="btn btn-cyber"
                >
                  Continue to Publish →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Publish to Marketplace */}
        {step === 5 && (
          <div className="space-y-8">
            <div className="card-quantum p-8 text-center">
              <h2 className="text-2xl font-bold cyber-text mb-6">🚀 Publish to Marketplace</h2>
              <p className="text-gray-400 mb-8">
                Your neural entity is ready for deployment! Publish it to the quantum marketplace 
                where other traders can discover and utilize your AI creation.
              </p>

              <div className="card-cyber p-6 mb-8">
                <h3 className="text-lg font-semibold text-neural-400 mb-4">Entity Summary</h3>
                <div className="text-left space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-400">Entity ID:</span>
                    <span className="text-quantum-400">#{createdBotId}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Template:</span>
                    <span>{selectedTemplate}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">
                      {(() => {
                        const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
                        const templateType = selectedTemplate?.type || 'TECHNICAL'
                        const activeBotTypes = ['FUTURES', 'FUTURES_RPA', 'SPOT']
                        const isActiveBotMode = activeBotTypes.includes(templateType)
                        
                        return isActiveBotMode ? 'Exchange Integration:' : 'Bot Mode:'
                      })()}
                    </span>
                    <span className="text-neural-400">
                      {(() => {
                        const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
                        const templateType = selectedTemplate?.type || 'TECHNICAL'
                        const activeBotTypes = ['FUTURES', 'FUTURES_RPA', 'SPOT']
                        const isActiveBotMode = activeBotTypes.includes(templateType)
                        
                        return isActiveBotMode ? '✅ Tested' : '🧠 PASSIVE (Signal Only)'
                      })()}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-400">Status:</span>
                    <span className="text-cyber-400">Ready for Deployment</span>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="btn btn-cyber px-12 py-4 text-lg font-bold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Publishing to Marketplace...
                  </>
                ) : (
                  <>
                    🚀 Publish Neural Entity
                  </>
                )}
              </button>

              <p className="text-xs text-gray-500 mt-4">
                🌐 Global marketplace • 💎 Quantum verified • 🔐 Secure deployment
              </p>

              <div className="flex justify-center mt-6">
                <button
                  type="button"
                  onClick={() => {
                    // Go back to appropriate step based on bot mode
                    const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
                    const templateType = selectedTemplate?.type || 'TECHNICAL'
                    const activeBotTypes = ['FUTURES', 'FUTURES_RPA', 'SPOT']
                    const isActiveBotMode = activeBotTypes.includes(templateType)
                    
                    if (isActiveBotMode) {
                      setStep(4) // Go back to Exchange Testing for ACTIVE bots
                    } else {
                      setStep(3) // Go back to Neural Architecture for PASSIVE bots
                    }
                  }}
                  className="btn btn-secondary"
                >
                  {(() => {
                    const selectedTemplate = botTemplates.find(t => t.id === watch('template'))
                    const templateType = selectedTemplate?.type || 'TECHNICAL'
                    const activeBotTypes = ['FUTURES', 'FUTURES_RPA', 'SPOT']
                    const isActiveBotMode = activeBotTypes.includes(templateType)
                    
                    return isActiveBotMode 
                      ? `← Back to ${watch('exchange_type')} Testing`
                      : '← Back to Neural Architecture'
                  })()}
                </button>
              </div>
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
