'use client'

import { useState, useEffect, useCallback } from 'react'
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
import { usePlan } from '@/hooks/usePlan'
import { useFeatureFlag, FEATURE_FLAGS } from '@/hooks/useFeatureFlag'
import config from '@/lib/config'
import BotPromptsTab from '@/components/BotPromptsTab'
import PreTrialValidationModal from '@/components/PreTrialValidationModal'
import UpgradeModal from '@/components/UpgradeModal'

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
  template: z.enum(['universal_futures_bot', 'universal_spot_bot', 'binance_futures_bot', 'binance_futures_rpa_bot', 'binance_signals_bot', 'universal_futures_signals_bot', 'custom']),
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
  // LLM Configuration (now managed by platform)
  llm_provider: z.string().optional(),
  llm_model: z.string().optional(),
  enable_image_analysis: z.boolean().default(false),
  enable_sentiment_analysis: z.boolean().default(false),
})
// Note: LLM Provider validation removed - platform now manages LLM providers centrally

type BotFormData = z.infer<typeof botSchema>

const botTemplates = [
  {
    id: 'universal_futures_bot',
    name: '🌐 Universal Futures Entity',
    description: 'Multi-exchange futures trading (Binance & Bybit) with unified LLM AI analysis. Choose your preferred exchange during setup.',
    type: 'FUTURES',
    exchange: 'MULTI',
    features: ['Binance & Bybit Support', 'LLM Integration', 'Unified Interface', 'Capital Management', 'Stop Loss/Take Profit', 'Multi-Timeframe'],
    gradient: 'from-blue-500 via-purple-500 to-pink-500',
    complexity: 'Advanced',
    templateFile: 'universal_futures_bot.py',
    highlighted: true,
    new: true
  },
  {
    id: 'universal_spot_bot',
    name: '🌟 Universal Spot Entity',
    description: 'Multi-exchange spot trading (Binance & Bybit) with OCO orders and no leverage. Safer than futures trading.',
    type: 'SPOT',
    exchange: 'MULTI',
    features: ['Binance & Bybit Support', 'No Leverage (1x)', 'OCO Orders (SL/TP)', 'LLM Integration', 'Safer than Futures', 'Multi-Timeframe Analysis'],
    gradient: 'from-emerald-500 via-teal-500 to-cyan-500',
    complexity: 'Intermediate',
    templateFile: 'universal_spot_bot.py',
    highlighted: true,
    new: true
  },
  {
    id: 'universal_futures_signals_bot',
    name: '📡 Universal Futures Signals Entity',
    description: 'Multi-exchange signals bot (Binance & Bybit) with LLM analysis. Telegram & Discord notifications. NO trading execution - signals only!',
    type: 'LLM',
    exchange: 'MULTI',
    features: ['Binance & Bybit Support', 'LLM Analysis', 'Multi-Timeframe', 'Telegram Signals', 'Discord Signals', 'No Trading Risk', 'Signal Intelligence'],
    gradient: 'from-purple-500 via-pink-500 to-red-500',
    complexity: 'Intermediate',
    templateFile: 'universal_futures_signals_bot.py',
    highlighted: true,
    new: true
  }
]

const exchangeTypes = [
  { value: 'BYBIT', label: '🟠 Bybit', description: 'Advanced derivatives platform' },
  { value: 'BINANCE', label: '🟡 Binance', description: 'World\'s largest crypto exchange' },
  //{ value: 'OKX', label: '⚫ OKX', description: 'Unified trading account' },
  //{ value: 'BITGET', label: '🟢 Bitget', description: 'Copy trading leader' },
  //{ value: 'KRAKEN', label: '🟣 Kraken', description: 'European regulated exchange' },
  //{ value: 'HUOBI', label: '🔴 Huobi/HTX', description: 'Global digital asset exchange' }
]

const timeframeOptions = [
  '1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M'
]

// Top 21 trading pairs from CoinMarketCap (against USDT)
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
  { symbol: 'FIL/USDT', name: 'Filecoin', rank: 20 },
  { symbol: 'ICP/USDT', name: 'Internet Computer', rank: 21 }
]

export default function ForgePage() {
  const { user, loading } = useAuthGuard({ 
    requireAuth: true,
    requiredRole: UserRole.DEVELOPER 
  })
  const router = useRouter()
  const [step, setStep] = useState(1)
  
  // Feature flags
  const canPublishToMarketplace = useFeatureFlag(FEATURE_FLAGS.MARKETPLACE_PUBLISH_BOT)
  const isPlanPackageEnabled = true // Always enable plan package checks
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
  
  // Trial & Logs state
  const [isStartingTrial, setIsStartingTrial] = useState(false)
  const [trialConfig, setTrialConfig] = useState({
    networkType: 'TESTNET',
    tradingPair: 'BTC/USDT',
    secondaryTradingPairs: [] as string[],
    subscriptionStart: '', // For Pro users
    subscriptionEnd: ''    // For Pro users
  })
  const [botLogs, setBotLogs] = useState<any[]>([])
  const [isLoadingLogs, setIsLoadingLogs] = useState(false)
  
  // Credentials management
  const [selectedCredentialsId, setSelectedCredentialsId] = useState<number | null>(null)
  const [showCredentialsModal, setShowCredentialsModal] = useState(false)

  // Image upload state
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string>('')
  const [isUploadingImage, setIsUploadingImage] = useState(false)
  
  // Name validation state
  const [nameCheckStatus, setNameCheckStatus] = useState<'idle' | 'checking' | 'available' | 'taken'>('idle')
  const [nameCheckMessage, setNameCheckMessage] = useState('')
  
  // Pre-trial validation state
  const [showValidationModal, setShowValidationModal] = useState(false)
  
  // Upgrade modal state
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  
  // Plan limits
  const { currentPlan, limits, isLoadingPlan } = usePlan()
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
      exchange_type: 'BYBIT',
      trading_pairs: ['BTC/USDT'],
      timeframe: '1h',
      timeframes: ['1h'],
      version: '1.0.0',
      price_per_month: 0,
      is_free: false,
      image_url: '',
      leverage: 5,
      risk_percentage: 2,
      stop_loss_percentage: 2,
      take_profit_percentage: 5,
      llm_provider: 'openai',
      llm_model: 'gpt-4',
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

  // Fetch bot logs - MUST be before any conditional returns (hooks rules)
  const fetchBotLogs = useCallback(async () => {
    if (!createdBotId) return
    
    setIsLoadingLogs(true)
    try {
      const response = await fetch(`${config.studioBaseUrl}/api/futures-bot/logs/${createdBotId}`)
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
  }, [createdBotId])

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

  // Check bot name availability
  const checkNameAvailability = async (name: string) => {
    if (!name || name.length < 3) {
      setNameCheckStatus('idle')
      setNameCheckMessage('')
      return
    }
    
    setNameCheckStatus('checking')
    setNameCheckMessage('Checking availability...')
    
    try {
      const response = await fetch(`http://localhost:8000/bots/check-name/${encodeURIComponent(name)}`)
      const result = await response.json()
      
      if (result.available) {
        setNameCheckStatus('available')
        setNameCheckMessage('✅ Name is available')
      } else {
        setNameCheckStatus('taken')
        setNameCheckMessage('❌ Name is already taken')
      }
    } catch (error) {
      console.error('Error checking name availability:', error)
      setNameCheckStatus('idle')
      setNameCheckMessage('Failed to check availability')
    }
  }

  const handleTemplateSelect = (template: typeof botTemplates[0]) => {
    setSelectedTemplate(template.id)
    setValue('template', template.id as any)
    setValue('bot_type', template.type as any)
    
    // For multi-exchange templates, default to BINANCE (user can change later)
    const defaultExchange = template.exchange === 'MULTI' ? 'BINANCE' : template.exchange
    setValue('exchange_type', defaultExchange as any)
    
    setValue('name', template.name)
    setValue('description', template.description)
    
    // Check name availability for template name
    checkNameAvailability(template.name)
    
    console.log('🎯 Template selected:', template.name, 'Exchange:', defaultExchange)
    setStep(2)
  }

  const onSubmit = async (data: BotFormData) => {
    if (step === 3) {
      // Check if name is available before creating bot
      if (nameCheckStatus === 'taken') {
        toast.error('❌ Bot name is already taken. Please choose a different name.')
        return
      }
      
      if (nameCheckStatus === 'checking') {
        toast.error('⏳ Please wait for name availability check to complete.')
        return
      }
      
      // Check plan limits before creating bot (only if plan package is enabled)
      if (isPlanPackageEnabled && limits && !limits.usage.can_create_bot) {
        toast.error('🚫 Entity creation limit reached!')
        setShowUpgradeModal(true)
        return
      }
      
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

  // Handle start free trial - show validation modal first
  const handleStartFreeTrial = async () => {
    if (isStartingTrial || !createdBotId) return
    
    // Show validation modal first
    setShowValidationModal(true)
  }

  // Actual trial start after validation passes
  const startTrialAfterValidation = async () => {
    if (isStartingTrial || !createdBotId) return
    
    setIsStartingTrial(true)
    setShowValidationModal(false)
    
    try {
      // ✅ Check for trading pair conflicts with existing active subscriptions
      const token = localStorage.getItem('access_token')
      if (token && user?.id) {
        try {
          // Fetch all subscriptions for this bot by this developer
          const checkResponse = await fetch(`${config.studioBaseUrl}/subscriptions?bot_id=${createdBotId}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })

          if (checkResponse.ok) {
            const allSubscriptions = await checkResponse.json()
            
            // Filter: only active subscriptions that haven't expired yet
            const now = new Date()
            const activeSubscriptions = allSubscriptions.filter((sub: any) => {
              // Check both expires_at and marketplace_subscription_end
              const endDate = sub.expires_at || sub.marketplace_subscription_end
              if (!endDate) return false
              const expireDate = new Date(endDate)
              return sub.status === 'ACTIVE' && expireDate > now
            })
            
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
      
      const currentUserId = user?.id || 1
      
      const subscriptionData = {
        user_principal_id: `trial_user_${Date.now()}`,
        user_id: currentUserId,
        bot_id: createdBotId,
        subscription_start: startDate.toISOString(),
        subscription_end: endDate.toISOString(),
        is_testnet: trialConfig.networkType === 'TESTNET',
        trading_pair: trialConfig.tradingPair,
        secondary_trading_pairs: trialConfig.secondaryTradingPairs,
        trading_network: trialConfig.networkType,
        payment_method: 'TRIAL'
      }
      
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
        
        // Start fetching logs
        fetchBotLogs()
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
                    <div className="relative">
                      <input
                        {...register('name')}
                        value={watch('name') || ''}
                        onChange={(e) => {
                          const newName = e.target.value
                          setValue('name', newName)
                          
                          // Debounced name checking
                          setTimeout(() => {
                            if (watch('name') === newName) {
                              checkNameAvailability(newName)
                            }
                          }, 500)
                        }}
                        className={`form-input pr-10 ${
                          nameCheckStatus === 'available' ? 'border-green-500' : 
                          nameCheckStatus === 'taken' ? 'border-red-500' : ''
                        }`}
                        placeholder="Enter neural entity name..."
                      />
                      {nameCheckStatus === 'checking' && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                        </div>
                      )}
                      {nameCheckStatus === 'available' && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-green-500">
                          ✅
                        </div>
                      )}
                      {nameCheckStatus === 'taken' && (
                        <div className="absolute right-3 top-1/2 transform -translate-y-1/2 text-red-500">
                          ❌
                        </div>
                      )}
                    </div>
                    {errors.name && <p className="form-error">{errors.name.message}</p>}
                    {nameCheckMessage && (
                      <p className={`text-sm mt-1 ${
                        nameCheckStatus === 'available' ? 'text-green-500' : 
                        nameCheckStatus === 'taken' ? 'text-red-500' : 'text-gray-500'
                      }`}>
                        {nameCheckMessage}
                      </p>
                    )}
                  </div>
                  
                  <div>
                    <label className="form-label">Description</label>
                    <textarea
                      {...register('description')}
                      value={watch('description') || ''}
                      onChange={(e) => setValue('description', e.target.value)}
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
                      <select 
                        {...register('exchange_type')} 
                        className="form-input"
                        defaultValue="BYBIT"
                      >
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
                        📊 Select from top coins. Users will choose from your selection when subscribing.
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
                      <select 
                        {...register('timeframe')} 
                        className="form-input"
                        defaultValue="1h"
                        onChange={(e) => {
                          const newPrimary = e.target.value
                          setValue('timeframe', newPrimary)
                          
                          // Auto-remove new primary from extra timeframes if it exists
                          const currentExtras = watch('timeframes') || []
                          const cleanedExtras = currentExtras.filter(tf => tf !== newPrimary)
                          if (cleanedExtras.length !== currentExtras.length) {
                            setValue('timeframes', cleanedExtras)
                          }
                        }}
                      >
                        {timeframeOptions.map((tf) => (
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

                {/* Pricing Configuration - Feature Flag Controlled */}
                {canPublishToMarketplace && (
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
                )}
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
                      {/* Free Plan Warning */}
                      {!isPro && (
                        <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-4">
                          <div className="flex items-start space-x-3">
                            <div className="flex-shrink-0">
                              <svg className="h-5 w-5 text-orange-400" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                              </svg>
                            </div>
                            <div className="flex-1">
                              <h4 className="text-sm font-semibold text-orange-400 mb-1">Free Plan - Limited AI Performance</h4>
                              <p className="text-xs text-orange-300/80 leading-relaxed">
                                Your entity will use <strong>Gemini 2.0 Flash (Free)</strong> - a basic AI model with slower response times and lower analysis accuracy. 
                                To unlock faster speeds, advanced models (GPT-4o, Claude 3.7 Sonnet), and higher accuracy, 
                                <button 
                                  type="button"
                                  onClick={() => setShowUpgradeModal(true)}
                                  className="underline hover:text-orange-200 font-semibold"
                                >
                                  upgrade to Pro Plan
                                </button>.
                              </p>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* LLM Provider Selection - Only for Pro Plan */}
                      {isPro && (
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

                      {/* Free Plan - Show auto-selected provider */}
                      {!isPro && (
                        <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
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

        {/* Step 4: Attach Strategies & Backtest */}
        {step === 4 && (
          <div className="space-y-8">
            {/* Attach Strategies Section - FIRST */}
            {createdBotId && (
              <div className="bg-gradient-to-r from-purple-900/30 to-indigo-900/30 p-6 rounded-lg border border-purple-700/50">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-2xl font-bold text-white flex items-center">
                    🎯 Attach Strategy
                    <span className="ml-2 px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full">REQUIRED</span>
                  </h4>
                </div>
                <p className="text-sm text-gray-300 mb-4">
                  Enhance your bot's decision-making by attaching custom strategy templates. 
                  Strategies guide your bot's AI analysis and trading strategies.
                </p>
                
                {/* Embedded BotPromptsTab Component */}
                <div className="bg-gray-900/50 rounded-lg border border-purple-700/30">
                  <BotPromptsTab botId={createdBotId} />
                </div>
              </div>
            )}

            {/* Backtest Your Bot Section - SECOND */}
            <div className="card-quantum p-8">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-bold cyber-text mb-2">🧪 Backtest Your Bot</h2>
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
                      Primary Trading Pair
                    </label>
                        <select
                      value={trialConfig.tradingPair}
                      onChange={(e) => setTrialConfig(prev => ({ ...prev, tradingPair: e.target.value }))}
                      className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    >
                      {watch('trading_pairs') && watch('trading_pairs').length > 0 ? (
                        watch('trading_pairs').map((pair: string) => (
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
                <div className="mt-4">
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
                      {watch('trading_pairs') && watch('trading_pairs').length > 0 ? (
                        watch('trading_pairs')
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
                    <p className="text-yellow-400 font-medium mb-2">⚠️ Bot requires a strategy to analyze market and make decisions!</p>
                    <div className="space-y-1.5">
                      <div className="flex items-start">
                        <span className="mr-2">1️⃣</span>
                        <span>After creating your bot, go to the bot details page</span>
                      </div>
                      <div className="flex items-start">
                        <span className="mr-2">2️⃣</span>
                        <span>Click on <strong className="text-indigo-400">"Strategy Management"</strong> tab</span>
                      </div>
                      <div className="flex items-start">
                        <span className="mr-2">3️⃣</span>
                        <span>Attach at least one strategy to configure trading strategy</span>
                      </div>
                    </div>
                    <div className="mt-3 p-2 bg-indigo-900/30 border border-indigo-500/20 rounded text-xs flex items-start">
                      <span className="mr-2">💡</span>
                      <span>The strategy guides your bot's trading strategy and decision-making process. Without a strategy, the bot cannot operate.</span>
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

              <div className="flex flex-col sm:flex-row gap-4 items-center justify-between mb-6">
                <div className="flex items-center space-x-4">
                      <button 
                    onClick={handleStartFreeTrial}
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
              <div className="bg-gray-800/50 p-6 rounded-lg border border-gray-700 mb-6">
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
                      onClick={() => setBotLogs([])}
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
                              case 'error': return 'text-red-400'
                              default: return 'text-gray-300'
                            }
                          }
                          
                          return (
                            <div key={index} className={`${getLogColor(log.type)} py-1 border-b border-gray-800`}>
                              <span className="text-gray-500">[{timestamp}]</span> {log.message}
                            </div>
                          )
                        })
                      ) : (
                        <div className="text-center text-gray-500 mt-8">
                          <p>No logs available yet</p>
                          <p className="text-sm mt-2">Start a trial to see bot execution logs</p>
                        </div>
                      )}
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

        {/* Step 5: Publish to Marketplace - Feature Flag Controlled */}
        {step === 5 && canPublishToMarketplace && (
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

      {/* Pre-Trial Validation Modal */}
      {createdBotId && (
        <PreTrialValidationModal
          isOpen={showValidationModal}
          onClose={() => setShowValidationModal(false)}
          onProceed={startTrialAfterValidation}
          bot={{
            id: createdBotId,
            name: watch('name') || 'Your Bot',
            exchange_type: watch('exchange_type'),
            bot_type: watch('bot_type')
          } as any}
          networkType={trialConfig.networkType as 'TESTNET' | 'MAINNET'}
        />
      )}

      {/* Floating Neural Particles */}
      <div className="fixed top-20 left-20 w-1 h-1 bg-quantum-500 rounded-full animate-neural-pulse opacity-60"></div>
      <div className="fixed top-40 right-32 w-1.5 h-1.5 bg-cyber-400 rounded-full animate-neural-pulse opacity-40" style={{ animationDelay: '1s' }}></div>
      <div className="fixed bottom-40 left-32 w-2 h-2 bg-neural-500 rounded-full animate-neural-pulse opacity-50" style={{ animationDelay: '2s' }}></div>
      <div className="fixed bottom-20 right-20 w-1 h-1 bg-quantum-400 rounded-full animate-neural-pulse opacity-30" style={{ animationDelay: '3s' }}></div>

      {/* Upgrade Modal */}
      <UpgradeModal
        isOpen={showUpgradeModal}
        onClose={() => setShowUpgradeModal(false)}
      />
    </div>
  )
}
